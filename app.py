# TODO
# Pantherin nollapisteen määritys
# ros2 service call /toLL robot_localization/srv/ToLL
#
# Hätäseis-toiminto
# ros2 service call /panther/hardware/e_stop_trigger std_srvs/srv/Trigger
# ros2 service call /panther/hardware/e_stop_reset std_srvs/srv/Trigger
import dataclasses
import os
import pathlib

import rclpy
import yaml
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from nav2_msgs.action._navigate_to_pose import NavigateToPose_Feedback
from nav2_simple_commander.robot_navigator import TaskResult

import models
from cfgreader import config
from utils.estop import EmergencyStop
from utils.navigation import Navigation
from utils.teleoperation import Teleoperation

INIT_ROVER_LATITUDE = 62.789252
INIT_ROVER_LONGITUDE = 22.821627


app = Flask(__name__)
socketio = SocketIO(app)

app_data = models.AppData(
    estop=models.EStop(),
    navigation=models.NavigationData(
        goal_pose=models.Pose(),
        start_location=models.Location(),
    ),
    rover=models.Location(
        latitude=INIT_ROVER_LATITUDE,
        longitude=INIT_ROVER_LONGITUDE,
    ),
)


def read_waypoints(route):
    """Read GPS waypoints from the YAML file."""
    cwd = pathlib.Path(__file__).parent
    filepath = os.path.join(cwd, "config", "waypoints.yaml")
    waypoints = []
    with open(filepath, "r") as file:
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
        is_estop_triggered=app_data.estop.is_triggered,
    )


#-----------------------------------------------------------------------------
# SocketIO: Connection
#-----------------------------------------------------------------------------
@socketio.event
def connect():
    """Called when a client connects to the SocketIO server."""
    socketio.emit("connection", dataclasses.asdict(app_data))


@socketio.event
def disconnect():
    """Called when the client disconnects from the SocketIO server."""
    print("[INFO] Client has disconnected")


#-----------------------------------------------------------------------------
# Alerts
#-----------------------------------------------------------------------------
def send_alert(alert_type: str, alert_message: str):
    """Send an alert message to client(s)."""
    socketio.emit("alert", {"type": alert_type, "message": alert_message})


#-----------------------------------------------------------------------------
# Emergency Stop
#-----------------------------------------------------------------------------
@socketio.event
def e_stop(message: str):
    """Receive an emenrgency stop message from a client."""
    if config.use_sim: # there is no e-stop in simulation
        return
    if message == "trigger":
        estop.trigger()
        app_data.estop.is_triggered = True
    elif message == "reset":
        estop.reset()
        app_data.estop.is_triggered = False


#-----------------------------------------------------------------------------
# Telemetry: Callback Functions
#-----------------------------------------------------------------------------
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
    app_data.rover.latitude = data.get("latitude", 0.0)
    app_data.rover.longitude = data.get("longitude", 0.0)
    socketio.emit("navsatfix", data)


@socketio.event
def on_nav_path(data: dict):
    """Send Nav2 planned path data to the connected clients."""
    socketio.emit("nav_path", data)


@socketio.event
def teleoperate(data: dict):
    """Teleoperate the mobile robot."""
    teleop.teleoperate(data)


#-----------------------------------------------------------------------------
# Navigation
#-----------------------------------------------------------------------------
def on_navigation_feedback_msg(msg: NavigateToPose_Feedback):
    """Callback function for navigation feedback message."""
    # Compute times in seconds.
    estimated_time_remaining = msg.estimated_time_remaining.sec + \
        msg.estimated_time_remaining.nanosec / 1_000_000_000
    navigation_time = msg.navigation_time.sec + \
        msg.navigation_time.nanosec / 1_000_000_000

    feedback = {
        "distance_remaining": round(msg.distance_remaining, 1),
        "estimated_time_remaining": round(estimated_time_remaining, 1),
        "navigation_time": round(navigation_time, 1),
        "number_of_recoveries": msg.number_of_recoveries,
    }

    socketio.emit("nav_feedback", feedback)


def on_navigation_result(result: TaskResult):
    """Send the result of the Nav2 task to the connected clients."""
    app_data.navigation.is_running = False
    app_data.navigation.reset_goal()

    socketio.emit("nav_result", {"result": result.name})
    
    alert_message = f"Navigation task result: {result.name}"
    if result.name == TaskResult.SUCCEEDED.name:
        send_alert(models.AlertType.SUCCESS, alert_message)
    elif result.name == TaskResult.CANCELED.name:
        send_alert(models.AlertType.WARNING, alert_message)
    elif result.name == TaskResult.FAILED.name:
        send_alert(models.AlertType.DANGER, alert_message)


@socketio.event
def get_waypoints(route: str):
    """Send GPS waypoints to the client."""
    waypoints = read_waypoints(route)
    socketio.emit("nav_waypoints", {"waypoints": waypoints})


@socketio.event
def on_nav2_state(is_active: bool):
    print("on_nav2_state()", is_active)
    app_data.navigation.is_nav2_active = is_active
    socketio.emit("nav2_state", {"is_active": is_active})


@socketio.event
def navigation_task(message: dict):
    """Receive and run a navigation task sent by client."""
    print(f"[INFO] New navigation task: {message}")

    task = message.get("task", "")

    if task == "start":
        if app_data.navigation.is_running:
            send_alert(models.AlertType.DANGER, "Navigation is already running")
            return
        # Check if the action server is running.
        if not navigation.action_client.wait_for_server(timeout_sec=10.0):
            on_navigation_result(TaskResult(value=3)) # 3 = FAILED
            return

        nav_goal = message.get("goal", {})

        app_data.navigation.is_running = True
        app_data.navigation.update_goal(nav_goal)

        waypoints = []
        # Navigate to a map point clicked by the user
        if app_data.navigation.goal == "mapPoint":
            waypoints = [models.GPSWaypoint(
                latitude=app_data.navigation.goal_pose.latitude,
                longitude=app_data.navigation.goal_pose.longitude,
                yaw=app_data.navigation.goal_pose.yaw,
            )]
        # Navigate to a predefined goal pose.
        elif app_data.navigation.goal in ("maptLab", "roboLab"):
            goal_pose = read_waypoints(app_data.navigation.goal)[0]
            waypoints = [models.GPSWaypoint(
                latitude=goal_pose[0], 
                longitude=goal_pose[1], 
                yaw=goal_pose[2])
            ]
        # Navigate via a predefined route.
        elif app_data.navigation.goal in ("auto2robo", "robo2auto"):
            wps = read_waypoints(app_data.navigation.goal)
            for wp in wps:
                waypoint = models.GPSWaypoint(wp[0], wp[1], wp[2])
                waypoints.append(waypoint)
        # Invalid goal.
        else:
            on_navigation_result(TaskResult(value=3)) # FAILED
            return
        navigation.start(waypoints)

    elif task == "stop":
        navigation.stop()
    
    else:
        on_navigation_result(TaskResult(value=3))


if __name__ == "__main__":
    rclpy.init()
    if not config.use_sim:
        estop = EmergencyStop()
    navigation = Navigation(on_navigation_feedback_msg, on_navigation_result)
    app_data.navigation.is_nav2_active = navigation.check_state()
    teleop = Teleoperation(config.ros2_topics.teleop)
    socketio.run(app, host="0.0.0.0", debug=True)
    if not config.use_sim:
        estop.destroy_node()
    navigation.destroy_node()
    teleop.destroy_node()
    rclpy.try_shutdown()
