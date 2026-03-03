from typing import Callable

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from geographic_msgs.msg import GeoPose
from nav_msgs.msg import Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from nav2_simple_commander.robot_navigator import BasicNavigator
from rclpy.node import Node
from robot_localization.srv import FromLL
from sensor_msgs.msg import BatteryState, Imu, NavSatFix

from utils import gps_utils


class DataMonitoring(Node):
    """
    Subscribe to ROS 2 topics and provide messages for a data monitoring app.

    :param cb_batstate: Function to call when battery state message is received.
    :param cb_feedback: Function to call when Nav2 feedback message is received.
    :param cb_imu: Function to call when IMU data message is received.
    :param cb_navsatfix: Function to call when satellite fix message is received.
    :param cb_path: Function to call when path message is received.

    """

    def __init__(
            self,
            cb_batstate: Callable,
            cb_feedback: Callable,
            cb_imu: Callable,
            cb_navsatfix: Callable,
            cb_path: Callable,
        ):
        super().__init__(node_name='data_monitoring')

        self.sub_battery = self.create_subscription(
            msg_type=BatteryState,
            topic='/panther/battery/battery_status',
            callback=cb_batstate,
            qos_profile=10,
        )
        self.sub_feedback = self.create_subscription(
            msg_type=NavigateToPose_FeedbackMessage,
            topic='/navigate_to_pose/_action/feedback',
            callback=cb_feedback,
            qos_profile=10,
        )
        self.sub_imu = self.create_subscription(
            msg_type=Imu,
            topic='/imu',
            callback=cb_imu,
            qos_profile=10,
        )
        self.sub_navsatfix = self.create_subscription(
            msg_type=NavSatFix,
            topic='/gps/fix',
            callback=cb_navsatfix,
            qos_profile=10,
        )
        self.sub_path = self.create_subscription(
            msg_type=Path,
            topic='/plan',
            callback=cb_path,
            qos_profile=10,
        )
        

class TeleopWeb(Node):
    """Teleoperate a robot using a web browser."""

    def __init__(self):
        super().__init__(node_name='teleop_web')
        self.navigator = BasicNavigator()
        self.srvclient = self.create_client(srv_type=FromLL, srv_name='/fromLL')
        self.twist_pub = self.create_publisher(
            msg_type=Twist,
            topic='/cmd_vel',
            qos_profile=10,
        )

    def _get_geopose(self, lat: float, lon: float, yaw: float) -> GeoPose:
        """Get the geographic pose of the given target coordinate."""
        return gps_utils.latLonYaw2Geopose(lat, lon, yaw)


    def cancel_nav_task(self):
        """Cancel a navigation task."""
        self.navigator.cancelTask()


    def start_nav_task(self, lat: float, lon: float, yaw: float, cb_result: Callable):
        """Start a navigation task.

        :param lat: Latitude of the navigation target.
        :param lat: Longitude of the navigation target.
        :param lat: Yaw of the navigation target.
        :param cb_result: Function to call when the navigation task is finished.

        """
        geopose = self._get_geopose(lat, lon, yaw)

        request = FromLL.Request()
        request.ll_point.altitude = geopose.position.altitude
        request.ll_point.latitude = geopose.position.latitude
        request.ll_point.longitude = geopose.position.longitude

        future = self.srvclient.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response: FromLL.Response = future.result()
        
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position = response.map_point
        pose.pose.orientation = geopose.orientation

        self.navigator.goToPose(pose)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if not feedback:
                continue

        cb_result(self.navigator.getResult())


    def teleoperate(self, msg: Twist):
        """Teleoperate a rover.

        :param msg: Twist message.

        """
        self.twist_pub.publish(msg)
