from os import environ
# import keras.backend
# environ["KERAS_BACKEND"] = "theano"
# environ["MKL_THREADING_LAYER"] = "GNU"
# if keras.backend.backend() != 'theano':
#   raise BaseException("This script uses other backend")
# else:
#    keras.backend.set_image_dim_ordering('th')

from flask import Flask, render_template, request, jsonify, json, redirect, Blueprint
from module import main
from module.get_tile import get_map
import os.path
from collections import deque
from math import fabs
from json import loads
from celery import Celery
import redis
from requests import post

r = redis.StrictRedis(host='127.0.0.1', port=6379)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.update(CELERY_BROKER_URL='redis://127.0.0.1:6379',
                  CELERY_RESULT_BACKEND='redis://127.0.0.1:6379')
celery = make_celery(app)

error = Blueprint('error', __name__)

@celery.task()
def get_detect_result(data_post):
    res = post('http://127.0.0.1:5001/', data=data_post)
    return res

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
        else:
            # если данных нет, то сделать
            print('file not exist')
            # ПОЛСЫЛАЕМ ЗАПРОС К ДРУГОМУ СЕРВЕРУ
            # post to
            data_post = {"lat": lat, "lon": lon}
            # add to queue

            resp = get_detect_result.delay(data_post)
            # resp.wait()
            res = loads(resp)
            print(type(res))

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