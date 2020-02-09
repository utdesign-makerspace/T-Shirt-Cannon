import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GLib

class PhysJoystick():
    adc = None
    def __init__(self, adc, x_channel=0, y_channel=1, inverted_x=0,
        inverted_y=0, swap_xy=0):
        self.adc = adc
        self.x_channel = x_channel
        self.y_channel = y_channel

        self._x = 0
        self._y = 0

	# These must have decimal to force floating point computation
        self.max_x = 1023.0
        self.max_y = 1023.0

        # dead zone in range: 0.0 to 1.0
        self.dead_zone_pct = .03

    @property
    def x(self):
        """ Poll adc for x value
            Scale x to -.5 to .5 range
        """
        x_input = self.adc.read_adc(self.x_channel)
        self._x = -(x_input/self.max_x - .5)
	if (abs(self._x) < (self.dead_zone_pct/2)):
            self._x = 0
        return self._x

    @property
    def y(self): 
        """ Poll adc for y value
            Scale y to -.5 to .5 range
        """
        y_input = self.adc.read_adc(self.y_channel)
        self._y = -(y_input/self.max_y - .5)
	if (abs(self._y) < (self.dead_zone_pct/2)):
            self._y = 0
        return self._y

def cleanup():
    self.adc.cleanup()