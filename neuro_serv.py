import json
import numpy as np
import re
import cv2
import keras.backend as K
from time import sleep
from ast import literal_eval
from flask import Flask, request, jsonify, json
from module.neuro_processing import *
from module.get_tile import get_map, get_one_tile
from module.path_to_tile_indexes import get_indexes
from keras.models import load_model
from os import environ
environ["KERAS_BACKEND"] = "theano"
environ["MKL_THREADING_LAYER"] = "GNU"
if K.backend() != 'tensorflow':
  raise BaseException("This script uses other backend")
else:
   K.set_image_dim_ordering('tf')


class_list_to_model = {
        'trees': {
            'path': 'module\\models\\model_trees.h5',
            'normalization': normalize_mean_std,
            'tile_size': 256,
        },
        'garage': {
            'path': 'module\\models\\model_garage.h5',
            'normalization': normalize_mean_std,
            'tile_size': 256
        },
        'cars': {
            'path': "module\\models\\model_cars.h5",
            'normalization': normalize_div255,
            'tile_size': 256
        },

     }
# 'buildings': {
#             'path': "module\\models\\unet_buildings.h5",
#             'normalization': normalize_mean_std,
#             'tile_size': 256
#         }
models = {}
for key in class_list_to_model.keys():
    models.update({key: load_model(class_list_to_model[key]['path'], custom_objects={
                                                                        'dice_coef_loss_bce': dice_coef_loss_bce,
                                                                        'dice_coef': dice_coef})})
    print(f'model {key} has been loaded')

app = Flask(__name__)

@app.route('/', methods=['GET', "POST"])
def main():
    #  check method
    if request.method == "POST":
        zoom = 18
        data = request.get_json()
        path = re.sub(" ", "", data['path'])
        classes = re.sub(" ", "", data['classes'])
        path = literal_eval(path)
        classes = literal_eval(classes)
        # sent request to google to get img
        try:
            combin = get_indexes(path)
            image = get_my_map(combin, zoom=zoom)
            index_image_arr = []

            # for index_xy in indexes:
            #     sleep(1.0)
            #     image_arr = get_one_tile(index_xy[0], index_xy[1], zoom)
            #     while image_arr is None:
            #         sleep(2.0)
            #         image_arr = get_one_tile(index_xy[0], index_xy[1], zoom)
            #     # cv2.imwrite(f'{index_xy[0]}_{index_xy[1]}.png', image_arr)
            #     index_image_arr.append([(index_xy[0], index_xy[1]), image_arr])
            # img_map, tile_index = get_map(float(lat), float(lon), zoom=18, neighbourhood=0)

            res = classify(image, classes, path, combin[0], class_list_to_model, models)
            return json.dumps(res)
        except Exception as e:
            print("Error. Can't run image recognition ", e)
            return 'fail'
    if request.method == "GET":
        print('get')

    return 'ok'


if __name__ == '__main__':
    app.run(port=5055)
