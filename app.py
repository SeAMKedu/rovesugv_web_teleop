# TODO
# Pantherin nollapisteen määritys
# ros2 service call /toLL robot_localization/srv/ToLL
#
# Hätäseis-toiminto
# ros2 service call /panther/hardware/e_stop_trigger std_srvs/srv/Trigger
# ros2 service call /panther/hardware/e_stop_reset std_srvs/srv/Trigger
import rclpy
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from nav2_simple_commander.robot_navigator import TaskResult

import yaml
from config import config
from models import GPSWaypoint
from utils.estop import EmergencyStop
from utils.navigation import Navigation
from utils.teleoperation import Teleoperation


app = Flask(__name__)
socketio = SocketIO(app)
is_estop_triggered = False
is_navigation_active = False
nav_data = {}


def read_waypoints(route):
    """Read GPS waypoints from the YAML file."""
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
    return render_template(
        template, 
        use_sim=config.use_sim,
        is_estop_triggered=is_estop_triggered,
    )


@socketio.event
def connect():
    """Called when a client connects to the SocketIO server."""
    message = {
        "isNavActive": is_navigation_active,
        "navData": nav_data
    }
    socketio.emit("connection", message)


@socketio.event
def disconnect():
    """Called when the client disconnects from the SocketIO server."""
    print("[INFO] Client has disconnected")


@socketio.event
def e_stop(message: str):
    global is_estop_triggered
    if config.use_sim: # there is no e-stop in simulation
        return
    if message == "trigger":
        estop.trigger()
        is_estop_triggered = True
    elif message == "reset":
        estop.reset()
        is_estop_triggered = False


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
    global is_navigation_active, nav_data
    is_navigation_active = False
    nav_data = {}
    socketio.emit("nav_active", is_navigation_active)
    socketio.emit("nav_result", result.name)
    if result.name == "SUCCEEDED":
        socketio.emit("alert", {"type": "success", "msg": "Goal succeeded"})
    elif result.name == "CANCELED":
        socketio.emit("alert", {"type": "warning", "msg": "Goal canceled"})
    elif result.name == "FAILED":
        socketio.emit("alert", {"type": "danger", "msg": "Goal failed"})


@socketio.event
def get_waypoints(route: str):
    waypoints = read_waypoints(route)
    socketio.emit("nav_waypoints", waypoints)


@socketio.event
def start_navigation(data: dict):
    """Receive a new navigation task."""
    global is_navigation_active, nav_data
    if is_navigation_active:
        return
    is_navigation_active = True
    socketio.emit("nav_active", is_navigation_active)

    nav_data = data
    goal = data.get("goal")

    waypoints = []
    if goal == "mapPoint": # navigate to map point clicked by the user
        waypoints = [GPSWaypoint(
            latitude=data.get("goalLat"),
            longitude=data.get("goalLon"),
            yaw=data.get("goalYaw"),
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
        print("[ERROR] Invalid goal")
        on_navigation_result(TaskResult(value=3)) # FAILED
        return
    navigation.start(waypoints, on_navigation_result)


@socketio.event
def stop_navigation():
    """Cancel the navigation task."""
    navigation.stop()


if __name__ == "__main__":
    rclpy.init()
    if not config.use_sim:
        estop = EmergencyStop()
    navigation = Navigation()
    #navigation.navigator.waitUntilNav2Active(localizer="controller_server")
    teleop = Teleoperation(config.ros2_topics.teleop)
    socketio.run(app, host="0.0.0.0", debug=True)
    if not config.use_sim:
        estop.destroy_node()
    navigation.destroy_node()
    teleop.destroy_node()
    rclpy.try_shutdown()
