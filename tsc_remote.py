#!/usr/bin/env python

import adc
import bt_ctrl
import ctrl_input
import tcp_comm
from discrete_scale import DiscreteScale

from threading import Thread
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GLib
import json
from math import sin, cos, atan2, sqrt, pi
import socket
import errno
import signal

AVG_COUNT = 10

class TSCRemote:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("./resources/air_robot.glade")
        self.pressure_txt = builder.get_object("pressure_txt")
        self.status_txt = builder.get_object("status_txt")
        self.root_widget = builder.get_object("root_widget")
        self.video_frame = builder.get_object("video_grid")
        self.safety_popup = builder.get_object("safety_popup")
        self.window = builder.get_object("window1")

        self.handlers = {"quit_sig": self.exit,
                         "bt_sig": self.on_bt_request,
                         "fire_sig": self.on_fire,
                         "charge_sig": self.on_charge,
                        }

        builder.connect_signals(self.handlers)
        
        p_scaler = DiscreteScale([50, 100, 150, 200])
        p_scaler.connect("change-value", self.on_pscale_change)
        self.root_widget.attach(p_scaler, 1,4,3,1)

        self.status_list = []
        self.update_status("")
        self.update_status("")
        self.update_status("")
        self.update_status("Remote Started      ")

        self.bt = bt_ctrl.BluetoothController()
        self.adc = adc.ADC_MCP3008()
        self.comm = tcp_comm.TCPClient()

        self.left_stick = ctrl_input.PhysJoystick(self.adc, x_channel=3, y_channel=2, swap_xy=1)
        self.right_stick = ctrl_input.PhysJoystick(self.adc, x_channel=1, y_channel=0, swap_xy=0)

        self.max_pressure = 50
    	self.spd_avg = {"x": [0.]*AVG_COUNT, "y": [0.]*AVG_COUNT, "z": [0.]*AVG_COUNT}
        self.override = False
        self.run = True

        self.ctrl_thread = Thread(target=self.ctrl_loop)
        self.status_thread = Thread(target=self.status_loop)

        self.ctrl_thread.start()
        self.status_thread.start()

        self.window.show_all()
        self.window.connect("destroy", self.exit)
        self.window.fullscreen()

    def on_bt_request(self, btn, *args):
        self.bt.restore_connection()
        self.update_status("Attempting sensor reconnect...")

    def ctrl_loop(self):
        while (self.run):
            x = self.left_stick.x
            y = self.left_stick.y
            z = self.right_stick.x
            print("x, y, z = " + str(x) ", " + str(y) + ", " + str(z))
            [x, y] = self.discrete_angle(x, y)
            x_avg = int(self.smooth_mag(x, "x") * 100)
            y_avg = int(self.smooth_mag(y, "y") * 100)
            z_avg = int(self.smooth_mag(z, "z") * 100)
            
            self.comm.post({"x": x_avg, "y": y_avg, "z": z_avg})
            self.update_status(str({"x": x_avg, "y": y_avg, "z": z_avg}))
            #print({"x": x, "y": y, "z": z})
            #print({"x": x_avg, "y": y_avg, "z": z_avg})
            time.sleep(.2)
        self.exit()

    def smooth_mag(self, var, var_name):
        """ updates the last AVG_COUNT for variable
            returns the average of the last AVG_COUNT INPUT
            If the current input is 0, set all input in list
            to 0 and return 0
        """
        if var:
            self.spd_avg[var_name].pop(0)
            self.spd_avg[var_name].append(var)
            return sum(self.spd_avg[var_name])/len(self.spd_avg[var_name])
        else:
            self.spd_avg[var_name] = [0.] * AVG_COUNT
            return 0

    def on_pscale_change(self, widget, scroll_type, value):
        print("SET MAX PRESSURE")
        self.max_pressure = value

    def status_loop(self):
        while(self.run):
            msg = self.comm.get()
            #print(msg)
            if msg:
                for key, value in msg.items():
                    if key == "status":
                        self.update_status(value)
                    elif key == "pressure":
                        self.update_pressure(value)
                    elif key == "charging":
                        self.on_charging(value)
                    elif key == "charged":
                        self.on_charged(value)
                    else:
                        print("Msg: " + str(msg))

            #msg = self.comm.get_msg()
            #print(msg)
            #time.sleep(1)

    def on_charging(self, charging):
        if charging:
            self.update_status("Cannon charging...")

    def on_charged(self, charged):
        print("on charged")
        if charged:
            self.update_status("Cannon fully charged")

    def update_status(self, status):
        if (len(self.status_list) > 3):
            del(self.status_list[0])
        self.status_list.append(status)
        txt_str = ''
        for msg in self.status_list:
            txt_str += msg + '\n'
        buff = self.status_txt.get_buffer()
        GLib.idle_add(buff.set_text, txt_str)
    
    def update_pressure(self, pressure):
        GLib.idle_add(self.pressure_txt.set_text, str(pressure))
    
    def exit(self, *args):
        self.run = False
        self.comm.stop_threads()
        self.adc.cleanup()
        mainloop.quit()

    def smooth_speed(self, mag):
        return mag

    def on_fire(self, *args):
        if self.comm.connected:
            if ((self.bt.is_clear() == 1) or self.override):
                self.update_status("Safety override disabled")
                self.override = False
                self.comm.post("fire")
            else:
                self.override = self.safety_popup.run()
                self.safety_popup.hide()
                self.update_status("CAUTION: 1 time safety override enabled.")
        else:
            self.update_status("Can't Fire, communication link down")

    def on_charge(self, *args):
        if self.comm.connected:
            self.comm.post({"charge": self.max_pressure})
            print("charge")
        else:
            self.update_status("Can't charge, communication link down")

    def discrete_theta(self, x, y):
        theta = atan2(y, x)
        if theta < 0:
            theta = theta + 2*pi

        t = theta * 4 / pi
        t = round(t)/4*pi
        return;

    def discrete_angle(self, x, y):
        if abs(x) > abs(y):
            y = 0
        else:
            x = 0
        return (x, y)

    def update_btn(self, btn, is_connected):
        if is_connected:
            btn = Gtk.Button.new_from_icon_name("emblem-default", Gtk.IconSize.SMALL_TOOLBAR)
        else:
            btn = Gtk.Button.new_from_icon_name("gtk-dialog-error", Gtk.IconSize.SMALL_TOOLBAR)
        btn.set_label(name)
        btn.set_always_show_image(True)
        btn.connect("clicked", self.btn_cb, address)
        
        self.page.pack_start(btn, 0, 0, 0)
        self.page.show_all()

def main():
    global mainloop
    mainloop = GObject.MainLoop()
    remote = TSCRemote()

    #window = Gtk.Window()
    #window.add(remote.root_widget)
    #window.show_all()
    #window.connect("destroy", remote.exit)
    #window.fullscreen()

    signal.signal(signal.SIGINT, remote.exit)
    mainloop.run()

if __name__ == '__main__':
    main()
