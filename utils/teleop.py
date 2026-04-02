from geometry_msgs.msg import Twist
from rclpy.node import Node


class RoverTeleop(Node):
    """ROS 2 node for teleoperating the mobile robot."""

    def __init__(self, teleop_topic):
        super().__init__(node_name="rover_teleop")
        self.teleop_topic = teleop_topic
        self.teleop_publisher = self.create_publisher(
            msg_type=Twist,
            topic=self.teleop_topic,
            qos_profile=10,
        )


    def teleoperate(self, teleop_command: dict):
        """Teleoperate the mobile robot."""
        msg = Twist()
        msg.linear.x = float(teleop_command.get("linearX", 0.0))
        msg.angular.z = float(teleop_command.get("angularZ", 0.0))
        self.teleop_publisher.publish(msg)
