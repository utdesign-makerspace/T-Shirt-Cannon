# Stub module for brining in settings

#! /usr/bin/python
import pyowm
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time

DAILY_FILE = '/home/pi/src/daily_greetings.txt'
PATH = os.path.dirname(os.path.realpath(__file__))

class MessagePi():
    def __init__(self):
        #file = open(DAILY_FILE)
        data = json.load(open(DAILY_FILE))
        self.greetings = data['Daily']
        self.weather_vars = data['Weather']
        time_vars = data['Time']

        self.tf = time_vars['time_format']
        self.owm = pyowm.OWM(OWM_KEY)
        self.lcd = LCD_Display()
