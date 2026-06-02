from typing import Callable

from nav_msgs.msg import Odometry, Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Image, NavSatFix
from std_msgs.msg import Bool


class Telemetry(Node):
    """Telemetry node for collecting data and sending it to web application."""

    def __init__(
            self,
            battery_status_topic: str,
            battery_status_callback: Callable[[BatteryState], None],
            camera_topic: str,
            camera_callback: Callable[[Image], None],
            e_stop_status_topic: str,
            e_stop_status_callback: Callable[[Bool], None],
            odom_topic: str,
            odom_callback: Callable[[Odometry], None],
            #nav_feedback_topic: str,
            #nav_feedback_callback: Callable[[NavigateToPose_FeedbackMessage], None],
            navsatfix_topic: str,
            navsatfix_callback: Callable[[NavSatFix], None],
            planned_path_topic: str,
            planned_path_callback: Callable[[Path], None],
        ):
        super().__init__(node_name="telemetry", namespace="web_teleop")

        self.battery_status_topic = battery_status_topic
        self.battery_status_callback = battery_status_callback
        self.camera_topic = camera_topic
        self.camera_callback = camera_callback
        self.e_stop_status_topic = e_stop_status_topic
        self.e_stop_status_callback = e_stop_status_callback
        self.odom_topic = odom_topic
        self.odom_callback = odom_callback
        #self.nav_feedback_topic = nav_feedback_topic
        #self.nav_feedback_callback = nav_feedback_callback
        self.navsatfix_topic = navsatfix_topic
        self.navsatfix_callback = navsatfix_callback
        self.planned_path_topic = planned_path_topic
        self.planned_path_callback = planned_path_callback

        if self.battery_status_topic:
            self.battery_state_subscription = self.create_subscription(
                msg_type=BatteryState,
                topic=self.battery_status_topic,
                callback=self.battery_status_callback,
                qos_profile=10,
            )
        self.camera_subscription = self.create_subscription(
            msg_type=Image,
            topic=self.camera_topic,
            callback=self.camera_callback,
            qos_profile=10,
        )
        self.e_stop_status_subscription = self.create_subscription(
            msg_type=Bool,
            topic=self.e_stop_status_topic,
            callback=self.e_stop_status_callback,
            qos_profile=10,
        )
        self.odom_subscription = self.create_subscription(
            msg_type=Odometry,
            topic=self.odom_topic,
            callback=self.odom_callback,
            qos_profile=10,
        )
        # self.nav_feedback_subscription = self.create_subscription(
        #     msg_type=NavigateToPose_FeedbackMessage,
        #     topic=self.nav_feedback_topic,
        #     callback=self.nav_feedback_callback,
        #     qos_profile=10,
        # )
        self.navsatfix_subscription = self.create_subscription(
            msg_type=NavSatFix,
            topic=self.navsatfix_topic,
            callback=self.navsatfix_callback,
            qos_profile=10,
        )
        self.planned_path_subscription = self.create_subscription(
            msg_type=Path,
            topic=self.planned_path_topic,
            callback=self.planned_path_callback,
            qos_profile=10,
        )
