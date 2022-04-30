from itertools import product, cycle
from threading import Thread
from random import randint
from queue import Queue
# from time import sleep
from io import BytesIO
from PIL import Image
import requests as rq
# import math
import math
import numpy as np
import cv2
import time

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

def get_one_tile(x_index, y_index, zoom):
    url = f'http://mt{randint(1, 3)}.google.com/vt/lyrs=s&x={x_index}&y={y_index}&z={zoom}'
    img = None
    try:
        data = rq.get(url)
        if data.status_code == 200:
            img = np.asarray(Image.open(BytesIO(data.content)), dtype=np.uint8)
    finally:
       return img

def get_tile(input, output):
    server_id = randint(1, 3)
    while not input.empty():
        index, ((yp, xp), zp) = input.get_nowait()
        img = None
        while img is None:
            url = f'http://mt{server_id}.google.com/vt/lyrs=s&x={xp}&y={yp}&z={zp}'
            try:
                data = rq.get(url)
                if data.status_code == 200:
                    img = Image.open(BytesIO(data.content))
            except Exception as e:
                print("Cant get Google Image")
                time.sleep(2)
        output.put_nowait((index, img))
        input.task_done()


def get_map(min_x, max_x, min_y, max_y, zoom, neighbourhood=None, name=None, dir=None,  threads=1):
    size = 256
    # входные данные
    coords = product(range(min_y, max_y), range(min_x, max_x))
    zooms = cycle([zoom])

    # входная и выходная очередь
    queue = Queue()
    result_queue = Queue()

    # добавляем данные в очередь
    for data in enumerate(zip(coords, zooms)):
        queue.put(data)

    # создаём потоки для обработки
    for i in range(threads):
        thread = Thread(target=get_tile, args=(queue, result_queue))
        thread.daemon = True
        thread.start()

    # ждём пока не обработаюся все данные
    queue.join()

    image = None

    # формируем картинку из полученных данных
    while not result_queue.empty():
        index, img = result_queue.get_nowait()
        if img is not None:
            if image is None:
                height = (max_y - min_y) * size
                width = (max_x - min_x) * size
                image = np.zeros((height, width, 3), dtype=np.uint8)
            nx, ny = index % width, index // height
            image[img.size[0] * ny: img.size[0] * ny + size,
                  img.size[0] * nx: img.size[0] * nx + size] = np.asarray(img, dtype=np.uint8)

    # cv2.imwrite("test.png", image)
    # отправляем изображение и верх. лев. индекс тайла
    return image


def get_my_map(combin, zoom):
    # входные данные
    size = 256
    combin = np.array(combin).reshape((-1, 2))
    # размер картинки с запасом 128 пикс.
    width = (np.max(combin[:, 0]) - np.min(combin[:, 0]) + 1) * size
    height = (np.max(combin[:, 1]) - np.min(combin[:, 1]) + 1) * size
    # пустая картинка
    image = np.zeros((height, width, 3), dtype=np.uint8)
    max_index_x = width // size
    # счетчик по Y
    index_y = 0
    # Получить каждый тайл в комбинации
    for index, x_y in enumerate(combin):
        image_small = get_one_tile(x_y[0], x_y[1], zoom)
        sleep_timer = 3
        while image_small is None:
            # print("image none")
            time.sleep(sleep_timer)
            sleep_timer += 1
            image_small = get_one_tile(x_y[0], x_y[1], zoom)
        try:
            image[index_y*size:index_y*size+size, index % max_index_x*size:index % max_index_x*size+size] = image_small
        except Exception as e:
            print(e)
        if (index + 1) % max_index_x == 0 and index > 0:
            index_y += 1

    # cv2.imwrite("test.png", cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    return image
