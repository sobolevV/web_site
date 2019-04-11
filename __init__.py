import os.path
from flask import Flask, render_template, request, jsonify, json, redirect, Blueprint, send_from_directory
from json import loads
from task import TaskSystem

app = Flask(__name__)

app.config.update(DEBUG=True, SECRET_KEY='test-app-key')

tasker = TaskSystem()
archive = []

error = Blueprint('error', __name__)


def write_to_file(location_name, result):
    with open('data/' + str(location_name) + '.json', 'w') as f:
        json.dump(result, f)


# main page
@app.route('/', methods = ['POST', 'GET'])
def index():
    global archive
    # Простой возврат начальной страницы
    if request.method == "GET" and len(request.form) == 0:
        return render_template('index.html', requests=archive)


@app.route('/analyze', methods=["GET", "POST"])
def analyze_area():
    global archive
    data = dict(request.form)
    data = json.loads(data['values'])
    path = data['arrayOfCoords']
    place_name = data['location']
    classes = data['classes']

    # данные есть. возвращаем
    if os.path.isfile(f'data/{place_name}.json'):
        print('file  exist')
        with open(f'data/{place_name}.json') as f:
            data = json.load(f)
        res = {'address': place_name, 'requests': archive, 'paths': data}
        return jsonify(res)

    # добавляем задачу в список
    data_post = {"path": str(path), "place_name": place_name, 'classes': str(classes)}
    tasker.add_task(data_post)
    return 'wait'


# check results
@app.route('/check', methods=["GET", "POST"])
def check():
    print(request.form)
    location_name = request.form['location']
    # location_name = location_name.decode('utf-8', 'ignore')
    print(location_name)
    res = tasker.check_status(location_name)
    # если рузальтат готов, то записываем в файл
    # if res == 'wait':
    #     return "wait"
    if res == "fail":
        return render_template('500.html'), 500
    elif res == "wait":
        return "wait"
    else:
        return_data = {'paths': res}
        write_to_file(location_name, res)

        archive.insert(0, [location_name])
        if len(archive) == 11:
            archive.pop()

        return_data.update({'location': location_name, 'requests': archive})
        return jsonify(return_data)


@app.route('/ready', methods=["GET", "POST"])
def get_ready():
    location_name = request.form['location']
    print(location_name)
    with open(f'data/{location_name}.json') as f:
        data = json.load(f)
    return jsonify({"paths": data})


# get form
@app.route('/results', methods=["GET", "POST"])
def get_results():
    return render_template('result.html')


# check requests
@app.route('/archive', methods=["GET", "POST"])
def get_requests():
    return jsonify(archive)


# Errors and other
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'logo.ico')


if __name__ == "__main__":
    app.run()