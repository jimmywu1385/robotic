#!/usr/bin/env python

import rclpy
from rclpy.node import Node

import sys
sys.path.append('/home/robot/colcon_ws/install/tm_msgs/lib/python3.6/site-packages')
import cv2
from tm_msgs.msg import *
from tm_msgs.srv import *
from std_msgs.msg import String
# from std_msgs.msg import Float64MultiArray

# class MinimalSubscriber(Node):
#     def __init__(self):
#         super().__init__('minimal_subscriber')
#         self.subscription = self.create_subscription(Float64MultiArray, 'topic', self.listener_callback, 10)
#         self.subscription

#     def listener_callback(self, msg):
#         self.get_logger().info('I hear: "%s"' %msg.data)


# arm client
def send_script(script):
    arm_node = rclpy.create_node('arm')
    arm_cli = arm_node.create_client(SendScript, 'send_script')

    while not arm_cli.wait_for_service(timeout_sec=1.0):
        arm_node.get_logger().info('service not availabe, waiting again...')

    move_cmd = SendScript.Request()
    move_cmd.script = script
    arm_cli.call_async(move_cmd)
    arm_node.destroy_node()

# gripper client
def set_io(state):
    gripper_node = rclpy.create_node('gripper')
    gripper_cli = gripper_node.create_client(SetIO, 'set_io')

    while not gripper_cli.wait_for_service(timeout_sec=1.0):
        node.get_logger().info('service not availabe, waiting again...')

    io_cmd = SetIO.Request()
    io_cmd.module = 1
    io_cmd.type = 1
    io_cmd.pin = 0
    io_cmd.state = state
    gripper_cli.call_async(io_cmd)
    gripper_node.destroy_node()

def main(args=None):

    rclpy.init(args=args)
    set_io(0.0)

    #--- move command by joint angle ---#
    # script = 'PTP(\"JPP\",45,0,90,0,90,0,35,200,0,false)'
    # send_script(script)

    #--- move command by end effector's pose (x,y,z,a,b,c) ---#
    # targetP1 = "398.97, -122.27, 748.26, -179.62, 0.25, 90.12"
    
    # Initial camera position for taking image (Please do not change the values)
    targetP3 = "350.00, 350, 730, -180.00, 0.0, 135.00"
    # targetP2 = "380.00, 200, 130, -180.00, 0.0, 135.00"
    # targetP1 = "350.00, 350, 130, -180.00, 0.0, 135.00"
    # script1 = "PTP(\"CPP\","+targetP1+",100,200,0,false)"
    # script2 = "PTP(\"CPP\","+targetP2+",100,200,0,false)"
    script3 = "PTP(\"CPP\","+targetP3+",100,200,0,false)"
    # send_script(script1)
    # send_script(script2)
    send_script(script3)

# What does Vision_DoJob do? Try to use it...
# -------------------------------------------------
    # send_script("Vision_DoJob(job1)")
    # cv2.waitKey(1)
    send_script("Vision_DoJob(job1)")
    cv2.waitKey(1)
#--------------------------------------------------

    set_io(0.0) # 1.0: close gripper, 0.0: open gripper

    # minimal_subscriber = MinimalSubscriber()
    # rclpy.spin(minimal_subscriber)
    # minimal_subscriber.destroy_node()

    rclpy.shutdown()

if __name__ == '__main__':
    main()
