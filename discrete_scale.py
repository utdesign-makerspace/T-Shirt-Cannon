import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gtk, Gst, GstVideo, GLib


class DiscreteScale(Gtk.Scale):
    def __init__(self, values, *args, **kwargs):
        super(DiscreteScale, self).__init__(*args, **kwargs)

        values.sort()
        self.values= values

        adjustment= self.get_adjustment()
        adjustment.set_lower(values[0])
        adjustment.set_upper(values[-1])

        self.__changed_value_id= self.connect('change-value', self.__change_value)

    def __change_value(self, scale, scroll_type, value):
        # find the closest valid value
        value= self.__closest_value(value)
        # emit a new signal with the new value
        self.handler_block(self.__changed_value_id)
        self.emit('change-value', scroll_type, value)
        self.handler_unblock(self.__changed_value_id)
        return True #prevent the signal from escalating

    def __closest_value(self, value):
        return min(self.values, key=lambda v:abs(value-v))


if __name__ == '__main__':

    w= Gtk.Window()
    s= DiscreteScale([50, 100, 150, 200])
    w.add(s)
    w.set_size_request(500, 50)

    w.connect('delete-event', Gtk.main_quit)
    w.show_all()
    Gtk.main()