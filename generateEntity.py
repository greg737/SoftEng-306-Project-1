#!/usr/bin/python
import subprocess
import os
import stat
import sys
import getopt

# Directory of where the temporary robot .py files will be written
directory = "./se306Project1/src/"
debug_text1 = "    debug = Debugger(robot)"
debug_text2 = "    debug.start()"
processes = []

def main(argv, config):
    testing = False
    debugging = False
    try:
        opts, args = getopt.getopt(argv,"td")
    except getopt.GetoptError:
        print 'test.py -d for debugger mode '
        print 'test.py -t for debugger mode '
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-t':
            testing = True
        elif opt == '-d':
            debugging = True

    # List of the temporary robot files created
    file_name = []
    # Types of robots that the script reads the config file for
    robot_type = ["Picker", "Carrier", "Visitor", "Worker", "Animal", "Tractor"]
    # Loads the fields in the config file

    # Creates or overwrites the myworld.world file
    myworld = open('world/myworld.world','w')
    # Reads and add the world template to the world file to be written
    world_template = open('world/templates/myworld.template').read()
    myworld.write(world_template)

    total_robots = 0;
    # Each robot type will start at a different y-position
    for type in robot_type:
        # Loads the corresponding robot template
        string = open('world/templates/' + type + '.template').read()
        if config.get(type.lower() + '.number') is None:
            break
        number = int(config.get(type.lower() + '.number'))
        if number > 4:  # Limit of 4 for each entity
            number = 4
        robot = ""
        if type == "Carrier":
            x_value = -50
        else:
            x_value = 45 - robot_type.index(type)*4
        for i in range(0, number):
            if type != "Picker":
                if type == "Carrier":
                    x_value += 10
                    constructor_name = "Robot" + type
                    y = -35-(4*i)
                else:
                    constructor_name = type
                    y = -35-(4*i)

                robot += type.lower() + "( pose [ " + str(x_value)  +  " " + str(y) + " 0.000 90 ] name \"r" + str(total_robots) + "\")" + "\n"
                if type != "Carrier":
                    constructor = "    robot = " + constructor_name + "(\"" + type + str(i) + "\", " + str(total_robots) + ", " + str(x_value) + ", " + str(y) +", math.pi/2)"
                else:
                    constructor = "    robot = " + constructor_name + "(\"" + type + str(i) + "\", " + str(total_robots) + ", " + str(x_value) + ", " + str(y) +", math.pi/2," + config.get("capacity.number") + ")"
                name = type + str(i) + ".py" # Name of the robot files
            else:
                output = spawnPickers(i, total_robots, file_name, config)
                robot += output[0]
                constructor = output[1]
                name = output[2]

            file_name.append(name)
            temp = open(os.path.join(directory, name),'w')
            if debugging:
                constructor = constructor + "\n" + debug_text1 + "\n" + debug_text2
            # Replaces "@@@" string in the template with the constructor
            temp.write(string.replace("@@@", constructor))
            temp.close()
            # Gives the temporary robot file run permission
            os.chmod(directory+name,stat.S_IRWXU)

            total_robots += 1
        robot = robot + "\n"
        # Writes the robot models to the world file
        myworld.write(robot)
    myworld.close()

    # This is the carrier queue creation
    string = open('world/templates/Queue.template').read()
    temp = open(os.path.join(directory, "Queue_0.py"),'w')
    # Replaces "@@@" string in the template with the constructor
    temp.write(string.replace("@@@", "    carrier_queue = Carrier_Queue(" + config.get("capacity.number") + ")"))
    temp.close()
    # Gives the temporary robot file run permission
    os.chmod(directory+"Queue_0.py",stat.S_IRWXU)
    file_name.append("Queue_0.py")


    if not(testing):
        for name in file_name:
            # Runs all the temporary robot files created
            command = ["rosrun", "se306Project1", name]
            processes.append(subprocess.Popen(command, shell=False))

    return file_name

"""
@function

The function generate the constructor line for both the world file and the robot's run script with
the appropriate position between the orchard rows
"""
def spawnPickers(number, total_robots, file_name, config):
    picker = ""
    #Creates the robot model of each robot to be appended to the world file
    picker ="picker( pose [ " + str(getPickerPosition(config, number))  +  " -28 0.000 90 ] name \"r" + str(total_robots) + "\")" + "\n"
    #The constructor of that robot type with the robot_id and the x y positions
    constructor = "    robot = " + "Robot" + "Picker" + "(\"" + "Picker" + str(number) + "\", " + str(total_robots) + ", " + str(getPickerPosition(config, number)) + ", -28, math.pi/2," + config.get("capacity.number") + ")"
    name = "Picker" + str(number) + ".py" #Name of the robot files
    return [picker, constructor, name]

"""
@function

The function calculates the picker x position which is in between the orchard rows
"""
def getPickerPosition(config, robot_number):
    WORLD_WIDTH = 80
    rows = int(config.get('orchard.number'))
    #max number of orchards is 10
    if rows > 10:
        rows = 10
    elif rows < 1:
        rows = 1

    #Set the width between the rows
    width_between_rows = WORLD_WIDTH/(rows)
    if robot_number == 0:
        return (-WORLD_WIDTH/2 + width_between_rows/2) - 4
    else:
        return -WORLD_WIDTH/2 + width_between_rows*robot_number


"""
@function

The function delete all the temporary robot files and the myworld.world file and kills
the entity processes running
"""
def exit_process(file_name):
    os.remove('./world/myworld.world')
    for name in file_name:
        os.remove(directory+name)
    for process in processes:
        process.kill()

if __name__ == "__main__":
    main(sys.argv[1:])


