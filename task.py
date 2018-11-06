from threading import Thread, Lock
from random import randrange
from time import sleep
from json import loads
from requests import post

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
                    # если статус этого запроса ждет
                    if self.list[self.id][1] == 'wait':
                        # посылаем запрос
                        print(f'make request for {self.id}')
                        res = post('http://127.0.0.1:5001/', data=self.list[self.id][0])
                        print(res.text)
                        # добавляем рузльтаты - долгота_широта : результат
                        self.results.update({self.list[self.id][0]['lat']+'_'+self.list[self.id][0]['lon']: res.text})
                        self.list[self.id][1] = 'done'
                        self.id += 1
                if not self.running:
                    break

    def add_task(self, LatLon):
        with self.mutex:
            self.list.append([LatLon, 'wait'])

    def check_status(self, lat, lon):
        with self.mutex:
            # если в списке результатов есть совпадение
            for key in self.results.keys():
                if str(lat)+'_'+str(lon) == key:
                    return self.results[key]
        # иначе дальше ожидаем
        return 'wait'

    def del_ready(self, key):
        del self.results[key]