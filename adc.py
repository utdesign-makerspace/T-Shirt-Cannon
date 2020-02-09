#!/usr/bin/env python
 
# Written by Limor "Ladyada" Fried for Adafruit Industries, (c) 2015
# This code is released into the public domain
 
import time
import os

try:
    import RPi.GPIO as GPIO
except ImportError:
    import fake_gpio as GPIO

#import RPi.GPIO as GPIO
 
DEBUG = 1
 
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPI_CLK  =  5
SPI_MOSI = 13
SPI_MISO =  6
SPI_CS   = 19

class ADC_MCP3008:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        # set up the SPI interface pins
        GPIO.setup(SPI_MOSI, GPIO.OUT)
        GPIO.setup(SPI_MISO, GPIO.IN)
        GPIO.setup(SPI_CLK, GPIO.OUT)
        GPIO.setup(SPI_CS, GPIO.OUT)

        #self.last_read = 0       # this keeps track of the last potentiometer value
        #self.tolerance = 5       # to keep from being jittery we'll only change
                            # volume when the pot has moved more than 5 'counts'

    def read_adc(self, channel=0):
        """ Read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
            Return -1 if channel is invalid
        """
        if ((channel > 7) or (channel < 0)):
            return -1
        GPIO.output(SPI_CS, True)
 
        GPIO.output(SPI_CLK, False)  # start clock low
        GPIO.output(SPI_CS, False)     # bring CS low
 
        commandout = channel
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(SPI_MOSI, True)
                else:
                        GPIO.output(SPI_MOSI, False)
                commandout <<= 1
                GPIO.output(SPI_CLK, True)
                GPIO.output(SPI_CLK, False)
 
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(SPI_CLK, True)
                GPIO.output(SPI_CLK, False)
                adcout <<= 1
                if (GPIO.input(SPI_MISO)):
                        adcout |= 0x1
 
        GPIO.output(SPI_CS, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
 
    def cleanup(self):
        GPIO.cleanup()
        
        """
        while True:
        # we'll assume that the pot didn't move
        trim_pot_changed = False
 
        # read the analog pin
        trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
        # how much has it changed since the last read?
        pot_adjust = abs(trim_pot - last_read)
 
        if DEBUG:
                print "trim_pot:", trim_pot
                print "pot_adjust:", pot_adjust
                print "last_read", last_read
 
        if ( pot_adjust > tolerance ):
               trim_pot_changed = True
 
        if DEBUG:
                print "trim_pot_changed", trim_pot_changed
 
        if ( trim_pot_changed ):
                set_volume = trim_pot / 10.24           # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
                set_volume = round(set_volume)          # round out decimal value
                set_volume = int(set_volume)            # cast volume as integer
 
                print 'Volume = {volume}%' .format(volume = set_volume)
                set_vol_cmd = 'sudo amixer cset numid=1 -- {volume}% > /dev/null' .format(volume = set_volume)
                os.system(set_vol_cmd)  # set volume
 
                if DEBUG:
                        print "set_volume", set_volume
                        print "tri_pot_changed", set_volume
 
                # save the potentiometer reading for the next loop
                last_read = trim_pot
 
        # hang out and do nothing for a half second
        time.sleep(0.5)
        """
