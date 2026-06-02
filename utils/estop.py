# TODO: call service
# ros2 service call /panther/hardware/e_stop_trigger std_srvs/srv/Trigger
# ros2 service call /panther/hardware/e_stop_reset std_srvs/srv/Trigger

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

from cfgreader import config


class EmergencyStop(Node):
    """ROS 2 node for triggering and reseting the emergency stop."""

    def __init__(self):
        super().__init__(node_name="web_teleop_estop")
        self.client_trigger = self.create_client(
            srv_type=Trigger, 
            srv_name=config.services.e_stop_trigger
        )
        self.client_reset = self.create_client(
            srv_type=Trigger, 
            srv_name=config.services.e_stop_reset
        )


    def trigger(self):
        """Call service to trigger emergency stop."""

        request = Trigger.Request()
        future = self.client_trigger.call_async(request)
        try:
            print("[INFO] Sending E-Stop trigger request")
            rclpy.spin_until_future_complete(self, future)
            response: Trigger.Response = future.result()
            print(f"[INFO] E-Stop trigger response: {response}")
        except RuntimeError as error:
            print(f"[ERROR] {error}")


    def reset(self):
        """Call service to reset emergency stop."""

        request = Trigger.Request()
        future = self.client_reset.call_async(request)
        try:
            print("[INFO] Sending E-Stop trigger request")
            rclpy.spin_until_future_complete(self, future)
            response: Trigger.Response = future.result()
            print(f"[INFO] E-Stop trigger response: {response}")
        except RuntimeError as error:
            print(f"[ERROR] {error}")
