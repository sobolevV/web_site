import json
import numpy as np
import math

def tile_index(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2 << (zoom - 1)
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = math.pow(2.0, zoom)
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = 180.0 * (lat_rad / math.pi)
    return [lat_deg, lon_deg]


def line(x0, x1, y0, y1, diff):
    steep = False
    fulled = []
    if abs(x0-x1) < abs(y0 - y1):
        y0, x0 = x0, y0
        y1, x1 = x1, y1
        steep = True

    if x0 > x1:
        x1, x0 = x0, x1
        y1, y0 = y0, y1

    dx = x1 - x0
    dy = y1 - y0

    derror2 = abs(dy) * 2
    error2 = 0
    y = y0
    for x in range(x0, x1):
        if steep:
            # image.set(y, x, color)
            fulled.append([y, x])
        else:
            fulled.append([x, y])
            # image.set(x, y, color)
        error2 += derror2;

        if error2 > dx:
            y += diff if y1 > y0 else -diff
            error2 -= dx * 2
    return fulled


def get_indexes(path, zoom=18):
    coords = np.array(path, dtype=np.float32).reshape(-1, 2)
    print(coords)
    coords.sort(axis=0)

    # ##################################################
    # координаты в id тайлов
    indexes = []
    for latlng in coords:
        indexes.append(list(tile_index(latlng[0], latlng[1], zoom)))
        # f.write(str(index)+'\n')
    indexes = np.unique(indexes, axis=0)
    indexes = np.array(indexes).reshape((-1, 2))

    # внешний контур тайлов
    min_of_x, max_of_x = np.min(indexes[:, 0]) - 1, np.max(indexes[:, 0]) + 1
    min_of_y, max_of_y = np.min(indexes[:, 1]) - 1, np.max(indexes[:, 1]) + 1

    combin = []
    # combin.append([[] for tile_x in range(max_of_x - min_of_x)])
    for y_index_tile in range(min_of_y, max_of_y + 1):
        for x_index_tile in range(min_of_x, max_of_x + 1):
            if [x_index_tile, y_index_tile] not in combin:
                combin.append([x_index_tile, y_index_tile])

    #
    return combin


