# import numpy as np
import cv2
import keras.backend
# import tensorflow as tf
# import keras.backend as K
from module.get_tile import *
from PIL import Image
from keras.backend.tensorflow_backend import _to_tensor
from .metrics import *
from shapely.geometry import Polygon, MultiPolygon
from simplification.util import simplify_coords, simplify_coords_vw
graph = tf.get_default_graph()


def normalize_127_1(image_arr):
    image_arr = np.array(image_arr)
    return image_arr / 127.5 - 1


def normalize_mean_std(image_arr):
    image_arr = np.array(image_arr)
    return (image_arr - np.mean(image_arr)) / np.std(image_arr)


def normalize_div255(image_arr):
    return np.array(image_arr, dtype=float) / 255.0


def normalize_mean(image_arr):
    image_arr = np.array(image_arr, dtype=float) / 255.0
    return image_arr - np.mean(image_arr, axis=(0, 1))


def normalization_hist(src):
    # Усиление границ изображения
    img_np = np.asarray(src)

    kernel3 = np.array([[-0.1, -0.1, -0.1], [-0.1, 2, -0.1], [-0.1, -0.1, -0.1]])

    src = cv2.filter2D(img_np, -1, kernel=kernel3)

    resR = src[:, :, 2]
    resG = src[:, :, 1]
    resB = src[:, :, 0]

    resR_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')
    resG_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')
    resB_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')

    # расстягиевание каждого слоя
    cv2.equalizeHist(resR, resR_dst)
    cv2.equalizeHist(resG, resG_dst)
    cv2.equalizeHist(resB, resB_dst)

    resR_dst = np.mean(np.array([resR, resR_dst]), axis=0)
    resG_dst = np.mean(np.array([resG, resG_dst]), axis=0)
    resB_dst = np.mean(np.array([resB, resB_dst]), axis=0)

    resR_dst = np.array(resR_dst).astype('uint8')
    resG_dst = np.array(resG_dst).astype('uint8')
    resB_dst = np.array(resB_dst).astype('uint8')

    # BRG
    out_img = np.dstack((resB_dst, resG_dst, resR_dst))
    # cv2.imshow('namewef', out_img)
    return Image.fromarray(out_img, 'RGB')


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def project(lat, lng):
    TILE_SIZE = 256
    siny = math.sin(lat * math.pi / 180)
    siny = min(max(siny, -0.9999), 0.9999)
    x = (TILE_SIZE * (0.5 + lng / 360))
    y = (TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)))
    return x, y


def getPixelCoordinates(lat, lng, zoom):
    scale = 1 << zoom
    x, y = project(lat, lng)
    pixelCoordinate = (math.floor(x * scale), math.floor(y * scale))
    return pixelCoordinate



def denoise_image(mask_arr):
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.fastNlMeansDenoising(mask_arr.astype(np.uint8), None, 5, 21, 7)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # mask = cv2.dilate(mask, kernel, iterations=1)
    return mask


def denoise_fill_image(image):
    """ Fill small holes in image """
    kernel = np.ones((3, 3), dtype=np.uint8)
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
    image = cv2.dilate(image, kernel)
    # image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    return image


def create_image_from_coordinates(coords, zoom=18, tile_size=256):
    # перевод коор-т в пиксели на глобальной карте
    coords = list(map(lambda lat_lng: getPixelCoordinates(lat_lng[0], lat_lng[1], zoom), coords))
    coords = np.array(coords).reshape((-1, 2))
    # Находим мин макс значения пикселей переведенных из координат
    coords_min_x = np.min(coords[:, 0])
    coords_max_x = np.max(coords[:, 0])

    coords_min_y = np.min(coords[:, 1])
    coords_max_y = np.max(coords[:, 1])
    # находим размер результиррующего изображения
    x_shape = (coords_max_x // 256 - coords_min_x // 256) * tile_size
    y_shape = (coords_max_y // 256 - coords_min_y // 256) * tile_size
    # центрируем - добавляем 256 пикс к X, Y т.к. картинка с маской имеет такой отступ
    x_shape, y_shape = x_shape + (tile_size * 3), y_shape + (tile_size * 3)

    pix_x = coords[:, 0] - (coords_min_x - coords_min_x % 256) + 256
    pix_y = coords[:, 1] - (coords_min_y - coords_min_y % 256) + 256
    # пустая маска
    user_mask = np.zeros((y_shape, x_shape), dtype=np.uint8)

    cnt = np.dstack([pix_x, pix_y])[0]
    # упрощаем массив в раст. 3 пикс.
    cnt = np.array(simplify_coords_vw(cnt.astype(float), 3.0), dtype=int)[1:-1]
    cv2.fillPoly(user_mask, [cnt], 255)
    # cv2.imwrite("user_area.png", user_mask)
    return user_mask


def find_contours(predicted_mask, start_lat, start_lng,
                  lat_per_pixel, lng_per_pixel, user_area_image, sub_classes=None, simplify_value=1):
    predicted_mask = np.array(predicted_mask).T

    layers_count = sub_classes['count']
    if np.ndim(predicted_mask) == 3:
        # возврат значения азмеров после транспон.
        intersection_user_mask = {}
        for layer_index in range(layers_count):
            predicted_layer = np.array(predicted_mask[layer_index, :, :], dtype=bool)
            bool_intersect = np.all([predicted_layer, user_area_image.astype(bool)], axis=0)
            intersection_user_mask.update({str(layer_index): np.array(bool_intersect, dtype=np.uint8) * 255})
    else:
        intersection_user_mask = np.all([predicted_mask.astype(bool), user_area_image.astype(bool)], axis=0)

    # simplify_value = 4
    result_contours = {}
    # для каждого слоя маски находим контуры
    for layer_index in range(layers_count):
        if sub_classes['count'] == 1:
            layer_intersection = denoise_image(intersection_user_mask)
        else:
            layer_intersection = denoise_image(intersection_user_mask[str(layer_index)])

        contours, hier = cv2.findContours(layer_intersection, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)
        layer_cnt = []

        # Перевод контуров в географич. координаты
        for cnt in contours:
            try:
                if cnt.shape[0] > 0:
                    cnt = np.array(np.reshape(cnt, (-1, 2)), dtype=float)
                    # упрощаем контур в значениях для пикселей
                    cnt = np.array(simplify_coords_vw(cnt, simplify_value), dtype=float)[1:-1]
                    cnt[:, 0] *= -lat_per_pixel
                    cnt[:, 0] += start_lat

                    cnt[:, 1] *= lng_per_pixel
                    cnt[:, 1] += start_lng

                    # cnt = np.unique(cnt, axis=0)
                    np.resize(cnt, (cnt.shape[0] + 1, cnt.shape[1]))
                    cnt[-1] = cnt[0]
                    layer_cnt.append(cnt.tolist())
            except Exception as e:
                print("find_contours func", e)

        result_contours.update({sub_classes['names_ru'][layer_index]: layer_cnt})
    return result_contours


def predict_class(image, class_property, model, class_name):
    crop_size = class_property["input_size"]    # размер исходного изображения
    output_size = class_property["output_size"] # размер изображения для нейронки
    delta = class_property["delta"]             # порог для поиска объекта
    sub_classes_count = class_property['sub_classes']['count']

    height = image.shape[0]
    width = image.shape[1]
    # пустая маска
    if sub_classes_count == 1:
        mask = np.zeros((height, width), dtype=np.float32)
    else:
        mask = np.zeros((height, width, sub_classes_count), dtype=np.float32)
    # нормализация входных данных для модели
    if class_property["normalize_hist"] and class_name != "water":
        image = normalization_hist(image)
    image = class_property["normalization"](image)

    half_step = crop_size // 2  # определяем шаг движения окна для модели
    # скольжение окна
    for i in range(height // half_step - 1):
        for j in range(width // half_step - 1):
            # получаем изображение
            cropped_image = image[i*half_step:i*half_step+crop_size, j*half_step:j*half_step+crop_size]
            # изменяем его размер для модели
            cropped_image = cv2.resize(cropped_image, (output_size, output_size))
            cropped_image = cropped_image[np.newaxis, :, :, :]
            # предсказываем
            pred = model.predict(cropped_image)
            # возвращаем в исходный вид массива
            if sub_classes_count == 1:
                pred = pred.reshape((output_size, output_size))
                # возвращаем исходный размер картинки
                pred = cv2.resize(pred, (crop_size, crop_size))
                # Добавляем к результирующей маске
                mask[i * half_step:i * half_step + crop_size, j * half_step:j * half_step + crop_size] += pred
            else:
                pred = pred.reshape((output_size, output_size, sub_classes_count))
                # pred_resized = np.array((crop_size, crop_size, classes_count))
                # изменяем размер каждого слоя в исходный
                for class_index in range(sub_classes_count):
                    resized_layer = cv2.resize(pred[:, :, class_index], (crop_size, crop_size))
                    mask[i * half_step:i * half_step + crop_size,
                         j * half_step:j * half_step + crop_size, class_index] += resized_layer

    # находим среднее значение для маски
    res_mask = mask / 4
    # определяем объекты, которые выше порогового значения
    res_mask[res_mask > delta] = 255
    res_mask[res_mask <= delta] = 0
    # возвращаем результат в виде изображения
    res_mask = np.array(res_mask, dtype=np.uint8)
    return res_mask


def classify(image, class_list, user_path, lat_lng, class_property, models):
    global graph
    zoom = 18
    user_poly = Polygon(list(map(tuple, user_path)))
    center_main_path = list(user_poly.centroid.coords[0])
    # Общий реультат для конутров и результатов
    glob_result = {"center": center_main_path}

    # перевод пользовательского контура в изображение - маску
    user_area_image = create_image_from_coordinates(user_path)
    user_area_image = user_area_image.T

    tile_index_x = lat_lng[0]
    tile_index_y = lat_lng[1]
    # ИЗ ID ПЕРЕВОДИМ В КООРДИНАТЫ И ПОЛУЧАЕМ (0, 0)
    first_lat, first_lng = num2deg(tile_index_x, tile_index_y, zoom)
    # находим разницу для широты
    sec_lat, _ = num2deg(tile_index_x, tile_index_y + 1, zoom)
    lat_per_pixel = math.fabs(sec_lat - first_lat) / 256
    # находим разницу для долготы
    _, sec_lng = num2deg(tile_index_x + 1, tile_index_y, zoom)
    lng_per_pixel = math.fabs(sec_lng - first_lng) / 256

    with graph.as_default():
        # для каждого класса в списке выбранном пользователем
        for class_name in class_list:
            try:
                ##### !!!!!!!!!!!!!!!!! ##########
                if class_name == "water":
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # находим объекты на изображении
                class_mask = predict_class(image=image, class_property=class_property[class_name],
                                           model=models[class_name], class_name=class_name)
                # устраняем шум и пропуски на изображении
                if class_property[class_name]['sub_classes']['count'] == 1:
                    class_mask = denoise_fill_image(class_mask)
                    # cv2.imwrite(f"{class_name}_pred.png", class_mask)
                else:
                    for class_index in range(class_property[class_name]['sub_classes']['count']):
                        class_mask[:, :, class_index] = denoise_fill_image(class_mask[:, :, class_index])
                        # cv2.imwrite(f"{class_name}_{str(class_index)}_pred.png", class_mask[:, :, class_index])

                # находим географические координаты контуров для маски
                coords_of_contours = find_contours(class_mask, first_lat, first_lng,
                                                   lat_per_pixel, lng_per_pixel, user_area_image,
                                                   class_property[class_name]['sub_classes'],
                                                   class_property[class_name]['simplify_val'])
                # Добавляем в результат
                glob_result.update({class_name: coords_of_contours})
            except Exception as e:
                print(f"Can't find contours in class: {class_name}. ", e)
        return glob_result

