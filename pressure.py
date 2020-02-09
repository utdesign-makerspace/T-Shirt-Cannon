import time
# Import the ADS1x15 module.
import Adafruit_ADS1x15
from threading import Thread

class PressureSensor(object):
    def __init__(self):

        self.avg_list = []
        self.avg_value = 0

        self.channel = 1    # channel used on ADC A0,A1,A2,A3
        self.gain = 2/3
        self.scale_f = .0001875
        self.Vcc = 5.0 #V into the pressure sensor 5.0V
        self.offset = 180 # to correct the reading ADC
        self.Vadc = 0

        self.data = {"pressure": 0}

        # Create an ADS1115 ADC (16-bit) instance.
        self.adc = Adafruit_ADS1x15.ADS1115() 

        self.run = False
        self.thread = Thread(target=self.start_loop)
        self.thread.setDaemon(True)
        self.thread.start()

    def start_loop(self):
        self.adc.start_adc(self.channel, gain=self.gain)
        self.run = True
        while(self.run):
            # Read the last ADC conversion value and store it in list to create a smoothing function.
            try:
                raw_adc = self.adc.get_last_result() + self.offset
            except:
                print("error reading pressure sensor")
                pressure = -1
                break
            self.Vadc = raw_adc * self.scale_f 
            if self.Vadc < 0.5:
                pressure = 0.0
            else:
                # convert pressure voltage to pressure (psi) value based on the spec sheet of the pressure sensor
                pressure  = 250*(self.Vadc / self.Vcc)-25 

            self.data.update({"pressure": pressure})

            #print('ADC Value: {0} | v_p: {1:4.5} | PSI: {2:4.5}'.format(raw_adc, self.Vadc, pressure))
            self.update_avg(pressure)
            #print('Avg Value: ' + str(self.avg_value))
            # Sleep for half a second.
            time.sleep(0.1)
        self.cleanup()

    def cleanup(self):
        self.adc.stop_adc()
        print("exit?")

    def stop_loop(self):
            self.run = False

    # Define smoother function
    def update_avg(self, v):
        if (len(self.avg_list) > 10):
            del(self.avg_list[0])
        self.avg_list.append(v)
        self.avg_value = sum(self.avg_list) / len(self.avg_list)
