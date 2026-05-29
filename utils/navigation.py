from typing import Callable

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav2_msgs.action._navigate_to_pose import NavigateToPose_Feedback
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.action import ActionClient
from rclpy.node import Node
from robot_localization.srv import FromLL
from std_srvs.srv import Trigger

from models import GPSWaypoint
from utils.gps_utils import latLonYaw2Geopose


class Navigation(Node):
    """
    Navigation node.

    :param on_feedback_msg: Callback function for navigation feedback message.
    :param on_task_result: Callback function for navigation task result.

    """

    def __init__(
            self,
            on_feedback_msg: Callable[[NavigateToPose_Feedback], None],
            on_task_result: Callable[[TaskResult], None]
        ):
        super().__init__(node_name="web_teleop_navigation")

        self.on_feedback_msg = on_feedback_msg
        self.on_task_result = on_task_result

        self.is_active = False
        self.navigator = BasicNavigator()
        self.srvclient = self.create_client(FromLL, "/fromLL")
        self.action_client = ActionClient(
            node=self,
            action_type=NavigateToPose,
            action_name="navigate_to_pose"
        )
    

    def check_state(self):
        """Check if the Navigation 2 stack is active."""
        service_name = "/lifecycle_manager_navigation/is_active"
        client = self.create_client(Trigger, service_name)
        is_ready = client.wait_for_service(timeout_sec=10)
        if not is_ready:
            return False
        request = Trigger.Request()
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response: Trigger.Response = future.result()
        return response.success
    

    def start(self, gps_waypoints: list[GPSWaypoint]):
        """
        Start a navigation task.

        :param gps_waypoints: List of GPS waypoints of the route to be driven.

        """
        self.is_active = True

        for wp in gps_waypoints:
            if self.is_active is False:
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
                feedback = self.navigator.getFeedback()
                self.on_feedback_msg(feedback)
                if self.is_active is False:
                    break
        
        self.on_task_result(self.navigator.getResult())


    def stop(self):
        """Stop the ongoing navigation task."""
        self.navigator.cancelTask()
        self.is_active = False
