import math
import sys
from threading import Lock
from typing import Sequence

import geopy.distance
import rclpy
import socketio
import socketio.exceptions
from geometry_msgs.msg import PoseStamped, Quaternion
from nav_msgs.msg import Odometry, Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from sensor_msgs.msg import BatteryState, NavSatFix

from config import config
from utils.gps_utils import euler_from_quaternion
from utils.tracking import DataTracking


bearing = 0.0
lock = Lock()
sio = socketio.SimpleClient()


def battery_state_callback(msg: BatteryState):
    """Called when a battery state message is published."""
    data = {
        "capacity": round(msg.design_capacity, 1),
        "charge": round(msg.charge, 1),
        "percentage": round(100 * msg.percentage, 1),
        "temperature": round(msg.temperature, 1),
    }
    sio.emit("on_battery_state", data)


def odom_callback(msg: Odometry):
    """Called when an odometry data message is published."""
    global bearing
    
    q = Quaternion()
    q.x = msg.pose.pose.orientation.x
    q.y = msg.pose.pose.orientation.y
    q.z = msg.pose.pose.orientation.z
    q.w = msg.pose.pose.orientation.w
    
    euler_angles = euler_from_quaternion(q)

    bearing_radians = euler_angles[2]
    bearing_degrees = bearing_radians * 180 / math.pi
    lock.acquire()
    # Geopy uses notation: 0 = North, 90 = West, 180 = South, -90 = East.
    # IMU uses notation: 90 = North, 180 = West, -90 = South, 0 = East.
    # => bearing_geopy = 90 - bearing_imu
    bearing = 90 - bearing_degrees
    lock.release()


def nav_feedback_callback(msg: NavigateToPose_FeedbackMessage):
    """Called when a Nav2 feedback message is published."""
    # Compute the time in seconds.
    estimated_time_remainging = msg.feedback.estimated_time_remaining.sec + \
        msg.feedback.estimated_time_remaining.nanosec / 1_000_000_000
    navigation_time = msg.feedback.navigation_time.sec + \
        msg.feedback.navigation_time.nanosec / 1_000_000_000
    
    feedback = {
        "estimated_time_remainging": round(estimated_time_remainging, 1),
        "distance_remaining": round(msg.feedback.distance_remaining, 1),
        "navigation_time": round(navigation_time, 1),
        "number_of_recoveries": msg.feedback.number_of_recoveries
    }
    sio.emit("on_nav_feedback", feedback)


def navsatfix_callback(msg: NavSatFix):
    """Called when a navigation satellite fix message is published."""
    lock.acquire()
    # Tip of the arrow that shows the orientation of the rover.
    arrow_head = geopy.distance.distance(meters=10).destination(
        point=(msg.latitude, msg.longitude),
        bearing=bearing,
    )
    lock.release()

    data = {
        "alt": round(msg.altitude, 9),
        "lat": round(msg.latitude, 9),
        "lon": round(msg.longitude, 9),
        "arrowhead": {
            "lat": arrow_head.latitude,
            "lon": arrow_head.longitude,
        }
    }
    sio.emit("on_navsatfix", data)


def planned_path_callback(msg: Path):
    """Called when a planned Nav2 path message is published."""
    start_point_lat = config.start_point.latitude
    start_point_lon = config.start_point.longitude
    data = []
    poses: Sequence[PoseStamped] = msg.poses

    for pose in poses:
        # Waypoint on the path.
        wp = pose.pose.position
        # Distance from the origin at (0, 0) to the waypoint.
        distance = math.sqrt(math.pow(wp.x, 2) + math.pow(wp.y, 2))
        # Bearing from the origin at (0, 0) to the waypoint.
        bearing_radians = math.atan2(wp.y, wp.x)
        bearing_degrees = bearing_radians * 180 / math.pi
        bearing_geopy = 90 - bearing_degrees
        # GPS coordinates of the waypoint.
        waypoint = geopy.distance.distance(meters=distance).destination(
            point=(start_point_lat, start_point_lon),
            bearing=bearing_geopy,
        )
        # The GPS coordinates are used to form a polyline on the Leaflet map.
        data.append([waypoint.latitude, waypoint.longitude])
    
    sio.emit("on_nav_path", {"path": data})


def main():
    try:
        sio.connect(url=f"http://{config.app.host}:{config.app.port}")
    except socketio.exceptions.ConnectionError:
        print("Could not connect to the SocketIO server, exiting...")
        return sys.exit(1)
    
    rclpy.init()
    
    tracking = DataTracking(
        battery_state_topic=config.ros2_topics.battery,
        battery_state_callback=battery_state_callback,
        odom_topic=config.ros2_topics.odom,
        odom_callback=odom_callback,
        nav_feedback_topic=config.ros2_topics.nav_feedback,
        nav_feedback_callback=nav_feedback_callback,
        navsatfix_topic=config.ros2_topics.navsatfix,
        navsatfix_callback=navsatfix_callback,
        planned_path_topic=config.ros2_topics.planned_path,
        planned_path_callback=planned_path_callback,
    )
    
    try:
        print("Running data tracking node...")
        rclpy.spin(tracking)
    except KeyboardInterrupt:
        print("\nStopping data tracking node...")
    finally:
        sio.disconnect()
        tracking.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
