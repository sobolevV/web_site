from os import environ
import keras.backend
environ["KERAS_BACKEND"] = "theano"
environ["MKL_THREADING_LAYER"] = "GNU"
if keras.backend.backend() != 'theano':
  raise BaseException("This script uses other backend")
else:
   keras.backend.set_image_dim_ordering('th')

from flask import Flask, request, jsonify, json, redirect, Blueprint
from module.neuro_processing import classify
from module.get_tile import get_map
from keras.models import load_model
import json

import keras.backend as K
import os.path

model = load_model('module/new_model_25_bright.hdf5')

app = Flask(__name__)
# load model
@app.route('/', methods = ['GET', "POST"])
def main():
    #  check method
    if request.method == "POST":
        # get lat, lon
        lon = request.form['lon']
        lat = request.form['lat']
        print('post', lat, lon )
        # sent request to google to get img
        img_map = get_map(float(lat), float(lon), 20, neighbourhood=7)

        res = classify(img_map, tile_size=25, model=model, delta=0.85)
        # analyse image with neuro

        # get contours with cv2

        # in every contour convert pixels to lat-lon

        # format json and return
        return json.dumps(res)
    if request.method == "GET":
        print('get')

    return 'ok'
if __name__ == '__main__':
      app.run(port=5001)