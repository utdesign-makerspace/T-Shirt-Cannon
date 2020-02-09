#!/usr/bin/env python

from sensor_db import SensorDB, Sensor
from bt_ctrl import BluetoothController
from gui import HubGUI
from pydbus import SystemBus

from dbus.mainloop.glib import DBusGMainLoop
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk
import sys
import time

import os

PATH = os.path.dirname(os.path.realpath(__file__))

def add_s(*args):
    #print("Add sensor")
    length = len(sensors)
    num = length+1
    name = "sensor_" + str(num)
    address = str(num) + str(num) + ":" + str(num) + str(num)
    print(name + ", " + address)

    sensors[address] = Sensor(name=name)
    #print(sensors)
    

def rm_s(*args):
    length = len(sensors)
    num = length

    name = "sensor_" + str(num)
    address = str(num) + str(num) + ":" + str(num) + str(num)
    print(name + ", " + address)

    if(length > 0):
        del sensors[address]

def update(*args):
    for key, val in sensors.items():
        val.value = val.value + 1

def list_sensors(*args):
    print("----------------")
    a = 4
    for key, val in sensors.items():
        print(key)
        print("Name: " + str(val.name))
        print("active: " + str(val.active))
        print("Connected: " + str(val.connected))
        print("Value: " + str(val.value))
        print("Position: " + str(val.position) + "\n")
        
def quit(*args):
    print "QUIT"
    mainloop.quit()

def dummy_cb(*args):
    for arg in args:
        print arg

def main():
    DBusGMainLoop(set_as_default=True)
    global mainloop
    mainloop = GObject.MainLoop()
    sys_bus = SystemBus()
    
    global gui
    global sensors

    sensors = SensorDB()

    gui = HubGUI(sensors)
    gui.handlers["window_close_sig"] = quit

    gui.bind_to("quit", quit)

    builder = Gtk.Builder()

    builder.add_from_file(PATH + "/resources/test_gui.glade")
    window = builder.get_object("window1")

    window.show_all()       
    
    handlers = {"window_close_sig": quit,
                "launch_sig": dummy_cb,
                "add_sig": add_s,
                "rm_sig": rm_s,
                "update_sig": update,
                "list_sig": list_sensors
    }
    
    builder.connect_signals(handlers)



    mainloop.run()

if __name__ == '__main__':
    main()