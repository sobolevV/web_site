import os.path
from flask import Flask, render_template, request, jsonify, json, redirect, sessions, send_from_directory, Blueprint, \
    session, url_for
from json import loads
from forms import LoginForm, RegistrationForm
from flask_wtf import csrf
from task import TaskSystem
from flask_mail import Message, Mail
from flask_login import UserMixin, LoginManager
from requests import post

tasker = TaskSystem()
error = Blueprint('error', __name__)
app = Flask(__name__)
app.config.update(DEBUG=True, SECRET_KEY='test-app-key')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'landprober@gmail.com'
app.config['MAIL_PASSWORD'] = 'landpassword2019'

archive = []
server_address = 'http://127.0.0.1:5055'
mail = Mail(app=app)
login_manager = LoginManager().init_app(app)

# ___________________________________________________________________________________
def send_activation_token(user_mail, token):
    confirm_url = url_for('activate_mail', _external=True, token=token)
    msg = Message("Регистрация LandProber",
                  sender=("landprober@gmail.com"),
                  html=render_template("email.html", confirm_url=confirm_url),
                  recipients=[user_mail])
    with mail.connect() as conn:
        conn.send(msg)


def get_error_messages(form):
    message = []
    for item, err_text in form.errors.items():
        if len(err_text) > 1:
            for sub_err in err_text:
                message.append(sub_err)
        else:
            message.append(err_text)
    return sum(message, [])


def prepare_answer(answer):
    if 'session' in answer.keys():
        if answer['session'] is not None:
            for key, val in answer['session'].items():
                session[key] = val
    if answer['type'] == "message" or answer['type'] == "error":
        return jsonify({'type': 'message', 'text': answer['message_text']})
    elif answer['type'] == "redirect":
        return redirect(answer['path'])
    elif answer['type'] == "render_template":
        variables = dict(answer['message_text'])
        return render_template(answer['path'], **variables)
# ___________________________________________________________________________________


def write_to_file(location_name, result):
    with open('data/' + str(location_name) + '.json', 'w') as f:
        json.dump(result, f)


# main page
@app.route('/', methods=['POST', 'GET'])
def index():
    global archive
    # Простой возврат начальной страницы
    if request.method == "GET" and len(request.form) == 0:
        csrf.generate_csrf()
        if "mail" in session:
            # login = True 'password': session['password1']
            user_data = {'name': session['mail'], 'mail': session['mail']}
            return render_template('index.html', requests=archive, login=True, user=user_data)
        else:
            login_form = LoginForm()
            registration_form = RegistrationForm()
            return render_template('index.html', requests=archive, login=False,
                                   login_form=login_form, registration_form=registration_form)


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
    location_name = request.form['location']
    print(location_name)
    res = tasker.check_status(location_name)
    if res == "fail":
        return render_template('500.html'), 500
    elif res == "wait":
        return "wait"
    else:
        # если рузальтат готов, то записываем в файл
        return_data = {'paths': res, 'location': location_name}
        write_to_file(location_name, return_data)
        archive.insert(0, [location_name])
        if len(archive) == 11:
            file_rm = archive.pop(0)[0]
            os.remove('data/' + str(file_rm) + '.json')
        return_data.update({'requests': archive})
        return jsonify(return_data)


@app.route('/ready', methods=["GET", "POST"])
def get_ready():
    location_name = request.form['location']
    print(location_name)
    with open(f'data/{location_name}.json') as f:
        data = json.load(f)
    data.update({'requests': archive})
    return jsonify(data)


@app.route('/ready/location=<string:location_name>', methods=["GET", "POST"])
def get_ready_link(location_name):
    # location_name = request.form['location']
    print('shared', location_name)
    with open(f'data/{location_name}.json') as f:
        data = json.load(f)
    data.update({'location': location_name.encode('utf-8'), 'requests': archive})
    return render_template("share.html", shared_data=data)


# get form
@app.route('/results', methods=["GET", "POST"])
def get_results():
    return render_template('result.html')


# check requests
@app.route('/archive', methods=["GET", "POST"])
def get_requests():
    return jsonify(archive)


@app.route('/activate/<string:token>', methods=["GET", "POST"])
def activate_mail(token):
    try:
        # Пользователь перешел по ссылке активации
        # mail = confirm_token(token)
        answer = post(server_address + '/activate/' + str(token)).json()
        answer = prepare_answer(answer)
        # user_coll.find_one_and_update({'mail': mail}, {'$set': {'confirmed': True}})
        # user = user_coll.find_one({'mail': mail})
        # print(f'user {mail} activated \n', user)
        return answer # redirect('/')
    except Exception as e:
        print("User didn't activated. ", e)
        message = "Вероятно срок действия ссылки истек или она является неверной. Попробуйте снова."
        return render_template("error.html", message=message)


@app.route('/registration', methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        regist_form = RegistrationForm(request.form)
        if regist_form.validate():
            regist_form = {'mail': regist_form.mail.data, 'password': regist_form.password.data,
                            'name': regist_form.name.data}
            # отправить на сервер, получить ответ
            answer = post(server_address + '/registration', json=regist_form).json()
            # Запрос успешный
            if answer['type'] == 'redirect':
                token = answer['values']['token']
                user_mail = answer['values']['mail']
                send_activation_token(user_mail, token)

            answer = prepare_answer(answer)
            return answer
            # проверка на существование пользователя
            # user_cursor = user_coll.find({'mail': regist_form.data['mail']})
            # if user_cursor.count():
            #     return jsonify({"type": "message",
            #                     "text": ["Пользователь с таким почтовым адресом уже существует."]})

            # user = create_user(regist_form.data)
            # user_coll.insert_one(user)
            # user_mail = user['mail']
            # token = generate_confirmation_token(user_mail)

        else:
            # Форма пользователя не прошла валидацию
            message = get_error_messages(regist_form)
            # Сообщить пользователю о ошибках
            return jsonify({"type": "message",
                            "text": message})


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # print(session['csrf_token'])
        login_form = LoginForm(request.form)
        if login_form.validate():
            data = {'mail': login_form.mail.data, 'password': login_form.password.data}
            answer = post(server_address + '/login', json=data).json()
            answ = prepare_answer(answer)
            return answ
            # user = user_coll.find({"mail": login_form.mail.data, 'password': login_form.password.data})
            # if user.count() == 0:
            #     return jsonify({"type": "message",
            #                     "text": ["Пользователя с таким логином и паролем не существует"]})
            # session['mail'] = login_form.mail.data
            # session['password'] = login_form.password.data
        else:
            message = get_error_messages(login_form)
            return jsonify({"type": "message",
                            "text": message})
    # return redirect("/")


@app.route('/logout', methods=["GET", "POST"])
def logout():
    global archive
    session.pop('mail', None)
    session.pop('password', None)
    return redirect("/")


# Errors and other
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route("/robots.txt", methods=["GET"])
def google_search():
    return send_from_directory("", "robots.txt")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'logo.ico')


if __name__ == "__main__":
    app.run()


