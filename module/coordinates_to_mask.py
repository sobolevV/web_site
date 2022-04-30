import cv2
import numpy as np
import ast
import math
from simplification.util import simplify_coords, simplify_coords_vw

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def deg2num(lat, lng, zoom):
    n = 2 ** zoom
    xtile = n * ((lng + 180) / 360)
    ytile = n * (1 - (math.log(math.tan(lat) + (1 - math.sin(lat)) ) / math.pi)) / 2
    return xtile, ytile


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
    return math.floor(x * scale), math.floor(y * scale)

# coords = coords.replace("VM74:2", "")
# coords = coords.replace("\n", " ")
# coords = np.fromstring(coords, dtype=float, sep=" ").reshape((-1, 2))
# # вход - coords
# zoom = 18
# tile_size = 256
# # перевод коор-т в пиксели на глобальной карте
# coords = list(map(lambda lat_lng: getPixelCoordinates(lat_lng[0], lat_lng[1], zoom), coords))
# coords = np.array(coords).reshape((-1, 2))
#
# # Находим мин макс значения пикселей переведенных из координат
# coords_min_x = np.min(coords[:, 0])
# coords_max_x = np.max(coords[:, 0])
#
# coords_min_y = np.min(coords[:, 1])
# coords_max_y = np.max(coords[:, 1])
# # находим размер результиррующего изображения
# x_shape = (coords_max_x // 256 - coords_min_x // 256) * tile_size
# y_shape = (coords_max_y // 256 - coords_min_y // 256) * tile_size
# # центрируем - добавляем 256 пикс к X, Y т.к. картинка с маской имеет такой отступ
# x_shape, y_shape = x_shape + (tile_size * 2), y_shape + (tile_size * 2)
#
# pix_x = coords[:, 0] - coords_min_x + tile_size
# pix_y = coords[:, 1] - coords_min_y + tile_size
#
# # пустая маска
# user_mask = np.zeros((y_shape, x_shape), dtype=np.uint8)
#
# cnt = np.dstack([pix_x, pix_y])[0]
# cnt = np.array(simplify_coords(cnt.astype(float), 3.0), dtype=int)[1:-1]
# cv2.fillPoly(user_mask, [cnt], 255)
# cv2.imshow("mask", user_mask)
# predicted_mask = cv2.imread("cars_pred.png", cv2.IMREAD_GRAYSCALE)
# predicted_mask = cv2.resize(predicted_mask, (x_shape, y_shape))
# if np.ndim(predicted_mask) == 3:
#     for layer_index in range(predicted_mask.shape[-1]):
#         layer = predicted_mask[:, :, layer_index]
#         and_op = np.all([layer.astype(bool), user_mask.astype(bool)], axis=0)
#         cv2.imshow("res", np.array(and_op, dtype=np.uint8)*255)
#         cv2.waitKey()
# else:
#     and_op = np.all([predicted_mask.astype(bool), user_mask.astype(bool)], axis=0)
#     cv2.imshow("res", np.array(and_op, dtype=np.uint8) * 255)
#     cv2.waitKey()

img = cv2.imread("buildings_pred.png", cv2.IMREAD_GRAYSCALE)
# img = cv2.resize(img, (450, 450))
contours, h = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

img_3d = np.dstack((img, img, img))
for sub_contour in contours:
    if sub_contour.shape[0] > 2:
        area = cv2.contourArea(sub_contour)
        coef = area // 500
        if coef <= 5:
            simplify_val = 5
            color = (255, 0, 0)
        elif coef > 5 and coef <= 20:
            simplify_val = 15
            color = (0, 255, 0)
        else:
            simplify_val = 30
            color = (0, 0, 255)
        sim_coords = np.array(simplify_coords(sub_contour.reshape((-1, 2)), simplify_val), dtype=int)[1: -1]
        if sim_coords.shape[0] >= 3:
            cv2.drawContours(img_3d, [sim_coords], 0, color, thickness=3)
cv2.imwrite('res.png', img_3d)
# cv2.waitKey()