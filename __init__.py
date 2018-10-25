
from flask import Flask, render_template, request, jsonify, json, redirect, Blueprint
# from module import main
# from module.get_tile import get_map
import os.path
# from math import fabs
from json import loads
from requests import post
from task import TaskSystem

app = Flask(__name__)
app.config.update(DEBUG=True, SECRET_KEY='test-app-key')

tasker = TaskSystem()
request_list = []

error = Blueprint('error', __name__)

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

            resp = tasker.add_task(data_post)
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