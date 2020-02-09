#!/usr/bin/env python

from bt_ctrl import BluetoothController
from sensor_db import SensorDB, Sensor
from pydbus import SystemBus, Variant
import time
import os
import sys
from dbus.mainloop.glib import DBusGMainLoop

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

PATH = os.path.dirname(os.path.realpath(__file__))

def main():
    print "self test..."

    DBusGMainLoop(set_as_default=True)
    global mainloop
    mainloop = GObject.MainLoop()
    
    global mybt
    mybt = BluetoothController(SystemBus())

    builder = Gtk.Builder()
    builder.add_from_file(PATH + "/resources/test_bt.glade")
    window = builder.get_object("window1")


    handlers = {"window_close_sig": quit,
                "start_sig": start_disco,
                "stop_sig": stop_disco,
                "list_sig": list_devs,
                "conn_sig": connect_all,
                "scan_sig": scan,
                "purge_sig": purge_cache,
                "notify_on_sig": notify_on,
                "notify_off_sig": notify_off
                }
                
    builder.connect_signals(handlers)
    window.show_all()

    mainloop.run()

def start_disco(*args):
    mybt.scan_devices()
    mybt.start_discovery()

def stop_disco(*args):
    mybt.stop_discovery()

def list_devs(*args):
    print(mybt.sensors)
    
def connect_all(*args):
    print(mybt.sensors)
    for sensor in mybt.sensors:
        mybt.connect_device(sensor.address)

def scan(*args):
    mybt.scan_devices()

def purge_cache(*args):
    mybt.purge_cache()

def notify_on(*args):
    mybt.start_notify()

def notify_off(*args):
    mybt.stop_notify()

def notify_handler(*args):
    print("notify handler")
    print(args)

def quit(*args):
    mainloop.quit()

if __name__ == '__main__':
    main()
