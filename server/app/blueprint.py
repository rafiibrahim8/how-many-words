import hashlib
import os

from flask import Blueprint, render_template, request, send_from_directory

from .communicate import communicator

_error_code_messages = {
    400: 'File format is not supported',
    # File was deleted before the worker could process it
    404: 'Error processing file',
}

app_blueprint = Blueprint('app', __name__)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_blueprint():
    return app_blueprint


@app_blueprint.get('/')
def index():
    return render_template('index.html')


@app_blueprint.post('/')
def count():
    try:
        length = int(request.form.get('length'))
    except (ValueError, TypeError):
        return render_template('result.html', error={'message': 'Length is not provided or not a number'})
    if length < 1:
        return render_template('result.html', error={'message': 'Length must be greater than 0'})
    file = request.files.get('file')
    if file is None:
        return render_template('result.html', error={'message': 'File is not provided'})

    file_id = hashlib.sha256(os.urandom(64)).hexdigest()
    _, ext = os.path.splitext(file.filename)
    file_name = f'{file_id}{ext}'
    file.save(os.path.join(UPLOAD_DIR, file_name))
    message_id = communicator.send({'length': length, 'file_name': file_name})
    response = communicator.recv(message_id)
    os.remove(os.path.join(UPLOAD_DIR, file_name))

    if response is None:
        return render_template('result.html', error={'message': 'Timeout waiting for response from worker'})
    if 'error' in response:
        return render_template('result.html',
                               error={'message': _error_code_messages.get(response['error']['code'], 'Unknown error')})
    return render_template('result.html', result=response, length=length)

# auth is not necessary as the filename is random and
# the file is short-lived


@app_blueprint.get('/file/<file_name>')
def get_file(file_name):
    return send_from_directory(UPLOAD_DIR, file_name)
