#!/usr/bin/env python
import rclpy

from rclpy.node import Node

import sys
sys.path.append('/home/robot/colcon_ws/install/tm_msgs/lib/python3.6/site-packages')
sys.path.append('/home/robotics/.pyenv/versions/team12_new2/lib/python2.7/site-packages')
from tm_msgs.msg import *
from tm_msgs.srv import *

from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_msgs.msg import Float64MultiArray
import cv2
import numpy as np
from cv_bridge import CvBridge
import math

import boto3
import time
import pyimgur
# import imgurpython

def getCenter(WorkImage, target):
    WorkImage = cv2.cvtColor(WorkImage, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(WorkImage, (11, 11),
                        cv2.BORDER_DEFAULT)
    ret, thresh = cv2.threshold(blur, 50, 255,
                            cv2.THRESH_BINARY_INV)

    thresh, contours, hierarchies = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    obj_label = ['fish', 'dog', 'plant']
    obj = dict()
    idx = 0
    centers = []
    for i in contours:
        M = cv2.moments(i)
        (x, y), (width, height), angle = cv2.minAreaRect(i)
        if M['m00'] > 1e4 and M['m00'] < 2e5:
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cv2.circle(WorkImage, (cx, cy), 7, (255, 0, 0), -1)

            obj[idx] = int(width * height)
            idx += 1
            centers.append((cx, cy))

    sorted_obj = dict(sorted(obj.items(), key=lambda item: item[1]))
    obj_idx = list(sorted_obj.keys())

    # for i in range(3):
    #     cv2.putText(WorkImage, obj_label[i], centers[obj_idx[i]], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA)

    # cv2.imshow('test', WorkImage)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    if  target == 'plant':
        return centers[obj_idx[0]][0], centers[obj_idx[0]][1]
    elif target == 'fish':
        return centers[obj_idx[1]][0], centers[obj_idx[1]][1]
    elif target == 'dog' or target == 'cat':
        return centers[obj_idx[2]][0], centers[obj_idx[2]][1]
    else:
        print('Wrong pet')
        return 0, 0

class ImageSub(Node):
    def __init__(self, nodeName):
        super().__init__(nodeName)
        self.subscription = self.create_subscription(Image,
        'techman_image', self.image_callback, 10)
        self.subscription


    def image_callback(self, data):

        self.get_logger().info('Received image')
        # global WorkImage
        WorkImage = np.frombuffer(data.data, dtype=np.uint8).reshape(data.height, data.width, -1)
        cv2.imwrite('done.jpg', WorkImage)


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


        targetP1 = "350.00, 350, 730, -180.00, 0.0, 135.00"
        script = "PTP(\"CPP\","+targetP1+",10,200,0,false)"
        send_script(script)

        # script = "PTP(\"CPP\",150.00, 450, 400, -180.00, 0.0, 135.00, 10, 200, 0, false)"
        # send_script(script)

        # script = "PTP(\"CPP\",500.00, 350, 300, -180.00, 0.0, 135.00, 105, 200, 0, false)"
        # send_script(script)
        # set_io(1.0)
        # script = "PTP(\"CPP\",350.00, 350, 310, -180.00, 0.0, 135.00,105,200,0,false)"
        # script = "PTP(\"CPP\"," + str(loc[0]) + ', ' + str(loc[1]) + ", 310, -180.00, 0.0, 135.00,105,200,0,false)"
        # send_script(script)
        # script = "PTP(\"CPP\",350.00, 350, 310, -225.00, 0.0, 135.00,105,200,0,false)"
        # script = "PTP(\"CPP\"," + str(loc[0]) + ', ' + str(loc[1]) + ", 310, -225.00, 0.0, 135.00,105,200,0,false)"
        # send_script(script)

        global isReceive
        global takepic
        takepic = False
        print('isReceive='+str(isReceive))

        # Upload image to Imgur
        CLIENT_ID = "c7f578c012a742e"
        queue_url_1="https://sqs.ap-northeast-1.amazonaws.com/739183738838/TestQueue.fifo"
        # PATH = "test_img.jpg" #A Filepath to an image on your computer"
        # title = "Uploaded with PyImgur"

        im = pyimgur.Imgur(CLIENT_ID)
        

        while True:
            if takepic == True:

                cv2.imwrite('done.jpg', WorkImage)
                PATH="done.jpg"
                title = "Uploaded with PyImgur"
                uploaded_image = im.upload_image(PATH, title=title)


                # Send message to SQS queue
                response = sqs.send_message(
                    QueueUrl=queue_url_1,
                    MessageBody=str(uploaded_image.link),
                    # MessageDeduplicationId='2',
                    MessageGroupId='1'
                )
                takepic = False

            while isReceive == False:
                response = sqs.receive_message(
                    QueueUrl=queue_url,
                    AttributeNames=[
                        'All',
                    ],
                    MaxNumberOfMessages=1,
                    MessageAttributeNames=[
                        'All',
                    ],
                    # VisibilityTimeout=30,
                    WaitTimeSeconds=10,
                )

                if ('Messages' in response) == False:
                    print('No messages!!')
                else:
                    message = response['Messages'][0]
                    receipt_handle = message['ReceiptHandle']

                    print('Received message: {}'.format(message['Body']))
                    if ('MessageAttributes' in message) == False:
                        print('No attributes')
                        # Delete received message from queue
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=receipt_handle
                        )
                        continue
                    else:
                        for attr in message['MessageAttributes']:
                            print('Attribute {attr_name}: {attr_value}'.format(attr_name=attr, attr_value=message['MessageAttributes'][attr]['StringValue']))
                    
                    global pet
                    global task
                    pet = message['MessageAttributes']['pet']['StringValue']
                    task = message['MessageAttributes']['task']['StringValue']

                    # Delete received message from queue
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=receipt_handle
                    )
                    
                    # global isReceive
                    isReceive = True
                    
                    print('-----------------------------------------------')
                    print('**Message has been Deleted**')

                    
                    send_script("Vision_DoJob(job1)")

                    break

        # Find center of target
            x, y = getCenter(WorkImage, pet)
            x_c = (y)  * mm_pixel
            y_c = (x)  * mm_pixel
            loc = np.matmul(transform_mat, np.array([x_c, y_c, 1]))

            if task == 'feed' or task == 'water':
                takepic = True
                if pet == 'cat':
                    print('Feed cat')
                    # TO DO
                    set_io(0.0)
                    script = "PTP(\"CPP\",760.00, 60, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    
                    # -------------------------------------------------------------------------------#
                    # head
                    script = "PTP(\"CPP\",760.00, 60, 270, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",760.00, 60, 400, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 170, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",350.00, 0, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    # --------------------------------------------------------------------------------#

                    # -------------------------------------------------------------------------------#
                    # edge
                    script = "PTP(\"CPP\",795.00, 95, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",795.00, 95, 195, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    time.sleep(3)
                    set_io(1.0)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -87.00, 0.0, 45.00, 2, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    
                    script = "PTP(\"CPP\",795.00, 95, 195, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 170, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",760.00, 60, 400, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",760.00, 60, 277, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",760.00, 60, 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                elif pet == 'dog':
                    print('Feed dog')
                    
                    set_io(0.0)
                    script = "PTP(\"CPP\",760.00, 60, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    
                    # -------------------------------------------------------------------------------#
                    # head
                    script = "PTP(\"CPP\",760.00, 60, 270, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",760.00, 60, 400, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 170, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",350.00, 0, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    # --------------------------------------------------------------------------------#

                    # -------------------------------------------------------------------------------#
                    # edge
                    script = "PTP(\"CPP\",795.00, 95, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",795.00, 95, 195, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    time.sleep(3)
                    set_io(1.0)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -87.00, 0.0, 45.00, 2, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+80)+","+ str(loc[1])+", 300, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    
                    script = "PTP(\"CPP\",795.00, 95, 195, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",795.00, 95, 350, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 0, 170, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",350.00, 0, 200, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",760.00, 60, 400, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",760.00, 60, 277, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",760.00, 60, 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                elif pet == 'fish':
                    print('Feed fish')
                    # TO DO
                    set_io(0.0)
                    script = "PTP(\"CPP\",660.00, -30, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",660.00, -30, 165, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    time.sleep(3)
                    set_io(1.0)

                    script = "PTP(\"CPP\",660.00, -30, 350, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+70)+","+ str(loc[1]+10)+", 400, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+70)+","+ str(loc[1]+10)+", 400, -80.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+70)+","+ str(loc[1]+10)+", 400, -180.00, 0.0, 45.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",660.00, -30, 250, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",660.00, -30, 165, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",660.00, -30, 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                elif pet == 'plant':
                    set_io(0.0)
                    script = "PTP(\"CPP\",590.00, -100, 400, -180.00, 0.0, 45.00, 30, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",590.00, -100, 185, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    time.sleep(5)
                    script = "PTP(\"CPP\",590.00, -100, 500, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+57)+","+ str(loc[1]-13)+", 500, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+57)+","+ str(loc[1]-13)+", 500, -120.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\","+ str(loc[0]+57)+","+ str(loc[1]-13)+", 500, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",590.00, -100, 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",590.00, -100, 185, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",590.00, -100, 300, -180.00, 0.0, 45.00, 10, 200, 0, false)"
                    send_script(script)

                else:
                    print('Wrong pet')



            elif task == 'play':
                if pet == 'cat':
                    set_io(0.0)
                    script = "PTP(\"CPP\",600.00, 500, 400, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 200, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 120, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 225.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 135.00, 10, 10, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 350, 350, -180.00, 0.0, 135.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",500.00, 50, 500, -180.00, 0.0, 135.00, 100, 10, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 120, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",850.00, 250, 300, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                elif pet == 'dog':
                    print('Play with dog')
                    # TO DO
                    set_io(0.0)
                    script = "PTP(\"CPP\",600.00, 500, 400, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 200, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 120, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(1.0)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 225.00, 5, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 135.00, 10, 10, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",350.00, 350, 350, -180.00, 0.0, 135.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",500.00, 50, 500, -180.00, 0.0, 135.00, 100, 10, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 350, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)

                    script = "PTP(\"CPP\",850.00, 250, 120, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)
                    set_io(0.0)

                    script = "PTP(\"CPP\",850.00, 250, 300, -180.00, 0.0, 225.00, 10, 200, 0, false)"
                    send_script(script)
                else:
                    print('Wrong pet')
            else:
                print('Wrong task')

            targetP1 = "350.00, 350, 730, -180.00, 0.0, 135.00"
            script = "PTP(\"CPP\","+targetP1+",10,200,0,false)"
            send_script(script)
            isReceive = False
            print('Done')
            send_script("Vision_DoJob(job1)")

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


isReceive = False
def main(args=None):
    rclpy.init(args=args)

    global queue_url 
    queue_url = 'https://sqs.ap-northeast-1.amazonaws.com/739183738838/pizzaQueue.fifo'

    global sqs
    sqs = boto3.client('sqs', 
            region_name='ap-northeast-1', 
            aws_access_key_id="AKIA2YGWIX7LOCLM6ZBA", 
            aws_secret_access_key="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")

    # Receive message from SQS queue
    
    global isReceive
    while isReceive == False:
        # global response
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'All',
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All',
            ],
            # VisibilityTimeout=30,
            WaitTimeSeconds=10,
        )

        if ('Messages' in response) == False: 
            print('No Message!!!!')
        else :
            message = response['Messages'][0]
            # global receipt_handle
            receipt_handle = message['ReceiptHandle']
            print('Received message: {}'.format(message['Body']))
            if ('MessageAttributes' in message) == False:
                print('No attributes')
                # Delete received message from queue
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
            else:
                for attr in message['MessageAttributes']:
                    print('Attribute {attr_name}: {attr_value}'.format(attr_name=attr, attr_value=message['MessageAttributes'][attr]['StringValue']))
            
            global pet
            global task
            pet = message['MessageAttributes']['pet']['StringValue']
            task = message['MessageAttributes']['task']['StringValue']

            # global isReceive
            isReceive = True

            # Delete received message from queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            targetP1 = "350.00, 350, 730, -180.00, 0.0, 135.00"
            script = "PTP(\"CPP\","+targetP1+",10,200,0,false)"
            send_script(script)
            send_script("Vision_DoJob(job1)")

    # print('---------------------------------------------------------------')
    # print('response : ', response)
    # print('---------------------------------------------------------------')

    # print(f"Number of messages received: {len(response.get('Messages', []))}")

    

    
    node = ImageSub('image_sub')
    rclpy.spin(node)
    print('test')
    # print('0')
    # node.destroy_node()

    # print('1')

    # minimal_publisher = MininalPublisher()
    # print('2')
    # rclpy.spin(minimal_publisher)
    # minimal_publisher.destroy_node()
    node.destroy_node()
    rclpy.shutdown()

    

if __name__ == '__main__':
    main()
