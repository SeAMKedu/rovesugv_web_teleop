from typing import Callable

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.action import ActionClient
from rclpy.node import Node
from robot_localization.srv import FromLL

from models import GPSWaypoint
from utils.gps_utils import latLonYaw2Geopose


class Navigation(Node):
    """ROS 2 node for GPS navigation."""

    def __init__(self):
        super().__init__(node_name="web_teleop_nav")
        self.is_task_running = False
        self.navigator = BasicNavigator()
        self.srvclient = self.create_client(FromLL, "/fromLL")
        self.action_client = ActionClient(
            node=self,
            action_type=NavigateToPose,
            action_name="navigate_to_pose"
        )
    

    def _check_action_server(self, timeout_sec=5.0) -> bool:
        """Check if the action server is available."""
        return self.action_client.wait_for_server(timeout_sec=timeout_sec)


    def stop(self):
        """Stop the ongoing navigation task."""
        if self.is_task_running:
            self.navigator.cancelTask()
            self.is_task_running = False


    def start(self, gps_waypoints: list[GPSWaypoint], on_result: Callable[[TaskResult], None]):
        """Start a navigation task."""
        is_server_available = self._check_action_server()
        
        if not is_server_available:
            on_result(TaskResult(value=0)) # UNKNOWN
            return

        self.is_task_running = True

        for wp in gps_waypoints:
            if self.is_task_running == False:
                break
            pose = latLonYaw2Geopose(wp.latitude, wp.longitude, wp.yaw)

            request = FromLL.Request()
            request.ll_point.altitude = pose.position.altitude
            request.ll_point.latitude = pose.position.latitude
            request.ll_point.longitude = pose.position.longitude

            future = self.srvclient.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            response: FromLL.Response = future.result()

            goal_pose = PoseStamped()
            goal_pose.header.frame_id = "map"
            goal_pose.header.stamp = self.get_clock().now().to_msg()
            goal_pose.pose.position = response.map_point
            goal_pose.pose.orientation = pose.orientation

            self.navigator.goToPose(goal_pose)

            while not self.navigator.isTaskComplete():
                _ = self.navigator.getFeedback()
                if self.is_task_running == False:
                    break
        
        on_result(self.navigator.getResult())
