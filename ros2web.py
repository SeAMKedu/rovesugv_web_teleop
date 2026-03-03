import math
import sys
from threading import Lock

import geopy.distance
import rclpy
import socketio
import socketio.exceptions
from geometry_msgs.msg import Point, Quaternion
from nav_msgs.msg import Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from sensor_msgs.msg import BatteryState, Imu, NavSatFix

import config
from utils import gps_utils, ros2_nodes

bearing = 0.0
lock = Lock()
sio = socketio.SimpleClient()


def callback_on_battery_state(msg: BatteryState):
    """Called when a battery state message is published."""
    battery_state = {
        'charge': round(msg.charge, 1),
        'percentage': round(100 * msg.percentage, 1),
        'temperature': round(msg.temperature, 1),
    }

    sio.emit('on_battery_state', battery_state)


def callback_on_nav_feedback(msg: NavigateToPose_FeedbackMessage):
    """Called when a Nav2 feedback message is published."""
    # Compute the time in seconds.
    estimated_time_remainging = msg.feedback.estimated_time_remaining.sec + \
        msg.feedback.estimated_time_remaining.nanosec / 1_000_000_000
    navigation_time = msg.feedback.navigation_time.sec + \
        msg.feedback.navigation_time.nanosec / 1_000_000_000
    
    feedback = {
        'estimated_time_remainging': round(estimated_time_remainging),
        'distance_remaining': round(msg.feedback.distance_remaining),
        'navigation_time': round(navigation_time),
        'number_of_recoveries': msg.feedback.number_of_recoveries
    }

    sio.emit('on_nav_feedback', feedback)


def callback_on_imu_data(msg: Imu):
    """Called when an IMU data message is published."""
    global bearing

    q = Quaternion()
    q.x = msg.orientation.x
    q.y = msg.orientation.y
    q.z = msg.orientation.z
    q.w = msg.orientation.w
    
    euler_angles = gps_utils.euler_from_quaternion(q)

    bearing_rad = euler_angles[2]
    bearing_deg = bearing_rad * 180 / math.pi # radians -> degrees
    lock.acquire()
    # Geopy uses notation: 0 = North, 90 = West, 180 = South, -90 = East.
    # IMU uses notation: 90 = North, 180 = West, -90 = South, 0 = East.
    # => bearing_geopy = 90 - bearing_imu
    bearing = 90 - bearing_deg
    lock.release()


def callback_on_navsatfix(msg: NavSatFix):
    """Called when a navigation satellite fix message is published."""
    lock.acquire()
    # Tip of the arrow that shows the orientation of the rover.
    arrow_tip = geopy.distance.distance(meters=10).destination(
        point=(msg.latitude, msg.longitude),
        bearing=bearing,
    )
    lock.release()

    navsatfix = {
        'alt': round(msg.altitude, 9),
        'lat': round(msg.latitude, 9),
        'lon': round(msg.longitude, 9),
        'arrow_tip': {
            'lat': arrow_tip.latitude,
            'lon': arrow_tip.longitude,
        }
    }

    sio.emit('on_navsatfix', navsatfix)


def callback_on_nav_path(msg: Path):
    """Called when a planned Nav2 path message is published."""
    planned_path = []
    for pose in msg.poses:
        # Waypoint on the path.
        wp: Point = pose.pose.position
        # Distance from the origin at (0, 0) to the waypoint.
        distance = math.sqrt(math.pow(wp.x, 2) + math.pow(wp.y, 2))
        # Bearing from the origin at (0, 0) to the waypoint.
        bearing_rad = math.atan2(wp.y, wp.x)
        bearing_deg = bearing_rad * 180 / math.pi
        bearing_geopy = 90 - bearing_deg
        # GPS coordinates of the waypoint.
        wp_location = geopy.distance.distance(meters=distance).destination(
            point=(config.INIT_POINT_LAT, config.INIT_POINT_LON),
            bearing=bearing_geopy,
        )
        # The GPS coordinates are used to form a polyline on the Leaflet map.
        planned_path.append([wp_location.latitude, wp_location.longitude])
    
    sio.emit('on_nav_path', {'path': planned_path})


def main():
    try:
        sio.connect(f'http://{config.SERVER_HOST}:{config.SERVER_PORT}')
    except socketio.exceptions.ConnectionError:
        print('Could not connect to the SocketIO server, exiting...')
        return sys.exit(1)

    rclpy.init()
    
    data_monitoring = ros2_nodes.DataMonitoring(
        cb_batstate=callback_on_battery_state,
        cb_feedback=callback_on_nav_feedback,
        cb_imu=callback_on_imu_data,
        cb_navsatfix=callback_on_navsatfix,
        cb_path=callback_on_nav_path,
    )

    try:
        rclpy.spin(data_monitoring)
    except KeyboardInterrupt:
        pass
    finally:
        sio.disconnect()
        data_monitoring.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
