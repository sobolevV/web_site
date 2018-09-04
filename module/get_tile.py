from itertools import product, cycle
from threading import Thread
from random import randint
from queue import Queue
from time import sleep
from io import BytesIO
from PIL import Image
import requests as rq
#import math
import math


def tile_index(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2 << (zoom - 1)
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def get_tile(input, output):
    server_id = randint(1, 3)
    while not input.empty():
        index, ((yp, xp), zp) = input.get_nowait()
        url = f'https://khms{server_id}.googleapis.com/kh?v=803&x={xp}&y={yp}&z={zp}'
        data = rq.get(url)
        if data.status_code == 200:
            img = Image.open(BytesIO(data.content))
        else:
            img = None
        output.put_nowait((index, img))
        input.task_done()


def get_map(filename, lat, lon, zoom, neighbourhood=7, threads=8):
    # получаем номер тайла по координатам
    x, y = tile_index(lat, lon, zoom)
    r_size = (neighbourhood * 2 + 1)

    # входные данные
    coords = product(range(y - neighbourhood, y + neighbourhood + 1),
                     range(x - neighbourhood, x + neighbourhood + 1))
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
                image = Image.new('RGB', (r_size * img.size[0], r_size * img.size[0]))
            nx, ny = index % r_size, index // r_size
            image.paste(img, (img.size[0] * nx, img.size[0] * ny))

    image.save(filename)
    return image



if __name__ == '__main__':
    output_file = 'image-all.jpg'
    lat, lon, zoom = 48.7078478, 44.513905199999954, 20
    result = get_map(output_file, lat, lon, zoom)
 