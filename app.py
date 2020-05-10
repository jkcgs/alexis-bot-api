from flask import Flask
from services import sismos

app = Flask(__name__)
app.register_blueprint(sismos.sismos_view)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
