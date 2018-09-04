from flask import Flask, render_template, request, jsonify, json, redirect
from app.module import main
from app.module.get_tile import get_map
from keras.models import load_model
import keras.backend as K
from os import environ
import keras.backend
import os.path
from math import fabs
#import theano
import threading, time
from multiprocessing.pool import ThreadPool
app = Flask(__name__)

environ["KERAS_BACKEND"] = "theano"
environ["MKL_THREADING_LAYER"] = "GNU"
if keras.backend.backend() != 'theano':
  raise BaseException("This script uses other backend")
else:
   keras.backend.set_image_dim_ordering('th')
model = load_model('module/new_model_25_bright.hdf5')

# proxy_list = main.parseProxy()
# proxy_index = 0             #индекс прокси, к которому обращаются
# proxy_request_counter = 0   #счетчик запросов к 1 прокси
# proxy_time_start = time.time()
request_list = []
@app.route('/', methods = ['POST', 'GET'])
def index():
    global proxy_time_start, proxy_list, proxy_request_counter, proxy_index, request_list
    if request.method == "POST" and len(request.form) != 0:
        print('post')
        # proxy_time_end = time.time()
        # #print('proxy start, end', proxy_time_start, proxy_time_end, proxy_time_start - proxy_time_end)
        # if fabs(proxy_time_start - proxy_time_end) > 60 * 20: # 20 minutes
        #     #print('time proxy end')
        #     pool = ThreadPool(processes=1)
        #     proxy_list = pool.apply_async(main.parseProxy, ()).get()
        #     proxy_time_start = proxy_time_end
        #     print('proxy from thread', proxy_list)

        lon = request.form['lon']
        lat = request.form['lat']

        #Список 5 последних запросов
        request_list.insert(0, [request.form['address'], str(lat) + " " + str(lon)])
        if len(request_list) == 11:
            request_list.pop()
        #проверка на существование данных
        if (os.path.isfile('data/'+str(lat)+'_'+str(lon)+'.json')):
            print('file  exist')
            with open('data/'+str(lat) + '_' + str(lon) + '.json') as f:
                res = json.load(f)
        else:#если данных нет, то сделать
            print('file not exist')
            # proxy_request_counter += 1
            # if proxy_request_counter >= 5:
            #     if proxy_index == len(proxy_list) - 1:
            #         proxy_index = 0
            #     else:
            #         proxy_index += 1
            #Формирование json внутри классификации объектов
            #main.getImage(lat, lon, '109.201.96.171:31773')
            #res = main.classify(main.getImage(lat, lon, proxy_list[proxy_index]), tile_size=25, model=model, delta=0.95)
            img_map = get_map('newTest.png', float(lat), float(lon), 20, neighbourhood=7)
            res = main.classify(img_map, tile_size=25, model=model, delta=0.97)#main.classify(main.getImage(lat, lon, '109.201.96.171:31773'), tile_size=25, model=model, delta=0.95)
            with open('data/'+str(lat)+'_'+str(lon)+'.json', 'w') as f:
                json.dump(res, f, indent=4)

        res.update({'lat': lat, 'lon': lon, 'requests': request_list})
        print(res, request_list)
        return jsonify(res)

    if request.method == "GET" and len(request.form) == 0:
        print('Get', request_list)
        return render_template('index.html', requests=request_list)


@app.route('/share/lat:<float:lat>_lon:<float:lon>_lng:<string:language>', methods=['GET'])
def places_view(lat, lon, language):
    print(language)
    if (os.path.isfile('data/'+str(lat)+'_'+str(lon)+'.json')):
        with open('data/'+str(lat) + '_' + str(lon) + '.json') as f:
            res = json.load(f)
        res.update({'lat': lat, 'lon': lon})
        return render_template('share.html', res=json.dumps(res), lng=language)
    else:
        return render_template('index.html')

# @app.route('/error', methods=['GET'])
# def places_view():
#     return render_template('error.html')
# @app.errorhandler(Exception)
# def exception_handler(error):
#     return render_template('error.html', error=error)

if __name__ == "__main__":
    app.run()