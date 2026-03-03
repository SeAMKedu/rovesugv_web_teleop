from flask import Flask, render_template, request
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    language_code = request.args.get('lang', 'fi')
    if language_code == 'fi':
        return render_template('lang_fi.html')
    return render_template('lang_en.html')


@socketio.event
def connect():
    socketio.emit('connection', 'connected')


@socketio.event
def disconnect():
    pass


if __name__ == '__main__':
    socketio.run(app, debug=True)
