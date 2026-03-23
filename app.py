# sudo docker run -p 8080:8080 -d -t -v ~/mapproxy:/mapproxy danielsnider/mapproxy

import rclpy
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from geometry_msgs.msg import Twist

import config
import models
from utils.teleop import Teleoperation

app = Flask(__name__)
socketio = SocketIO(app)
teleop = None


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


@socketio.event
def on_battery_state(data):
    """Send battery state data to the connected clients."""
    socketio.emit('battery_state', data)


@socketio.event
def on_nav_feedback(data):
    """Send Nav2 feedback data to the connected clients."""
    socketio.emit('nav_feedback', data)


@socketio.event
def on_nav_path(data):
    """Send Nav2 planned path data to the connected clients."""
    socketio.emit('nav_path', data)


@socketio.event
def on_navsatfix(data):
    """Send satellite navigation fix data to the connected clients."""
    socketio.emit('navsatfix', data)


@socketio.event
def drive_robot(data: dict):
    """Receive teleoperation command from a client."""
    print(data)
    if not teleop:
        return
    command = models.DriveCommand(data['env'], data['direction'])
    if not str(command.direction) in config.COMMAND_VELOCITY.keys():
        return
    teleop.teleoperate(command)


def on_nav_result(result: config.TaskResult):
    """Called when Nav2 task is finished."""
    socketio.emit('nav_result', f'{result.name:<9}')


@socketio.event
def nav_start(location: dict):
    """Receive a navigation target from a client."""
    if not teleop:
        return
    lat = location['lat']
    lon = location['lon']
    yaw = location['yaw']
    teleop.start_nav_task(lat, lon, yaw, on_nav_result)


@socketio.event
def nav_cancel():
    if not teleop:
        return
    teleop.cancel_nav_task()
    socketio.emit('nav_result', 'ABORTED')


if __name__ == '__main__':
    rclpy.init()
    teleop = Teleoperation()
    try:
        socketio.run(app, host="0.0.0.0", debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        teleop.destroy_node()
        rclpy.try_shutdown()
