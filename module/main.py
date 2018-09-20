from keras.preprocessing import image
import numpy as np
import io
import urllib.request
import re
import time
import numpy as np
import cv2
from module.get_tile import *
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

def classify(img_Src, tile_size, model, delta):

    w, h = img_Src.size
    img_map = img_Src.resize((2500, 2500))
    # img_map = normalization_image(img_map)
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
