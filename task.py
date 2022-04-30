from threading import Thread, Lock
from random import randrange
from time import sleep
from json import loads
from requests import post

# res = post('http://79.170.167.30:61102/', data="{'lat': '48.70829492856548', 'lon': '44.514713287353516'}")
# print(res.text)


class TaskSystem:
    def __init__(self):
        self.list = []
        self.id = 0
        self.mutex = Lock()
        self.results = {}
        self.running = True
        self.thread = Thread(target=self.__thread)
        self.thread.start()

    def __del__(self):
        with self.mutex:
            self.running = False
        self.thread.join()

    def __thread(self):
        while True:
            sleep(0.1)
            with self.mutex:
                # если все запросы обработаны, то ждем
                if self.id >= len(self.list):
                    continue
                else:
                    # иначе переходим к след.
                    # если статус этого запроса - ждет
                    if self.list[self.id][1] == 'wait':
                        # посылаем запрос
                        print(f'make request for {self.id}')
                        # res =  post('http://79.170.167.30:61102/', data=self.list[self.id][0])
                        try:
                            res = post('http://127.0.0.1:5055/analyze', json=self.list[self.id][0]).json()
                            # res = res.text
                            self.list[self.id][1] = 'done'
                            print('RESULT: ', res)
                        except Exception as e:
                            res = "fail"
                            self.list[self.id][1] = 'fail'
                            print("Can't post to server \n", e)
                        # добавляем рузльтаты - название места : результат
                        self.results.update({str(self.list[self.id][0]['place_name']): {
                                'status': self.list[self.id][1],
                                'data': res
                            }
                        })

                        self.id += 1
                if not self.running:
                    break

    def add_task(self, area_address):
        with self.mutex:
            self.list.append([area_address, 'wait'])

    def check_status(self, place_name):
        with self.mutex:
            # если в списке результатов есть совпадение
            for key in self.results.keys():
                if place_name == key and self.results[key]['status'] == "done":
                    # print('key ' + str(key) + 'ready')
                    res_check = self.results[key]['data']
                    del self.results[key]
                    return res_check
                elif place_name == key and self.results[key]['status'] == "fail":
                    del self.results[key]
                    return 'fail'

            # иначе проверяем - есть ли в списке запросов
            for name_status in self.list:
                if name_status[0]['place_name'] == place_name:
                    return 'wait'
            # если нет в списке запросов
            return 'fail'
