#!/usr/bin/env python

import tsc_remote
from sensor_db import SensorDB, Sensor
from bt_ctrl_old import BluetoothController
from gui import HubGUI
from pydbus import SystemBus

from dbus.mainloop.glib import DBusGMainLoop
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
import sys
import time
import os

PATH = os.path.dirname(os.path.realpath(__file__))

class Controller:
    def __init__(self):
        self.sensors = SensorDB()
        self.sensors.bind_to(self.db_changed)

        self.sys_bus = SystemBus()

        self.bt = BluetoothController(self.sys_bus)
        self.bt.bind_to("new", self.new_sensor)

        self.our_gui = HubGUI(self.sensors)
        self.our_gui.bind_to("quit", self.quit)
        self.our_gui.sensorPage.bind_to("load", self.enter_sensor_menu)
        self.our_gui.sensorPage.bind_to("unload", self.exit_sensor_menu)
        self.our_gui.HUD.bind_to("load", self.enter_HUD)
        self.our_gui.HUD.bind_to("unload", self.exit_HUD)
        self.our_gui.carousel.reload_current()
        
        self.bt.scan_devices()

        #self.ctrl_thread = threading.Thread()

    def new_sensor(self, address):
        if address not in self.sensors.keys():
            self.sensors[address] = Sensor(address)

    def enter_sensor_menu(self):
        #print "***** Enter sensor menu"
        #self.bt.scan_devices()
        self.bt.start_discovery()

    def exit_sensor_menu(self):
        #print "****** Leave sensor menu"
        self.bt.stop_discovery()

    def db_changed(self, name, sensor):
        #print("ctrl db changed")
        if sensor != None:
            sensor.bind_to("active", self.sensor_active_changed)

    def enter_HUD(self):
        self.bt.start_notify()

    def exit_HUD(self):
        self.our_gui.clear_cr()
        self.bt.stop_notify()
        
    def sensor_active_changed(self, sensor, key, value):
        print("ctrl, conn sensor")
        self.bt.connect_device(sensor.address)
        self.bt.bind_to_value(sensor.address, self.update_value)

    def update_value(self, address, value):
        self.sensors[address].value = value

    def quit(self, *args):
        #print "QUIT"
        mainloop.quit()

def main():
    DBusGMainLoop(set_as_default=True)
    global mainloop
    mainloop = GObject.MainLoop()
    
    ctrl = Controller()
    
    mainloop.run()

if __name__ == '__main__':
    main()