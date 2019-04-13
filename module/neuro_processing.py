import numpy as np
import cv2
import keras.backend
import tensorflow as tf
import keras.backend as K
from module.get_tile import *
from PIL import Image
from keras.backend.tensorflow_backend import _to_tensor
# from pysal.lib.cg import get_polygon_point_intersect, Point, Polygon, get_shared_segments
# from arcgis.geometry import Polygon, Point, Geometry
# from sympy.geometry import Polygon, Point, intersection
from shapely.geometry import Polygon, MultiPolygon
graph = tf.get_default_graph()


def normalize_mean_std(image_arr):
    image_arr = np.array(image_arr)
    return (image_arr - np.mean(image_arr)) / np.std(image_arr)


def normalize_div255(image_arr):
    return np.array(image_arr, dtype=float) / 255.0


def normalize_mean(image_arr):
    image_arr = np.array(image_arr, dtype=float) / 255.0
    return image_arr - np.mean(image_arr, axis=(0, 1))


def normalization(img):
    for i in range(3):
        min = img[:, i].min()
        max = img[:, i].max()
        if min != max:
            img[:, i] -= min
            img[:, i] *= (255./(max-min))
    return img


def normalization_image(src):
    # Усиление границ изображения
    img_np = np.asarray(src)

    # nparr = np.fromstring(src, np.uint8)
    # nparr = nparr.reshape((255, 255))
    # img_np = cv2.imdecode(nparr, cv2.COLOR_RGB2BGR)

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



def dice_coef(y_true, y_pred, smooth=1.0):
    y_true_f = K.batch_flatten(y_true)
    y_pred_f = K.batch_flatten(y_pred)
    intersection = 2. * K.sum(y_true_f * y_pred_f, axis=1, keepdims=True) + smooth
    union = K.sum(y_true_f, axis=1, keepdims=True) + K.sum(y_pred_f, axis=1, keepdims=True) + smooth
    return K.mean(intersection / union)


def dice_coef_loss(y_true, y_pred):
    return 1 - dice_coef(y_true, y_pred)


def bootstrapped_crossentropy(y_true, y_pred, bootstrap_type='hard', alpha=0.95):
    target_tensor = y_true
    prediction_tensor = y_pred
    _epsilon = _to_tensor(K.epsilon(), prediction_tensor.dtype.base_dtype)
    prediction_tensor = K.tf.clip_by_value(prediction_tensor, _epsilon, 1 - _epsilon)
    prediction_tensor = K.tf.log(prediction_tensor / (1 - prediction_tensor))
    if bootstrap_type == 'soft':
        bootstrap_target_tensor = alpha * target_tensor + (1.0 - alpha) * K.tf.sigmoid(prediction_tensor)
    else:
        bootstrap_target_tensor = alpha * target_tensor + (1.0 - alpha) * K.tf.cast(
            K.tf.sigmoid(prediction_tensor) > 0.5, K.tf.float32)
    return K.mean(K.tf.nn.sigmoid_cross_entropy_with_logits(labels=bootstrap_target_tensor, logits=prediction_tensor))


def dice_coef_loss_bce(y_true, y_pred, dice=0.5, bce=0.5, bootstrapping='hard', alpha=1.):
    return bootstrapped_crossentropy(y_true, y_pred, bootstrapping, alpha) * bce + dice_coef_loss(y_true, y_pred) * dice


def denoise_image(mask_arr):
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.fastNlMeansDenoising(mask_arr.astype(np.uint8), None, 5, 21, 7)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)
    return mask


def denoise_fill_image(image):
    """ Fill small holes in image """
    kernel = np.ones((3, 3), dtype=np.uint8)
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
    image = cv2.dilate(image, kernel)
    # image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    return image


def find_contours(mask_arr, start_lat, start_lng, lat_per_pixel, lng_per_pixel, main_path):
    img_t = np.transpose(mask_arr).copy()
    _, contours, hier = cv2.findContours(img_t, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)
    coords_cnt = []
    main_path = main_path.simplify(lat_per_pixel)
    for cnt, h in zip(contours, hier[0]):
        try:
            cnt = np.array(np.reshape(cnt, (-1, 2)), dtype=float)
            cnt[:, 0] *= -lat_per_pixel
            cnt[:, 0] += start_lat

            cnt[:, 1] *= lng_per_pixel
            cnt[:, 1] += start_lng

            # cnt = np.unique(cnt, axis=0)
            np.resize(cnt, (cnt.shape[0] + 1, cnt.shape[1]))
            cnt[-1] = cnt[0]
            # coords_cnt.append(cnt.tolist())
            if cnt.shape[0] > 2:
                if h[-1] != -1:
                    cnt = np.flip(cnt, 0)
                cnt_poly = Polygon(list(map(tuple, cnt.tolist())))

                cnt_poly = cnt_poly.buffer(0)
                if not cnt_poly.is_valid:
                    print("not valid, ", cnt_poly.type)
                    # cnt_poly = cnt_poly.simplify(lat_per_pixel)

                if cnt_poly.geom_type == 'Polygon' and cnt_poly.is_valid:
                    if not main_path.disjoint(cnt_poly):
                        intersection_cnt = find_intersection(main_path, cnt_poly)
                        if len(intersection_cnt) > 2:
                            coords_cnt.append(intersection_cnt)

                elif cnt_poly.type == 'MultiPolygon' and cnt_poly.is_valid:
                    for sub_poly in cnt_poly:
                        if not main_path.disjoint(sub_poly):
                            intersection_cnt = find_intersection(main_path, sub_poly)
                            if len(intersection_cnt) > 2:
                                    coords_cnt.append(intersection_cnt)
                else:
                    print("No intersection, type is ", cnt_poly.type)

            # !!!!!!!Возможна ошибка - fabs
        except Exception as e:
            print("find_contours func", e)
    # coords_cnt = np.array(coords_cnt).reshape((-1, 2))
    return coords_cnt


def find_intersection(main_path, poly_path):
    try:
        intersect = main_path.intersection(poly_path)

        if not intersect.is_empty and hasattr(intersect, 'exterior'):
            intersect = np.array(intersect.exterior.coords[:])
            if intersect.shape[0] > 2:
                intersect = intersect.reshape((-1, 2))
                return np.array(intersect).tolist()

        return []
    except Exception as e:
        print("Find_intersection function error", e)
        return []


def predict_class(image, class_property, model, class_name):
    crop_size = class_property["input_size"]
    output_size = class_property["output_size"]
    delta = class_property["delta"]
    height = image.shape[0]
    width = image.shape[1]
    mask = np.zeros((height, width), dtype=np.uint8)

    image = class_property["normalization"](image)
    for i in range(height // crop_size):
        for j in range(width // crop_size):
            cropped_image = image[i*crop_size:i*crop_size+crop_size, j*crop_size:j*crop_size+crop_size]
            cropped_image = cv2.resize(cropped_image, (output_size, output_size))
            cropped_image = cropped_image[np.newaxis, :, :, :]
            pred = model.predict(cropped_image)
            pred[pred > delta] = 255
            pred[pred <= delta] = 0
            pred = np.array(pred, dtype=np.uint8).reshape((output_size, output_size))
            pred = cv2.resize(pred, (crop_size, crop_size))
            mask[i*crop_size:i*crop_size+crop_size, j*crop_size:j*crop_size+crop_size] = pred

    return mask


def classify(image, class_list, path, lat_lng, class_prop_to_model, models):
    global graph
    zoom = 18
    main_path = Polygon(list(map(tuple, path)))
    center_main_path = list(main_path.centroid.coords[0])
    # Общий реультат для конутров и результатов
    glob_result = {"center": center_main_path}

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
        for class_name in class_list:
            # results_for_class = {}
            try:
                class_mask = predict_class(image=image, class_property=class_prop_to_model[class_name],
                                           model=models[class_name], class_name=class_name)

                class_mask = denoise_fill_image(class_mask)
                cv2.imwrite(f"{class_name}_pred.png", class_mask)

                coords_of_contours = find_contours(class_mask, first_lat, first_lng, lat_per_pixel, lng_per_pixel, main_path)
                glob_result.update({class_name: coords_of_contours})
                # results_for_class.update({f'{tile_index_X}_{tile_index_Y}': coords_of_contours})
            except Exception as e:
                print(f"Can't find contours in class: {class_name}. ", e)
        return glob_result

