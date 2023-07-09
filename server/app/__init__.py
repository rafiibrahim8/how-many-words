from flask import Flask

from .blueprint import get_blueprint as get_app_blueprint
from .communicate import communicator

app = Flask(__name__)
app.register_blueprint(get_app_blueprint())
communicator.initialize()

if __name__ == '__main__':
    app.run(debug=True, port=65011)
