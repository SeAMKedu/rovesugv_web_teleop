import rclpy
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from nav2_simple_commander.robot_navigator import TaskResult

import yaml
from config import config
from models import GPSWaypoint
from utils.navigation import Navigation
from utils.teleop import RoverTeleop


app = Flask(__name__)
socketio = SocketIO(app)
is_navigation_active = False


def read_waypoints(route):
    waypoints = []
    with open("waypoints.yaml", "r") as file:
        data: dict = yaml.safe_load(file)
        wps = data.get(route, [])
        for wp in wps:
            waypoint = [wp["latitude"], wp["longitude"], wp["yaw"]]
            waypoints.append(waypoint)
    return waypoints


@app.route("/")
def index():
    """Return the HTML template."""
    language_code = request.args.get("lang", "fi")
    default_template = "lang_fi.html"
    template = "lang_en.html" if language_code == "en" else default_template
    return render_template(template, use_sim=config.use_sim)


@socketio.event
def connect():
    """Called when a client connects to the SocketIO server."""
    message = {"navStatus": is_navigation_active}
    socketio.emit("connection", message)


@socketio.event
def disconnect():
    """Called when the client disconnects from the SocketIO server."""
    pass


@socketio.event
def on_battery_state(data: dict):
    """Send battery state data to the connected clients."""
    socketio.emit("battery_state", data)


@socketio.event
def on_nav_feedback(data: dict):
    """Send Nav2 feedback data to the connected clients."""
    socketio.emit("nav_feedback", data)


@socketio.event
def on_navsatfix(data: dict):
    """Send the location of the mobile robot to the connected clients."""
    socketio.emit("navsatfix", data)


@socketio.event
def on_nav_path(data: dict):
    """Send Nav2 planned path data to the connected clients."""
    socketio.emit("nav_path", data)


@socketio.event
def teleoperate(data: dict):
    """Teleoperate the mobile robot."""
    teleop.teleoperate(data)


def on_navigation_result(result: TaskResult):
    """Send the result of the Nav2 task to the connected clients."""
    global is_navigation_active
    is_navigation_active = False
    socketio.emit("nav_status", is_navigation_active)
    socketio.emit("nav_result", result.name)


@socketio.event
def get_waypoints(route: str):
    waypoints = read_waypoints(route)
    socketio.emit("nav_waypoints", waypoints)


@socketio.event
def start_navigation(data: dict):
    """Receive a new navigation task."""
    global is_navigation_active
    if is_navigation_active:
        return
    is_navigation_active = True
    socketio.emit("nav_status", is_navigation_active)

    goal = data.get("goal")

    waypoints = []
    if goal == "mapPoint": # navigate to map point clicked by the user
        waypoints = [GPSWaypoint(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            yaw=data.get("yaw"),
        )]
    elif goal in ("maptLab", "roboLab"): # navigate to predefined goal pose
        wps = read_waypoints(goal)
        waypoints = [GPSWaypoint(
            latitude=wps[0][0],
            longitude=wps[0][1],
            yaw=wps[0][2]
        )]
    elif goal in ("auto2robo", "robo2auto"): # navigate via predefined route
        wps = read_waypoints(goal)
        for wp in wps:
            waypoint = GPSWaypoint(
                latitude=wp[0],
                longitude=wp[1],
                yaw=wp[2]
            )
            waypoints.append(waypoint)
    else:
        pass
    navigation.start(waypoints, on_navigation_result)


@socketio.event
def stop_navigation():
    """Cancel the navigation task."""
    global is_navigation_active
    is_navigation_active = False
    socketio.emit("nav_status", is_navigation_active)

    navigation.cancel()


if __name__ == "__main__":
    rclpy.init()
    navigation = Navigation()
    teleop = RoverTeleop(config.ros2_topics.teleop)
    socketio.run(app, host="0.0.0.0", debug=True)
    navigation.destroy_node()
    teleop.destroy_node()
    rclpy.try_shutdown()
