# T-Shirt-Cannon (Old Code Branch)

## What is this?
This is the Python code the robot was running when we inherited the project in Spring 2020.

## Why are we rewriting?
This code uses Raspberry Pis for both the remote and robot, and seems to use Bluetooth for communication, as well as a complex Wi-Fi AP setup for video streaming. There is lots of lag with this, so we're trying to make it more responsive by rewriting to hardware that is better suited for low latency.

## What's in this code?

Here's some quick but likely incomplete notes:

### Tools

 - GTK for the remote GUI
 - Kivy library for touchscreen compatibility
 - BlueZ for Bluetooth
 - HostAPd and dnsmasq for the Wi-Fi network

### Code Notes
  - The main files are `tsc_remote.py` for the remote and `tsc_robot.py` for the robot
 - There are mentions of a pressure sensor but also this comment in `robot/tsc_robot.py:RobotController:pressure()`: "Dummy method right now"
 - There is definitely more information to be found, please contribute!
