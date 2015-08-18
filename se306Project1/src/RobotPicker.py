#!/usr/bin/env python

import rospy
from std_msgs.msg import*
from geometry_msgs.msg import*
from nav_msgs.msg import*
from sensor_msgs.msg import*
from tf.transformations import *
import math
import time
from Robot import Robot
import Entity
import os
import ActionInterruptException


"""
@class

The RobotPicker class used to represent a picker in the world stage.
It inherits from the Robot class.

"""
class RobotPicker(Robot):

    def enum(**enums):
        return type('Enum', (), enums)

    PickerState = enum(PICKING="Picking Fruit",
                              FINDING="Finding Orchard", WAITINGFORCOLLECTION="Waiting for collection")

    def __init__(self,r_id,x_off,y_off,theta_off):
        self.picker_pub = rospy.Publisher("pickerPosition",String, queue_size=10)

        self.max_load = 100
        self.current_load = 0
        self.firstLaserReading = []
        self.timeLastAdded = time.clock()

        self.disableSideLaser = False

        self.kiwi_sub = rospy.Subscriber("carrier_kiwiTransfer", String, self.kiwi_callback)
        self.kiwi_pub = rospy.Publisher("picker_kiwiTransfer",String, queue_size=10)

        Robot.__init__(self,r_id,x_off,y_off,theta_off)

    def robot_specific_function(self):
        pass

    """
    @function
    @parameter: Msg msg

    Callback function to update position and other odometry values
    """
    def StageOdom_callback(self,msg):

        #Update the px and py values
        self.update_position(msg.pose.pose.position.x, msg.pose.pose.position.y)

        #Find the yaw from the quaternion values
        (roll, pitch, yaw) = euler_from_quaternion((msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w))

        #Update the theta value
        self.update_theta(yaw)

        #publish:- id, xpos, ypos, kiwinunber
        self.picker_pub.publish(str(self.robot_id) + "," + str(self.px) + "," + str(self.py) + "," + str(self.theta) + "," + str(self.current_load))

        fn = os.path.join(os.path.dirname(__file__), str(self.robot_id)+"pic.sta")
        output_file = open(fn, "w")
        output_file.write(str(self.robot_node_identifier)+ "\n")
        output_file.write("Picker\n")
        output_file.write(self.state+"\n")
        output_file.write(str(round(self.px,2)) + "\n")
        output_file.write(str(round(self.py,2)) + "\n")
        output_file.write(str(round(self.theta,2)) + "\n")
        output_file.write(str(self.current_load)+ "/" + str(self.max_load))
        output_file.close()


    """
    @function

    Transfer kiwifruit
    """
    def kiwi_callback(self, message):
        if (message.data.split(",")[0] != str(self.robot_id) and self.current_load >= self.max_load and message.data.split(",")[1] == str(self.robot_id)):
            print("transfer load")
            self.current_load = 0
            self.kiwi_pub.publish(str(self.robot_id))

    """
    @function

    Add a kiwifruit
    """
    def addKiwi(self, clockTime):
        if(self.current_load >= self.max_load):
            self.waitForCollection()
        elif(clockTime >= (self.timeLastAdded + 0.005)):
            self.current_load = self.current_load + 1
            self.timeLastAdded = clockTime

        """
    @function

    Wait for a carrier to pickup
    """
    def waitForCollection(self):
        self.state = self.PickerState.WAITINGFORCOLLECTION
        self._stopCurrentAction_ = True
        self.disableLaser = True
        action = self._actions_[7],[]
        if action != self._actionsStack_[-1]:
            #stop moving foward and add turn action
            self._stopCurrentAction_ = True
            self._actionsStack_.append(action)

    def gotoClosestRobot(self):
        pass

    def StageLaser_callback(self, msg):
        barCount = 0
        found = False
        if not self.disableLaser:
            for i in range(70, 110):
                if msg.ranges[i]< 4.0:
                    #check if dynamic entity
                    self._stopCurrentAction_ = True
                    if self.firstLaserReading == []:
                        self.disableLaser = True
                        #read 0-110 lasers into array
                        self.read(msg.ranges, self.firstLaserReading)
                        #add stop and wait actions to stack
                        stop = self._actions_[3], [1]
                        wait = self._actions_[4], [1]
                        self._actionsStack_.append(stop)
                        self._actionsStack_.append(wait)
                        return
                    #check for an initial laser reading
                    if self.firstLaserReading != []:
                        for i in range(len(self.firstLaserReading)):
                            #check if laser reading's differ
                            if self.firstLaserReading[i] != msg.ranges[i+70]:
                                #if they do, entity is dynamic, so wait 5's for it to leave.
                                wait = self._actions_[4], [5]
                                self._actionsStack_.append(wait)
                                #reset laserReading
                                self.firstLaserReading = []
                                return

                        print("static")
                        # action = self._actions_[2], [Entity.Direction.RIGHT]
                        action = self._actions_[1], [self.init_x, self.init_y]
                        goToAction = self._actions_[5], [self.init_x, -13.5]
                        turnAction = self._actions_[2], [Entity.Direction.RIGHT]
                        #check if action already exists in stack, otherwise laser will spam rotates
                        if action != self._actionsStack_[-1]:
                            #stop moving foward and add turn action
                            self._stopCurrentAction_ = True
                            self._actionsStack_.append(turnAction)
                            self._actionsStack_.append(goToAction)
                            self._actionsStack_.append(action)
                            self.firstLaserReading = []
                            return
                        return


            #check that all lasers in 0-20 range are not hitting object
            if not self.disableSideLaser:
                rangeCount = 0
                for i in range(160,180):
                    if msg.ranges[i]<5.0:
                        rangeCount += 1
                #move to next row
                if self.noMoreTrees>15 and self.state == self.PickerState.PICKING and \
                        self.py < -10 and self.get_current_direction() == Entity.Direction.SOUTH:
                    #stop the robot moving forward
                    self.noMoreTrees = 0
                    self.state = self.PickerState.FINDING
                    self._stopCurrentAction_ = True
                    self.disableSideLaser = True
                    goToAction = self._actions_[5], [self.px+15, self.py]
                    self._actionsStack_.append(goToAction)
                #check if no more trees at top
                elif self.noMoreTrees>15 and self.state == self.PickerState.PICKING:
                    self.noMoreTrees = 0
                    #stop the robot moving forward
                    self._stopCurrentAction_ = True
                    turnAction = self._actions_[2], [Entity.Direction.LEFT]
                    self._actionsStack_.append(turnAction)
                elif rangeCount == 0:
                    self.noMoreTrees +=1
                    self.treeDetected = False
                #check if new tree dected
                elif 0 < rangeCount < 20 and not self.treeDetected:
                    self.state = self.PickerState.PICKING
                    self.treeDetected = True
                    self.noMoreTrees=0
                    #print("Found Tree")
                    self.addKiwi(time.clock())
                elif rangeCount == 20:
                    pass

    def read(self, msg, container):
        for i in range(70, 110):
            container.append(msg[i])

    """
    @function

    Wait function
    """
    def pickerWait(self):
        while(self.current_load != 0):
            time.sleep(1)

        time.sleep(10)
        self.disableLaser = False
        return 0
