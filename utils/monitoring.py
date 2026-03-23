from typing import Callable

from nav_msgs.msg import Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu, NavSatFix


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
