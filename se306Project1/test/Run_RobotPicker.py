#!/usr/bin/env python
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))


import rospy
from std_msgs.msg import*
from geometry_msgs.msg import*
from nav_msgs.msg import*
from sensor_msgs.msg import*
from tf.transformations import *
import math
from src.RobotPicker import RobotPicker
from src.ActionInterruptException import ActionInterruptException
from src.Debugger import Debugger
from  src.Entity import Direction

def main():
    #Construction of Robot objects take 3 params... Robot ID, Start X, Start Y. Start X and Start Y correlates to the myworld.world file
    #Can't create more than one robot per main() .... ie can't run more than one robot per terminal running

    robot = RobotPicker("RunPickerNode",0, -30, -28, math.pi/2,40)
    debugger = Debugger(robot)
    debugger.start()

    rospy.Rate(100)
    rospy.sleep(0.1)

    print("Current x pos = " + str(robot.px))
    print("Current y pos = " + str(robot.py))


    #You can use RobotNode_cmdvel to simulate movements, place them in the while loop to try it out
    #RobotNode_cmdvel = geometry_msgs.msg.Twist()

    moveAction = robot._actions_[0], [1000]
    goToAction = robot._actions_[5], [robot.px, -13]
    turnAction = robot._actions_[2], [Direction.RIGHT]

    robot._actionsStack_.append(moveAction)
    robot._actionsStack_.append(turnAction)
    robot._actionsStack_.append(goToAction)
    robot.state = robot.PickerState.FINDING

    while not rospy.is_shutdown():
    #check if there is an action on the stack or an action already running
        if(robot._actionsStack_.__len__() > 0 and not robot._actionRunning_):
            #get top action on stack
            action = robot._actionsStack_[-1]
            #run action with parameter
            try:
                result = action[0](*action[1])
                robot._stopCurrentAction_ = False
                #if action completes succesfully pop it
                if result == 0:
                    robot._actionsStack_.pop()
                    robot.disableSideLaser = False
            except ActionInterruptException as e:
                print(e)


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
