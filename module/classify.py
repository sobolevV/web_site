from os import environ

environ["KERAS_BACKEND"] = "theano"
environ["MKL_THREADING_LAYER"] = "GNU"

import keras.backend

if keras.backend.backend() != 'theano':
    raise BaseException("This script uses other backend")
else:
    keras.backend.set_image_dim_ordering('th')

from keras.preprocessing import image
from keras.models import load_model
from itertools import product
from datetime import datetime
from pathlib import Path
from PIL import Image
import numpy as np


def convert_img(img, data):
    # normalize data
    data /= data.max()
    data *= 255
    data = data.astype('uint8')
    # convert to image & composite
    mask_layer = Image.fromarray(data, 'L')
    red_layer = Image.new('RGBA', img.size, (255, 0, 0, 110))
    def_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
    # create alpha mask layer
    red_mask = Image.composite(red_layer, def_layer, mask_layer)
    return Image.alpha_composite(img.convert('RGBA'), red_mask).convert('RGB')


def classify(l_image, model, m_name, delta=0.9, tile_size=None, number_of_classes=1, type_names=None):
    img_map = Image.open(l_image).convert('RGB')

    input_shape = model.input_shape[1:]

    elements = np.ceil(img_map.size[0] / tile_size) * np.ceil(img_map.size[1] / tile_size)
    img_size = (img_map.size[1], img_map.size[0])

    def generator():
        indexes = product(range(0, img_map.size[1], tile_size), range(0, img_map.size[0], tile_size))
        for (y, x) in indexes:
            img_crop = img_map.crop((x, y, x + tile_size, y + tile_size))
            x1 = image.img_to_array(img_crop)
            x1 /= 255
            x1 = x1.reshape((-1, *input_shape))
            yield x1

    start_time = datetime.now()
    print(' ┣━ start ┅', start_time.strftime('%H:%M:%S.%f'))
    result = model.predict_generator(generator(), steps=elements, use_multiprocessing=True)
    stop_time = datetime.now()
    print(' ┣━  stop ┅', stop_time.strftime('%H:%M:%S.%f'))
    print('┏┻━ delta ┅', stop_time - start_time)

    # create N layers for predicting classes
    res_layer = [np.zeros(img_size, dtype=float) for _ in range(number_of_classes)]

    indexes = product(range(0, img_map.size[1], tile_size), range(0, img_map.size[0], tile_size))
    for prediction, (y, x) in zip(result, indexes):
        for index, pred_value in enumerate(prediction):
            # index: 0 -- trees, 1 -- grass, 2 -- buildings
            if pred_value >= delta:
                res_layer[index][y:y + tile_size, x:x + tile_size] += pred_value

    output_dir = Path('results')
    output_dir.mkdir(exist_ok=True)

    for index in range(number_of_classes):
        if type_names is not None:
            output_file = output_dir / f'{m_name}_class-{type_names[index]}_{l_image.stem}.jpg'
        else:
            output_file = output_dir / f'{m_name}_class-{index}_{l_image.stem}.jpg'
        convert_img(img_map, res_layer[index]).save(output_file)


if __name__ == '__main__':
    models = list(Path('models').iterdir())
    images = list(Path('images').iterdir())
    # names = [
    #     'центр-плотной-застройки', 'квартальн-свободный', 'многоэтажки', 'современные-многоэтажки'
    # ]
    for model_path in models:
        print(f"┢━ processing `{model_path.name}' model")
        try:
            model = load_model(model_path)
        except NameError as error:
            print(f"┗┯┉ problem with `{model_path.name}' model [{error}]")
            continue
        tile_size = model.input_shape[2]
        number_of_classes = model.output_shape[1]
        for img in images:
            print(f"┗┳━ processing `{img.name}' image")
            try:
                classify(img, model, model_path.name, tile_size=tile_size,
                         number_of_classes=number_of_classes, delta=0.95)#,
                         # type_names=names)
            except NameError as error:
                print(f"┡┉┉ classification problem at `{img.name}' image [{error}]")
    print('┗┅ finished')
