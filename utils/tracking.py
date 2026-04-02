from typing import Callable

from nav_msgs.msg import Odometry, Path
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, NavSatFix


class DataTracking(Node):
    """ROS 2 node for data tracking."""

    def __init__(
            self,
            battery_state_topic: str,
            battery_state_callback: Callable[[BatteryState], None],
            odom_topic: str,
            odom_callback: Callable[[Odometry], None],
            nav_feedback_topic: str,
            nav_feedback_callback: Callable[[NavigateToPose_FeedbackMessage], None],
            navsatfix_topic: str,
            navsatfix_callback: Callable[[NavSatFix], None],
            planned_path_topic: str,
            planned_path_callback: Callable[[Path], None],
        ):
        super().__init__(node_name="data_tracking")

        self.battery_state_topic = battery_state_topic
        self.battery_state_callback = battery_state_callback
        self.odom_topic = odom_topic
        self.odom_callback = odom_callback
        self.nav_feedback_topic = nav_feedback_topic
        self.nav_feedback_callback = nav_feedback_callback
        self.navsatfix_topic = navsatfix_topic
        self.navsatfix_callback = navsatfix_callback
        self.planned_path_topic = planned_path_topic
        self.planned_path_callback = planned_path_callback

        if self.battery_state_topic:
            self.battery_state_subscription = self.create_subscription(
                msg_type=BatteryState,
                topic=self.battery_state_topic,
                callback=self.battery_state_callback,
                qos_profile=10,
            )
        self.odom_subscription = self.create_subscription(
            msg_type=Odometry,
            topic=self.odom_topic,
            callback=self.odom_callback,
            qos_profile=10,
        )
        self.nav_feedback_subscription = self.create_subscription(
            msg_type=NavigateToPose_FeedbackMessage,
            topic=self.nav_feedback_topic,
            callback=self.nav_feedback_callback,
            qos_profile=10,
        )
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
