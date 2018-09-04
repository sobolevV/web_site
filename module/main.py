from app.module.ya_maps import YandexMapParser
#from keras.models import load_model
#from keras.models import Model
from keras.preprocessing import image
import numpy as np
import io
import bs4 as bs
import urllib.request
from selenium import webdriver
import re
import time
import numpy as np
import cv2
import time, schedule
from app.module.get_tile import *
from PIL import Image, ImageDraw
names = ['tree', 'grass', 'other' ]
objects = ['#EA0F0F', '#FAE7B5', '#957B8D']

def normalization(img):
	for i in range(3):
		min = img[:, i].min()
		max = img[:, i].max()
		if min != max:
			img[:, i ] -= min
			img[:, i ] *= (255./(max-min))
	return img

#цвет пиксела RGB -> значение яркости
def lum(c):
#формула, которая обычно используется для определения яркости
	return int(0.3*c[0] + 0.59*c[1] + 0.11*c[2])
def r(c): #цвет пиксела RGB -> значение R
	return c[0]
def g(c): #цвет пиксела RGB -> значение G
	return c[1]
def b(c): #цвет пиксела RGB -> значение B
	return c[2]


def normalization_image(src):
#Усиление границ изображения
    #Image.open(io.BytesIO(src)).convert('RGB').save('beforeNorm.png')
    img_np = np.asarray(src)

    # nparr = np.fromstring(src, np.uint8)
    # nparr = nparr.reshape((255, 255))
    # img_np = cv2.imdecode(nparr, cv2.COLOR_RGB2BGR)

    kernel3 = np.array([[-0.1, -0.1, -0.1], [-0.1, 2, -0.1], [-0.1, -0.1, -0.1]])
#kernel3_2 = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) # <-- Более резкий
#kernel5 = np.array([[-0.1, 0, -0.1, 0, -0.1], [0, 0, 0, 0, 0], [-0.1, 0, 2, 0, -0.1], [0, 0, 0, 0, 0], [-0.1, 0, -0.1, 0, -0.1]])
#kernel7 = np.array(
#	[[0, 0, 0, -0.1, 0, 0, 0], [0, -0.1, 0, 0, 0, -0.1, 0], [0, 0, 0, 0, 0, 0, 0], [-0.1, 0, 0, 2, 0, 0, -0.1],
#		 [0, 0, 0, 0, 0, 0, 0], [0, -0.1, 0, 0, 0, -0.1, 0], [0, 0, 0, -0.1, 0, 0, 0]])
#nparr = np.fromstring(src, np.uint8)

    src = cv2.filter2D(img_np, -1, kernel=kernel3)

    resR = src[:, :,2]
    resG = src[:, :,1]
    resB = src[:, :,0]

    resR_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')
    resG_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')
    resB_dst = np.empty(shape=(len(src), len(src[0])), dtype='uint8')

    # расстягиевание каждого слоя
    cv2.equalizeHist(resR, resR_dst)
    cv2.equalizeHist(resG, resG_dst)
    cv2.equalizeHist(resB, resB_dst)

    resR_dst = np.mean(np.array([resR, resR_dst]), axis=0)
    resG_dst = np.mean(np.array([resG, resG_dst]), axis=0)
    resB_dst = np.mean(np.array([resB, resB_dst]), axis=0)

    resR_dst = np.array(resR_dst).astype('uint8')
    resG_dst = np.array(resG_dst).astype('uint8')
    resB_dst = np.array(resB_dst).astype('uint8')

    #BRG
    out_img = np.dstack((resB_dst, resG_dst, resR_dst))
    cv2.imshow('namewef', out_img)
    return Image.fromarray(out_img, 'RGB')

def getImage(lat, lon, proxy):
    ya = YandexMapParser(width=2500, height=2500, proxy=proxy)
    url = 'https://www.google.ru/maps/@{},{},350m/data=!3m1!1e3?hl=ru'.format(lat, lon)
    r = ya.screenshot(url=url)
    with open(f'image-res.png', 'wb') as f:
        f.write(r)

    return r

def classify(img_Src, tile_size, model, delta):

    #test = Image.fromarray(normalization_image(img_Src))
    #img_map = Image.fromarray(normalization_image(img_Src))#Image.open(io.BytesIO(normalization_image(img_Src))).convert('RGB')#Image.frombytes(mode='RGB', size=(2500, 2500), data=io.BytesIO(img_Src))#Image.open(img_Src).convert('RGB')
    #img_map = Image.frombytes("RGB", 2500, img_Src)
    img_Src.save('newTest.png')
    w, h = img_Src.size
    dif = (w - 2500)/2
    #print(w, h)
    #img_Src.save('newTest-beforeCrop.png')
    #img_map = img_Src.crop((dif, dif, w-dif, h-dif))
    # img_Src = img_Src.crop((110, 115, w - 290, h - 128))
    img_map = img_Src.resize((2500, 2500))
    img_map = normalization_image(img_map)
    print(img_map.size)
    #draw = ImageDraw.Draw(img_map)
    json_result = {}

    trees = 0
    # draw = ImageDraw.Draw(img_map)
    for i in range(round(img_map.size[0] / tile_size)):
        for j in range(round(img_map.size[1] / tile_size)):
            img_crop = img_map.crop(
                (i * tile_size, j * tile_size, i * tile_size + tile_size, j * tile_size + tile_size))
            # img_crop = img_crop.resize((25,25))
            x1 = image.img_to_array(img_crop).astype('float32')
            x1 /= 255
            x1 = np.expand_dims(x1, axis=0)

            prediction = model.predict(x1.reshape((-1, 3, tile_size, tile_size)))
            print(prediction)
            max_index = prediction[0].argmax()

            if prediction[0][max_index] >= delta and max_index == 0:
                json_result.update({
                    str(i)+':'+str(j): {
                        'i': str(i),
                        'j': str(j),
                        'color': objects[max_index],
                        'delta': True
                    }
                })
                trees += 1
                ##########
            else:
                json_result.update({
                    str(i) + ':' + str(j): {
                        'delta': False
                        }
                })

            print(json_result[str(i)+':'+str(j)])
    json_result.update({'objects': {}})
    for i in range(len(objects)):
        json_result['objects'].update( { names[i]: {'color': objects[i], 'count': trees} } )
    return json_result

def parseProxy():
    url = 'http://free-proxy.cz/ru/proxylist/country/RU/http/ping/all' #'https://hidemy.name/ru/proxy-list/?country=RU#list'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    capabilities = webdriver.DesiredCapabilities.CHROME
    # prox.add_to_capabilities(capabilities)

    browser = webdriver.Chrome(executable_path='C:\\Users\\Vadim\\chrome_driver\\chromedriver.exe',
                               desired_capabilities=capabilities, options=options)
    # browser.set_window_size(2500, 2500)
    browser.get(url)
    time.sleep(5)
    #script = """
    #  window.setTimeout(click(), 6000);
    # function click(){
    #     document.getElementsByClassName('button button_green ')[0].click();
    #     document.getElementById('t_h').click()
    # }
    #    """
    script = """document.getElementById('frmsearchFilter-send').click()"""
    try:
        browser.execute_script(script)
        print('execute script for parsing')
    except Exception:
        print('Function - parseProxy: Script didn\'t execute ')

    time.sleep(3)
    soup = bs.BeautifulSoup(browser.page_source, 'lxml')

    #table = soup.body.table['proxy_list']
    tr = soup.find_all('table')[1].find_all('tr')
    proxy_list = []
    for i in tr:
        td = i.find_all('td')
        if len(td) > 1:
            row = [j.text for j in td]
        #print(re.sub(r'\D', '', row[-4]))
            if row[6] == 'прозрачный':
                #print(re.sub(r'\D^.', '', row[0]) + ':' + row[1])
                proxy_list.append(row[0].split(')')[-1] + ':' + row[1])
                #print(proxy_list[-1])
    print('proxy count = ', len(proxy_list))


    return proxy_list
