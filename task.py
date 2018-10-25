from threading import Thread, Lock
from random import randrange
from time import sleep

from requests import post

class TaskSystem:
    def __init__(self):
        self.list = []
        self.id = 0
        self.mutex = Lock()
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
                    self.list[self.id][1] -= 1
                    # если статус этого запроса ждет
                    if self.list[self.id][1] == 'wait':
                        # посылаем запрос
                        post('http://127.0.0.1:5001/', data=self.list[self.id][0])
                        self.list[self.id][2] = 'done'
                        self.id += 1
                if not self.running:
                    break

    def add_task(self, LatLon):
        with self.mutex:
            self.list.append([LatLon, 'wait'])

    def get_list(self):
        result = []
        with self.mutex:
            for name, cnt, status in self.list:
                result.append({'name': name, 'status': status, 'counter': cnt})
        return result