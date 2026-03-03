# sudo docker run -p 8080:8080 -d -t -v ~/mapproxy:/mapproxy danielsnider/mapproxy

import rclpy
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from geometry_msgs.msg import Twist

import config
from utils import ros2_nodes

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
def cmd_vel(pressed_key: str):
    """Receive velocity command data from a client."""
    if not teleop:
        return
    if not pressed_key in config.COMMAND_VELOCITY.keys():
        return
    msg = Twist()
    msg.linear.x = config.COMMAND_VELOCITY[pressed_key]['linearX']
    msg.angular.z = config.COMMAND_VELOCITY[pressed_key]['angularZ']
    teleop.teleoperate(msg)


def on_nav_result(result: config.TaskResult):
    """Called when Nav2 task is finished."""
    socketio.emit('nav_result', f'{result.name:<9}')


@socketio.event
def navigate(target: str):
    """Receive a navigation target from a client."""
    if not teleop:
        return
    if target == config.NAV_TARGET_STOP:
        teleop.cancel_nav_task()
        socketio.emit('nav_result', 'ABORTED  ')
        return
    if not target in config.NAV_TARGETS.keys():
        socketio.emit('nav_result', 'INVALID  ')
        return
    lat = config.NAV_TARGETS[target]['latitude']
    lon = config.NAV_TARGETS[target]['longitude']
    yaw = config.NAV_TARGETS[target]['yaw']
    teleop.start_nav_task(lat, lon, yaw, on_nav_result)


if __name__ == '__main__':
    rclpy.init()
    teleop = ros2_nodes.TeleopWeb()
    try:
        socketio.run(app, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        teleop.destroy_node()
        rclpy.try_shutdown()
