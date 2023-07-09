import json
import logging
import os
import tempfile
from argparse import ArgumentParser

import pypandoc
import requests
from pdfminer.high_level import extract_text
from redis import Redis

SERVER_TO_WORKER_GROUP = 'server_to_worker'
SERVER_TO_WORKER_STREAM = 'server_to_worker_stream'
WORKER_TO_SERVER_STREAM = 'worker_to_server_stream'

logger = logging.getLogger('worker-logger')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class Converter:
    @staticmethod
    def _use_pypandoc(file_path):
        _, ext = os.path.splitext(file_path)
        return pypandoc.convert_file(file_path, 'plain', format=ext[1:])

    @staticmethod
    def _use_pdfminer(file_path):
        return extract_text(file_path)

    @staticmethod
    def _use_txt(file_path):
        with open(file_path, 'r') as f:
            return f.read()

    @staticmethod
    def convert(file_path):
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.pdf':
            return Converter._use_pdfminer(file_path)
        if ext.lower() == '.txt':
            return Converter._use_txt(file_path)
        return Converter._use_pypandoc(file_path)


class Worker:
    def __init__(self, redis_host='localhost', redis_port=6379, server_url='http://localhost:65011'):
        self.redis = Redis(redis_host, redis_port)
        self.server_url = server_url.rstrip('/')
        self.__worker_id = hex(abs(hash(os.urandom(8))))

    def send(self, message):
        dump = json.dumps(message)
        self.redis.xadd(WORKER_TO_SERVER_STREAM, {'dump': dump})

    def recv(self):
        received = self.redis.xreadgroup(SERVER_TO_WORKER_GROUP, f'consumer-{self.__worker_id}', {
                                         SERVER_TO_WORKER_STREAM: '>'}, count=1, block=0)
        mid, data = received[0][1][0]
        message = json.loads(data[b'dump'])
        return mid, message

    def ack(self, mid):
        self.redis.xack(SERVER_TO_WORKER_STREAM, SERVER_TO_WORKER_GROUP, mid)

    def disconnect(self):
        self.redis.close()

    def count(self, text, wordlen):
        c = 0
        for word in text.split():
            if len(word.strip()) == wordlen:
                c += 1
        return c

    def process(self, message):
        filename = message['file_name']
        length = message['length']
        res = requests.get(self.server_url + '/file/' + filename, stream=True)
        if res.status_code >= 400:
            # handle all errors as 404
            return {'error': {'code': 404, 'message': 'File not found'}}
        _, ext = os.path.splitext(filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            temp_filename = f.name
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        try:
            res = Converter.convert(temp_filename)
        except Exception as e:
            return {'error': {'code': 400, 'message': str(e)}}
        finally:
            os.remove(temp_filename)
        return {'count': self.count(res, length)}

    def run(self):
        logger.info(f'Worker {self.__worker_id} started')
        while True:
            transmission_id, transmission = self.recv()
            logger.info(f"Received {transmission['task_id']}")
            response = self.process(transmission['message'])
            self.ack(transmission_id)
            self.send(
                {'task_id': transmission['task_id'], 'message': response})
            logger.info(f"Sent {transmission['task_id']}")


def main():
    parser = ArgumentParser(description='Worker for counting words')
    parser.add_argument('--redis-host', type=str, help='Redis host')
    parser.add_argument('--redis-port', type=int, help='Redis port')
    parser.add_argument('--server-url', type=str, help='Server url')
    args = parser.parse_args()

    redis_host = args.redis_host if args.redis_host else os.environ.get(
        'REDIS_HOST', 'localhost')
    redis_port = args.redis_port if args.redis_port else int(
        os.environ.get('REDIS_PORT', '6379'))
    server_url = args.server_url if args.server_url else os.environ.get(
        'SERVER_URL', 'http://localhost:65011')

    worker = Worker(redis_host, redis_port, server_url)
    worker.run()


if __name__ == '__main__':
    main()
