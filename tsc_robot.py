#!/usr/bin/env python
import pressure
import tcp_comm
from threading import Thread
import signal
import sys
import time
import random
try:
    import RPi.GPIO as GPIO
except ImportError:
    import fake_gpio as GPIO
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject

PWM_FREQ = 100
FIRE_PIN = 40
CHARGE_PIN = 36

'''
front
right = 19 -> 35
left 17 -> 11

rear:
left = 22 -> 15
right = 5 -> 29
'''

LF_PWM = 11  # 11 Board, 17 broadcom
RF_PWM = 37  # 37 Board, 26 broadcom
LR_PWM = 15  # 15 Board, 22 broadcom
RR_PWM = 29  # 29 Board, 5 broadcom


MAX_CHG_TIME = 5 # Max time in seconds to charge cannon
TIMEOUT = 1

class RobotController(object):
    def __init__(self):
        self.setup_gpio()

        self.run = False
        self._pres_pressuresure = 0
        self._charging = False
        self._charged = False
        self._fire = False
        self.stopped = True
        self.max_pressure = 0

        self.max_fwd = {"LF": 20, "RF": 10, "LR": 20, "RR": 10}
        self.max_bkwd = {"LF": 10, "RF": 20, "LR": 10, "RR": 20}
        self.mid = {}
        self.multi = {}
        for key in self.max_fwd.keys():
            #self.mid[key] = (self.max_fwd[key] + self.max_bkwd[key])/2
            self.mid[key] = 15 # override to account for unequal motor scale
            self.multi[key] = (self.max_fwd[key] - self.max_bkwd[key])/2

        self._speed = {"LF": 0, "RF": 0, "LR": 0, "RR": 0}

        self.run = True
        self.last_update = 0

        self.comm = tcp_comm.TCPServer()
        self.pressure_sensor = pressure.PressureSensor()

        self.status_thread = Thread(target=self.status)
        self.status_thread.setDaemon(True)
        self.thread = Thread(target=self.start_loop)
        self.status_thread.start()        
        self.thread.start()

    def status(self):
        while(self.run):
            self.comm.post({"pressure": self.pressure})
            time.sleep(.1)

    def setup_gpio(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LF_PWM,GPIO.OUT)  # PWM out
        GPIO.setup(RF_PWM,GPIO.OUT)  # PWM out
        GPIO.setup(LR_PWM,GPIO.OUT)  # PWM out
        GPIO.setup(RR_PWM,GPIO.OUT)  # PWM pwm

        GPIO.setup(FIRE_PIN,GPIO.OUT)  # Canon Fire out
        GPIO.setup(CHARGE_PIN,GPIO.OUT)  # Canon Charge

        self.motor_pwm = {"LF": GPIO.PWM(LF_PWM, PWM_FREQ),
                          "RF": GPIO.PWM(RF_PWM, PWM_FREQ),
                          "LR": GPIO.PWM(LR_PWM, PWM_FREQ),
                          "RR": GPIO.PWM(RR_PWM, PWM_FREQ)
                          }
        for motor in self.motor_pwm.values():
            motor.start(0)
        GPIO.output(CHARGE_PIN,0)
        GPIO.output(FIRE_PIN,0)

    def start_loop(self):
        self.run = True
        while(self.run):
            msg = self.comm.get()
            if msg:
                self.update(msg)
                self.update_motors()
            if (time.time() - self.last_update) > 1:
                self.stop()
            time.sleep(.01)

    def update_motors(self):
        for key, value in self._speed.items():
            self.motor_pwm[key].ChangeDutyCycle(value)
            #print(str(key) + ": " + str(value))

    def exit(self, *args):
        self.run = False
        self.comm.exit()
        GPIO.cleanup()
        print("Exited")

    @property
    def pressure(self):
        """ This gets the pressure from the pressure sensor
            Dummy method right now
        """
        #self._pressure = random.randint(1,21)*5
        self._pressure = int(self.pressure_sensor.avg_value)
        return self._pressure

    def update(self, data):
        #print(data)
        if data == "fire":
            self.fire()
        elif "charge" in data.keys():
            self.max_pressure = data["charge"]
            if not self.charging:
                Thread(target=self.charge()).start()
        elif "x" in data.keys():
            self.last_update = time.time()
            self.mecanum(data["x"], data["y"], data["z"])

    def stop(self):
        self.speed = {"LF": 0, "RF": 0, "LR": 0, "RR": 0}
        self.stopped = True

    def mecanum(self, x, y, z):
        if (x or y or z):
            spd = {}
            #print("( " + str(x) + ", " + str(y) + ", " + str(z) + ")")
            spd["LF"] = (x + y + z) / 50.0
            spd["RF"] = (-x + y - z) / 50.0
            spd["LR"] = (-x + y + z) / 50.0
            spd["RR"] = (x + y - z) / 50.0
            #print(spd)
            spd = self.normalize(spd);
            self.speed = spd
            self.stopped = False
        else:
            self.stop()

    def normalize(self, speed):
        max_speed = 1
        for spd in speed.values():
            max_speed = max(max_speed, abs(spd))

        if (max_speed):
            for key, value in speed.items():
                speed[key] = value / max_speed
        return speed

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, spd):
        for key, value in spd.items():
            if value == self._speed[key]:
                continue
            if value == 0:
                self._speed[key] = 0
            else:
                self._speed[key] = (self.multi[key] * spd[key] + self.mid[key])

        #print(self._speed)

    def can_fire(self):
        """ Performs checks before firing:
            1) Robot must be stationary
            2) Robot must not be charging
            3) Robot must be fully charged
        """
        if not self.stopped:
            self.comm.post({"status": "Cannot fire while robot is moving."})
            return False
        if self.charging:
            self.comm.post({"status": "Cannot fire while cannon is charging."})
            return False
        if not self.charged:
            self.comm.post({"status": "Cannot fire, cannon not charged fully"})
            return False
        return True

    def fire(self):
        if self.can_fire():
            self.comm.post({"status": "Cannon fired!!!"})
            print("Firing cannon")
            GPIO.output(FIRE_PIN,1)
            print("Opened dump valve")            
            time.sleep(.5)
            GPIO.output(FIRE_PIN,0)
            print("Closed dump valve")            
            self.charged = False

    @property
    def charging(self):
        return self._charging

    @charging.setter
    def charging(self, var):
        print("self.charging: " + str(self.charging))
        self._charging = var
        self.comm.post({"charging": self._charging})

    @property
    def charged(self):
        return self._charged

    @charged.setter
    def charged(self, var):
        self._charged = var
        self.comm.post({"charged": self._charged})
        print("charged updated")

    def charge(self):
        """ Charges cannon until max pressure or max time reached,
            whichever occurrs first
        """
        start_time = time.time()
        chg_time = 0
        self.charging = True
        # open
        # wait x seconds
        # close
        # check
        #restart

        sleep_time = self.max_pressure / 40
	    #print("sleep time: " + str(sleep_time))
        print("Start charging...")
        charge_count = 0
        while(charge_count < 3):
            if (((int(self.pressure)+1) >= (self.max_pressure)) or (chg_time >= MAX_CHG_TIME)):
                break
            GPIO.output(CHARGE_PIN, 1)
            print("Opened charge valve")
            time.sleep(sleep_time)
            GPIO.output(CHARGE_PIN, 0)
            print("Closed charge valve")
            time.sleep(.5)
            charge_count = charge_count + 1
            sleep_time = (self.max_pressure - self.pressure) / 45
            #print("sleep time: " + str(sleep_time))

        print("Done charging")
        self.charging = False
        self.charged = True

def main():
    global robot
    robot = RobotController()
    signal.signal(signal.SIGINT, robot.exit)
    robot.start_loop()
    
if __name__ == '__main__':
    main()
