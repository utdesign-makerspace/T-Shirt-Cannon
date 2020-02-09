# T-Shirt-Cannon (Old Code Branch)

## What is this?
This is the Python code the robot was running when we inherited the project in Spring 2020.

## Why are we rewriting?
This code uses Raspberry Pis for both the remote and robot, and seems to use Bluetooth for communication, as well as a complex Wi-Fi AP setup for video streaming. There is lots of lag with this, so we're trying to make it more responsive by rewriting to hardware that is better suited for low latency.
