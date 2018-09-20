from os import environ
import keras.backend
environ["KERAS_BACKEND"] = "theano"
environ["MKL_THREADING_LAYER"] = "GNU"
if keras.backend.backend() != 'theano':
  raise BaseException("This script uses other backend")
else:
   keras.backend.set_image_dim_ordering('th')

from flask import Flask, render_template, request, jsonify, json, redirect, Blueprint
from module import main
from module.get_tile import get_map
from keras.models import load_model
import keras.backend as K
import os.path
from math import fabs
#import theano
import threading, time
from multiprocessing.pool import ThreadPool
app = Flask(__name__)

model = load_model('module/new_model_25_bright.hdf5')
error = Blueprint('error', __name__)

request_list = []
# main page
@app.route('/', methods = ['POST', 'GET'])
def index():
    global request_list
    if request.method == "POST" and len(request.form) != 0:
        print('post')
        lon = request.form['lon']
        lat = request.form['lat']

        # Список 5 последних запросов
        request_list.insert(0, [request.form['address'], str(lat) + " " + str(lon)])
        if len(request_list) == 11:
            request_list.pop()
        # проверка на существование данных
        if (os.path.isfile('data/'+str(lat)+'_'+str(lon)+'.json')):
            print('file  exist')
            with open('data/'+str(lat) + '_' + str(lon) + '.json') as f:
                res = json.load(f)
        else: # если данных нет, то сделать
            print('file not exist')
            img_map = get_map('newTest.png', float(lat), float(lon), 20, neighbourhood=7)
            res = main.classify(img_map, tile_size=25, model=model, delta=0.97)
            with open('data/'+str(lat)+'_'+str(lon)+'.json', 'w') as f:
                json.dump(res, f, indent=4)
        # Добавить данные по координатам
        res.update({'lat': lat, 'lon': lon, 'requests': request_list})
        print(res, request_list)
        return jsonify(res)
    # Простой возврат начальной страницы
    if request.method == "GET" and len(request.form) == 0:
        print('Get', request_list)
        return render_template('index.html', requests=request_list)

# share page
@app.route('/share/lat:<float:lat>_lon:<float:lon>_lng:<string:language>', methods=['GET'])
def share_view(lat, lon, language):
    print(language)
    if (os.path.isfile('data/'+str(lat)+'_'+str(lon)+'.json')):
        with open('data/'+str(lat) + '_' + str(lon) + '.json') as f:
            res = json.load(f)
        res.update({'lat': lat, 'lon': lon})
        return render_template('share.html', res=json.dumps(res), lng=language)
    else:
        return render_template('index.html')

# error
@app.route('/error', methods=['GET', 'POST'])
def err():
    descr = str(request.form['descr'])
    return render_template('error.html', error=descr)

if __name__ == "__main__":
    app.run()