import json
import numpy as np
import re
# import keras.backend as K

from ast import literal_eval
from flask import Flask, request, jsonify, json
from module.neuro_processing import *
from module.get_tile import get_map, get_one_tile
from module.path_to_tile_indexes import get_indexes
from keras.models import load_model
from os import environ
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer
from pymongo import MongoClient
from datetime import datetime
from module.metrics import *

# ____________________________________________  БД  ______________________________________________
client = MongoClient()
if "LandProber" in client.list_database_names():
    print("DB exist")
else:
    print('Create DB LANDPROBER')
db = client['LandProber']

db.drop_collection('user')
print("Список коллекций:", db.list_collection_names())
user_coll = db['user']

# ____________________________________________  МОДЕЛИ  ______________________________________________

class_list_to_model = {
        'trees': {
            'path': 'module\\models\\model_trees.h5',
            'normalization': normalize_mean_std,
            'normalize_hist': True,
            'delta': 0.8,
            'simplify_val': 0.5,
            'input_size': 256,
            'output_size': 256,
            'sub_classes': {
                'count': 1,
                    'names_ru': ['Деревья']
            }
        },
        'garage': {
            'path': 'module\\models\\model_garage.h5',
            'normalization': normalize_mean_std,
            'normalize_hist': True,
            'delta': 0.7,
            'simplify_val': 1,
            'input_size': 256,
            'output_size': 256,
            'sub_classes': {
                'count': 1,
                    'names_ru': ['Гаражи']
            }
        },
        'cars': {
            'path': "module\\models\\model_cars.h5",
            'normalization': normalize_div255,
            'normalize_hist': True,
            'delta': 0.65,
            'simplify_val': 0.2,
            'input_size': 256,
            'output_size': 256,
            'sub_classes': {
                'count': 1,
                    'names_ru': ['Автомобили']
            }
        },
        'buildings': {
            'path': "module\\models\\unet_buildings_multi.h5",
            'normalization': normalize_127_1,
            'normalize_hist': True,
            'delta': 0.6,
            'simplify_val': 1.5,
            'input_size': 512,
            'output_size': 256,
            'sub_classes': {
                'count': 3,
                'names': ['apartments', 'privat', 'other'],
                'names_ru': ['Многоэтажные здания', 'Одноэтажные здания', 'Иные строения']
            }
        },
        'rails': {
            'path': "module\\models\\unet_rails.h5",
            'normalization': normalize_127_1,
            'normalize_hist': True,
            'delta': 0.7,
            'simplify_val': 3,
            'input_size': 256,
            'output_size': 256,
            'sub_classes': {
                'count': 1,
                'names_ru': ['Железная дорога']
            }
        }
     }

# 'water': {
#             'path': "module\\models\\unet_water_GRAY_d255.h5",
#             'normalization': normalize_div255,
#             'normalize_hist': False,
#             'delta': 0.8,
#             'input_size': 256,
#             'output_size': 256,
#             'sub_classes': {
#                 'count': 1,
#                 'names_ru': ['Железная дорога']
#             }
#         }

# model_buildings
models = {}
for key in class_list_to_model.keys():
    models.update({key: load_model(class_list_to_model[key]['path'],
                                   custom_objects={
                                        'dice_coef_loss': dice_coef_loss,
                                        'dice_coef': dice_coef,
                                        'dice_coef_multilabel': dice_coef_multilabel,
                                        'weighted_cross_entropy': weighted_cross_entropy,
                                        'balanced_cross_entropy': balanced_cross_entropy,
                                        'mean_iou': mean_iou}
                                   )})
    print(f'model {key} loaded')


# _____________________________________________   КОНФИГ   _______________________________________________________
app = Flask(__name__)
app.config.update(DEBUG=False, SECRET_KEY='test-app-key')
app.config['SECURITY_PASSWORD_SALT'] = "test-app-key_two"

# ______________________________________________    КЛЮЧИ    _______________________________________


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=3600 * 72)
    return email

# ______________________________________________    ПОЛЬЗОВАТЕЛЬ    _______________________________________


def create_user(user_data):
    user = {
            'name': user_data['name'],
            'mail': user_data['mail'],
            'password': user_data['password'],
            'confirmed': False,
            'account_date': datetime.now().strftime("%Y-%m-%d"),
            'requests': []}
    return user

# def send_activation_token(user_mail, token):
#     confirm_url = url_for('activate_mail', _external=True, token=token)
#     msg = Message("Регистрация LandProber",
#                   sender=("landprober@gmail.com"),
#                   html=render_template("email.html", confirm_url=confirm_url),
#                   recipients=[user_mail])
#     with mail.connect() as conn:
#         conn.send(msg)
# ___________________________________________________________________________________


def create_response(type, path=None, message=None, session_vals=None, vals=None):
    response = {'type': type}
    if session_vals is not None:
        response['session'] = session_vals
    if vals is not None:
        response['values'] = vals
    if type == "message" or type == "error":
        response.update({'message_text': message})
    elif type == "render_template":
        response.update({'path': path, 'message_text': message})
    elif type == "redirect":
        response.update({'path': path})

    return jsonify(response)


@app.route('/analyze', methods=['GET', "POST"])
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
            res = classify(image, classes, path, combin[0], class_list_to_model, models)
            return json.dumps(res)
        except Exception as e:
            print("Error. Can't run image recognition ", e)
            return 'fail'
    if request.method == "GET":
        print('get')

    return 'ok'


@app.route('/activate/<string:token>', methods=["GET", "POST"])
def activate_mail(token):
    try:
        mail = confirm_token(token)
        user_coll.find_one_and_update({'mail': mail}, {'$set': {'confirmed': True}})
        # user = user_coll.find_one({'mail': mail})
        # print(f'user {mail} activated \n', user)
        # session['mail'] = mail
        session_val = {'mail': mail}
        return create_response(type="redirect", path="/", session_vals=session_val) # redirect('/')
    except Exception as e:
        print("User didn't activated. ", e)
        message = "Вероятно срок действия ссылки истек или она является неверной. Попробуйте снова."
        return create_response("render_template", "error.html", message=message)
        # return render_template("error.html", message=message)


@app.route('/registration', methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        regist_form = request.get_json()
        # проверка на существование пользователя
        user_coll.delete_one({'mail': regist_form['mail']})
        user_cursor = user_coll.find({'mail': regist_form['mail']})
        if user_cursor.count():
            return jsonify({"type": "message",
                            "message_text": ["Пользователь с таким почтовым адресом уже существует."]})

        user = create_user(regist_form)
        user_coll.insert_one(user)
        user_mail = user['mail']
        token = generate_confirmation_token(user_mail)
        values = {'mail': user_mail, 'token': token}
        # send_activation_token(user_mail, token)
        # else:
        #     message = get_error_messages(regist_form)
        #     return jsonify({"type": "message",
        #                     "text": message})
        return create_response('redirect', path='/', vals=values)# redirect("/")




@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # print(session['csrf_token'])
        # login_form = LoginForm(request.form)
        login_form = request.get_json()
        user = user_coll.find({"mail": login_form['mail'], 'password': login_form['password']})
        if user.count() == 0:
            return create_response(type='message', message="Пользователя с таким логином и паролем не существует")

        session_val = {
            'mail': login_form['mail']
        }
    return create_response(type='redirect', path='/', session_vals=session_val) #redirect("/")


if __name__ == '__main__':
    app.run(port=5055)
