#!/usr/bin/env python
import rclpy

from rclpy.node import Node

import sys
sys.path.append('/home/robot/colcon_ws/install/tm_msgs/lib/python3.6/site-packages')
from tm_msgs.msg import *
from tm_msgs.srv import *

from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_msgs.msg import Float64MultiArray
import cv2
import numpy as np
from cv_bridge import CvBridge
import math

def regionGrowing(frame):
    regionMap = np.zeros(shape = (frame.shape[0], frame.shape[1]))
    label = 0
    stack = []
    for i in range(frame.shape[0]):
        for j in range(frame.shape[1]):
            if frame[i][j][0]==255 and regionMap[i][j]==0:
                label += 1
                stack.append([i, j])
                regionMap[i][j] = label
                while len(stack)!=0:
                    coordinate = stack.pop(-1)
                    x = coordinate[0]
                    y = coordinate[1]
                    if frame[x][y+1][0]==255 and regionMap[x][y+1]==0:
                        regionMap[x][y+1] = label
                        stack.append([x, y+1])
                    if frame[x][y-1][0]==255 and regionMap[x][y-1]==0:
                        regionMap[x][y-1] = label
                        stack.append([x, y-1])
                    if frame[x+1][y][0]==255 and regionMap[x+1][y]==0:
                        regionMap[x+1][y] = label
                        stack.append([x+1, y])
                    if frame[x-1][y][0]==255 and regionMap[x-1][y]==0:
                        regionMap[x-1][y] = label
                        stack.append([x-1, y])
    return regionMap, label

# class MininalPublisher(Node):
#     def __init__(self):
#         print('init')
#         super().__init__('minimal_publisher')
#         self.publisher_=self.create_publisher(String,'topic', 10)
#         timer_period=0.5
#         self.timer=self.create_timer(timer_period, self.timer_callback)
#         self.i=0

#     def timer_callback(self):
#         print('call_back')
#         msg=String()
#         msg.data = str(angles[0])
#         self.publisher_.publish(msg)
#         self.get_logger().info('Publishing: "%s"' %msg.data)
#         self.i+=1

class ImageSub(Node):
    def __init__(self, nodeName):
        super().__init__(nodeName)
        self.subscription = self.create_subscription(Image,
        'techman_image', self.image_callback, 10)
        self.subscription

    #     self.publisher_=self.create_publisher(String,'topic', 10)
    #     timer_period=0.5
    #     self.timer=self.create_timer(timer_period, self.timer_callback)
    #     self.i=0
    
    # def timer_callback(self):
    #     print('call_back')
    #     msg=Float64MultiArray()
    #     global angles
    #     msg.data = angles
    #     self.publisher_.publish(msg)
    #     self.get_logger().info('Publishing: "%f"' %msg.data[0])
    #     self.i+=1

    def image_callback(self, data):
        self.get_logger().info('Received image')
        #print(data)
        # TODO (write your code here)
        # bridge = CvBridge()
        # data = np.asarray(bridge.imgmsg_to_cv2(data, 'bgr8'))
        regionNum = 0
        WorkImage = np.frombuffer(data.data, dtype=np.uint8).reshape(data.height, data.width, -1)
        # print(type(data))
        # print(data)
        centers = []
        angles = []

        # Preprocessing
        #WorkImage = cv2.GaussianBlur(WorkImage, (3, 3), 0)
        #WorkImage = cv2.threshold(WorkImage, 0, 255, cv2.THRESH_OTSU)
        frame = np.zeros((data.height, data.width, 3))

        for i in range(WorkImage.shape[0]):
            for j in range(WorkImage.shape[1]):
                if WorkImage[i][j][0] >= 130:
                    frame[i][j][:] = 255
                else:
                    frame[i][j][:] = 0

        regionMap, regionNum = regionGrowing(frame)

        # Find centers and angles
        for i in range(regionNum):
            area = 0
            center = [0, 0]
            for r in range(regionMap.shape[0]):
                for c in range(regionMap.shape[1]):
                    if regionMap[r, c] == i+1:
                        area += 1
                        center[0] += r
                        center[1] += c
                    

            if area < 200:
                continue
            center[0] /= area
            center[1] /= area

            cv2.circle(frame, (int(center[1]), int(center[0])), 3, (0, 255, 0),-1)
            print(int(center[0]))
            print(int(center[1]))

            m11 = 0
            m20 = 0
            m02 = 0

            for r in range(regionMap.shape[0]):
                for c in range(regionMap.shape[1]):
                    if regionMap[r, c] == i+1:
                        m11 += (r - center[0]) * (c - center[1])
                        m20 += (r - center[0])**2
                        m02 += (c - center[1])**2
                    
            angle = 0.5*math.atan2(2*m11, m20-m02)
            a = angle
            # if (angle < 0):
            #     a += math.pi
            
            #cv2.circle(frame, (int(center[0]), int(center[1])), 3, (0, 0, 255),-1)
             
            
            centers.append(center)
            angles.append(a)

        print(angles)
        # cv2.imshow('test', frame)
        #cv2.waitKey()
        # targetP1 = "350.00, 350, 730, -180.00, 0.0, 135.00"
        # (960, 1280)
        x = 350+75.0333
        y = 350+75.0333
        z = 730
        A = -180
        B = 0
        C = 135

        x_p = 960
        y_p = 1280
        theta = -0.75 * math.pi

        transform_mat = np.array([
            [-0.732, 0.711, 373.733],
            [-0.697, -0.72, 817.651],
            [0, 0, 1]
        ])
        mm_pixel = 0.5072
        for i in range(len(centers)):
            x_c = (centers[i][0] )  * mm_pixel
            y_c = (centers[i][1] )  * mm_pixel

            loc = np.matmul(transform_mat, np.array([x_c, y_c, 1]))
            loc_str = str(loc[0]) + ", " + str(loc[1]) + ", " + "110, -180.00, 0.0, " + str(angles[i]/math.pi*180+135)
            script = "PTP(\"CPP\","+loc_str+",105,200,0,false)"
            send_script(script)

            set_io(1.0)

            loc_str = "350.00, 350, " + str(i*25+120) + ", -180.00, 0.0, 135.00"
            script = "PTP(\"CPP\","+loc_str+",100,200,0,false)"
            send_script(script)

            set_io(0.0)
            loc_str = "350.00, 350, 400, -180.00, 0.0, 135.00"
            script = "PTP(\"CPP\","+loc_str+",100,200,0,false)"
            send_script(script)





    


def send_script(script):
    arm_node = rclpy.create_node('arm')
    arm_cli = arm_node.create_client(SendScript, 'send_script')

    while not arm_cli.wait_for_service(timeout_sec=1.0):
        arm_node.get_logger().info('service not availabe, waiting again...')

    move_cmd = SendScript.Request()
    move_cmd.script = script
    arm_cli.call_async(move_cmd)
    arm_node.destroy_node()

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

    node = ImageSub('image_sub')
    rclpy.spin(node)
    # print('0')
    # node.destroy_node()

    # print('1')

    # minimal_publisher = MininalPublisher()
    # print('2')
    # rclpy.spin(minimal_publisher)
    # minimal_publisher.destroy_node()
    rclpy.shutdown()

    

if __name__ == '__main__':
    main()
