import rclpy
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from nav2_simple_commander.robot_navigator import TaskResult

from config import cfg
from models import GPSWaypoint
from utils.navigation import Navigation
from utils.teleop import RoverTeleop

app = Flask(__name__)
socketio = SocketIO(app)
env = cfg["env"]


@app.route("/")
def index():
    """Return the HTML template."""
    language_code = request.args.get("lang", "fi")
    default_template = "lang_fi.html"
    template = "lang_en.html" if language_code == "en" else default_template
    return render_template(template, env=env)


@socketio.event
def connect():
    """Called when a client connects to the SocketIO server."""
    socketio.emit("connection", "connected")


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
    socketio.emit("nav_result", result.name)


@socketio.event
def start_navigation(data: dict):
    """Receive a new navigation task."""
    goal = data.get("goal")
    map_click = data.get("mapClick")
    route = data.get("route")

    waypoints = []
    if goal: # navigate to predefined goal pose
        goal_pose = cfg["waypoints"]["goals"][goal]
        waypoints = [GPSWaypoint(
            latitude=goal_pose["latitude"],
            longitude=goal_pose["longitude"],
            yaw=goal_pose["yaw"]
        )]
    elif map_click: # navigate to map point clicked by the user
        waypoints = [GPSWaypoint(
            latitude=map_click["latitude"],
            longitude=map_click["longitude"],
            yaw=0.0
        )]
    elif data["route"]: # navigate via predefined route
        route_poses = cfg["waypoints"]["routes"][route]
        for pose in route_poses:
            waypoint = GPSWaypoint(
                latitude=pose["latitude"],
                longitude=pose["longitude"],
                yaw=pose["yaw"]
            )
            waypoints.append(waypoint)
    navigation.start(waypoints, on_navigation_result)


@socketio.event
def stop_navigation():
    """Cancel the navigation task."""
    navigation.cancel()


if __name__ == "__main__":
    rclpy.init()
    navigation = Navigation()
    teleop = RoverTeleop(cfg["topic"]["teleop"][env])
    socketio.run(app, host="0.0.0.0", debug=True)
    navigation.destroy_node()
    teleop.destroy_node()
    rclpy.try_shutdown()
