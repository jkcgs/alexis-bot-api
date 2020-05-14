from flask import Flask, jsonify
from services import sismos, covid19cl, booru, discord_meme

app = Flask(__name__)
app.register_blueprint(sismos.view)
app.register_blueprint(covid19cl.view)
app.register_blueprint(booru.view)
app.register_blueprint(discord_meme.view)


@app.route('/')
def hello_world():
    return jsonify({'message': 'Hello World!'})


if __name__ == '__main__':
    app.run()
