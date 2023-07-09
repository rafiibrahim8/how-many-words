import hashlib
import json
import os
import time
from threading import Thread

from redis import Redis


class Communicator:
    _SERVER_TO_WORKER_GROUP = 'server_to_worker'
    _SERVER_TO_WORKER_STREAM = 'server_to_worker_stream'
    _WORKER_TO_SERVER_GROUP = 'worker_to_server'
    _WORKER_TO_SERVER_STREAM = 'worker_to_server_stream'

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        self.redis_password = os.environ.get('REDIS_PASSWORD')
        self.redis = None
        self.recv_dict = {}
        self.__will_recv = True
        self.__is_initialized = False
        self.initialize()

    
    def initialize(self):
        if self.__is_initialized:
            return
        self.redis = Redis(self.redis_host, self.redis_port, password=self.redis_password)
        self.__create_group(self._SERVER_TO_WORKER_GROUP, self._SERVER_TO_WORKER_STREAM)
        self.__create_group(self._WORKER_TO_SERVER_GROUP, self._WORKER_TO_SERVER_STREAM)
        recv_thread = Thread(target=self.__recv_loop)
        recv_thread.daemon = True
        recv_thread.start()
        self.__is_initialized = True
        
    def disconnect(self):
        self.redis.close()
        self.__will_recv = False

    def __create_group(self, group_name, stream_name):
        try:
            return self.redis.xgroup_create(stream_name, group_name, mkstream=True)
        except Exception as e:
            if 'already exists' not in str(e).lower():
                raise e
        
    def send(self, message):
        task_id = hashlib.sha256(os.urandom(64)).hexdigest()
        dump = json.dumps({'task_id': task_id, 'message': message})
        self.redis.xadd(self._SERVER_TO_WORKER_STREAM, {'dump': dump})
        return task_id

    def recv(self, task_id, timeout=10):
        ends = time.time() + timeout
        while task_id not in self.recv_dict and time.time() < ends:
            time.sleep(0.05)
        if task_id in self.recv_dict:
            return self.recv_dict.pop(task_id)
    
    def __recv_loop(self):
        while self.__will_recv:
            transmission = self.redis.xreadgroup(self._WORKER_TO_SERVER_GROUP, "consumer" , {self._WORKER_TO_SERVER_STREAM: ">"}, count=1, block=0)
            transmission_id, transmission = transmission[0][1][0]
            data = json.loads(transmission[b'dump'])
            self.recv_dict[data['task_id']] = data['message']
            self.redis.xack(self._WORKER_TO_SERVER_STREAM, self._WORKER_TO_SERVER_GROUP, transmission_id)

communicator = Communicator()
