from typing import Callable

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from geographic_msgs.msg import GeoPose
from nav2_simple_commander.robot_navigator import BasicNavigator
from rclpy.node import Node
from robot_localization.srv import FromLL

import config
import models
from utils import gps_utils


class Teleoperation(Node):
    """Teleoperate a robot using a web browser."""

    def __init__(self):
        super().__init__(node_name='teleop_web')
        
        self.topic_simu = config.EnvSimulation.TELEOPERATION_TOPIC.value
        self.topic_robo = config.EnvRobot.TELEOPERATION_TOPIC.value

        self.navigator = BasicNavigator()
        self.srvclient = self.create_client(srv_type=FromLL, srv_name='/fromLL')
        self.teleop_publisher = self.create_publisher(
            msg_type=Twist,
            topic=self.topic_simu,
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


    def teleoperate(self, command: models.DriveCommand):
        """Drive the rover.

        :param command: Drive command.

        """
        if command.env == config.Environment.SIMULATION.value:
            if not self.teleop_publisher.topic == self.topic_simu:
                self.teleop_publisher.destroy()
                self.teleop_publisher = self.create_publisher(
                    Twist, self.topic_simu, 10)
        elif command.env == config.Environment.ROBOT.value:
            if not self.teleop_publisher.topic == self.topic_robo:
                self.teleop_publisher.destroy()
                self.teleop_publisher = self.create_publisher(
                    Twist, self.topic_robo, 10)
        msg = Twist()
        msg.linear.x = config.COMMAND_VELOCITY[command.direction]['linearX']
        msg.angular.z = config.COMMAND_VELOCITY[command.direction]['angularZ']
        
        self.teleop_publisher.publish(msg)

