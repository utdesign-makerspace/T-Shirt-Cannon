from threading import Thread
import signal
import sys
import time
import RPi.GPIO as GPIO

PWM_FREQ = 1500

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.OUT)   # PWM out
GPIO.setup(11,GPIO.OUT)  # PWM GND
sound_pwm  = GPIO.PWM(7, PWM_FREQ)
GPIO.output(11,False)

sound_pwm.start(50)


while(1):
    time.sleep(1)
    pass

