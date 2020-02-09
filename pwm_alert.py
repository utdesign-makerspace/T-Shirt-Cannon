#!/usr/bin/env python

import Queue
import threading
import time
try:
    import pigpio
except ImportError:
    import fake_gpio as pigpio


class PWMAlert:
    def __init__(self, pwm_pin, low_freq=800, high_freq=1500, ground_pin=None):
        self.pwm_pin = pwm_pin
        self.pi = pigpio.pi()
        if ground_pin:
            self.pi.set_mode(ground_pin, pigpio.OUTPUT) # Ground -> output=0
            self.pi.set_pull_up_down(ground_pin, pigpio.PUD_DOWN)
        self.low_freq = 800
        self.high_freq = 1500
        self.modes = {"beep_beep": self.beep_beep,
                      "low_high": self.low_high,
                      "long_beep": self.long_beep
                      }

        self.alert_queue = Queue.Queue(maxsize=1)
        self.thread = threading.Thread(target=self.sound_alert)
        self.thread.setDaemon(True)
        self.thread.start()

    def beep_beep(self, duration):
        print("Beep beep")
        start_time = time.time()
        while(time.time() - start_time < duration):
            self.pwm_high()
            time.sleep(.2)
            self.pwm_off()
            time.sleep(.2)


    def low_high(self, duration):
        print("low high beep")
        self.pwm_low()
        time.sleep(.2)
        self.pwm_high()
        time.sleep(.2)
        self.pwm_off()

    def long_beep(self, duration):
        print("Long beep")
        start_time = time.time()
        while(time.time() - start_time < duration):
            self.pwm_high()
            time.sleep(.6)
            self.pwm_off()
            time.sleep(.2)
 
    def sound_alert(self, sound="beep_beep", duration=1):
        while(1):
            key, args = self.alert_queue.get()
            self.modes[key](*args)

    def pwm_high(self):
        self.pi.hardware_PWM(self.pwm_pin, self.high_freq, 500000)

    def pwm_low(self):
            self.pi.hardware_PWM(self.pwm_pin, self.low_freq, 500000)

    def pwm_off(self):
            self.pi.set_PWM_dutycycle(self.pwm_pin, 0)

def main():
    buzzer = PWMAlert(19)
    buzzer.alert_queue.put_nowait(["low_high", [1]])
    time.sleep(3)
if __name__ == '__main__':
    main()