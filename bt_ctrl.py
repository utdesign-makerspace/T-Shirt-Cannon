#!/usr/bin/env python

from pydbus import SystemBus, Variant
import Queue
import time
import sys
import threading
from dbus.mainloop.glib import DBusGMainLoop

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib

BT_ADAPTOR_HINT = None 
BLUEZ_SVC_NAME = 'org.bluez'
ADAPTER_IFACE = 'org.bluez.Adapter1'
DEVICE_IFACE = 'org.bluez.Device1'

DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

GATT_SVC_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'

SONAR_SVC_UUID = '19b10010-e8f2-537e-4f6c-d104768a1214'
DIST_CHRC_UUID = '19b10011-e8f2-537e-4f6c-d104768a1214'

UUIDs = ['19b10012-e8f2-537e-4f6c-d104768a1214',
         '19b10010-e8f2-537e-4f6c-d104768a1214', 
         '19b10011-e8f2-537e-4f6c-d104768a1214']

BT_MAC = 'DC:D3:01:DA:2D:3E'

class BluetoothSensor(object):
    def __init__(self, address, path=None):
        self.address = address
        self.path = path
        self.chrc_path = None
        self.object = None
        self.chrc_obj = None
        self.connected = False
        self.pending_connection = False
        #self._observers = {"connected": [], "value": []}
'''
    @property
    def chrc_path(self):
        return self._chrc_path

    @chrc_path.setter
    def chrc_path(self, path):
        self._chrc_path = path
        #self.en_notifications(path)
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        self.handle_cb("value", new_value)

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        #print(str(self.address) + ".connected = " + str(value))
        self._connected = value
        self.handle_cb("connected", value)

    def handle_cb(self, key, value):
        for callback in self._observers[key]:
            callback(self.address, value)
'''
'''
    def on_properties_changed(self, adapter, path, dbus_iface, sig, data):
        """ Watch for dropped connections,
            possibly other properties changed
            data is a tuple containing:
                (Interface="", Properties={}, *Unknown=[])
        """
        iface = data[0]
        properties = data[1]
        if iface == DEVICE_IFACE:
            for key, value in properties.items():
                if key == "Connected":
                    self.connected = value
        elif iface == GATT_CHRC_IFACE:
            for key, value in properties.items():
                if key == "Value":
                    #print("***" + str(key) + ", " + str(value))
                    self.value = value[0] + 256*value[1]

    def bind_to(self, key, cb):
        self._observers[key].append(cb)

    def clear_binds(self, key):
        self._observers[key] = []
'''

class BluetoothController:
    def __init__(self, sys_bus=None):
        if sys_bus == None:
            self.bus = SystemBus()
        else:
            self.bus = sys_bus

        self.bluez = self.bus.get(BLUEZ_SVC_NAME, '/')
        self.adapter = self.find_adapter()
        
        #self.task_handlers = {"connect": self.connect, "discovery": self.start_discovery}
        self.bt_dev = BluetoothSensor(BT_MAC)

        self.bt_lock = threading.Lock()

    def restore_connection(self):
        """ Call internal function inside thread to prevent blocking GUI
            Restore function will run for several seconds
        """
        restore_thread = threading.Thread(target=self._restore_connection)
        restore_thread.setDaemon(True)
        restore_thread.start()

    def _restore_connection(self):
        """  Search for bt devices and attempt to connect if address is in
             our list of devices. Run for 10 seconds
             Only 1 instance may run at a time
        """
        if (self.bt_lock.locked()):
            return
        self.bt_lock.acquire()    
        start_time = time.time()        
        self.purge_cache()
        if (not self.start_discovery()): # Couldn't start discovery
            self.bt_lock.release()
            return
        while((time.time() - start_time) < 10):
            self.scan_devices()
            print("Searching...")
            time.sleep(2)
            if ((self.bt_dev.chrc_obj is not None) and self.bt_dev.connected):
                break
        self.stop_discovery()
        self.bt_lock.release()

    def purge_cache(self):
        objs = self.bluez.GetManagedObjects()
        objs = self.filter_by_uuid_and_iface(objs, SONAR_SVC_UUID, DEVICE_IFACE)

        for path, ifaces in objs.items():
            properties = ifaces[DEVICE_IFACE]
            if (properties["Connected"]):
                continue
            try:
                #print("Purge " + str(path))
                self.adapter.RemoveDevice(path)
            except Exception as err:
                print("Doesn't exist")
                continue

    def connect(self, bt_dev):
        bt_dev.pending_connection = True
        try:
            bt_dev.object['org.bluez.Device1'].Connect()
            print(str(bt_dev.address) + ": connected.")
            bt_dev.connected = True
        except Exception as err:
            print(str(bt_dev.address) + ": connect ERROR: " + str(err))
            bt_dev.connected = False
        finally:
            bt_dev.pending_connection = False

    def handle_connect(self, address):
        device = self.find_device(address)

        print("Pending connection? " + str(device.pending_connection))
        if device.pending_connection:
            print(str(address) + " pending connection")
            return
        if device.connected:
            print(str(address) + " already connected.")
            return
        else:
            threading.Thread(target=device.connect).start()
            return

    def start_discovery(self):
        discovering = self.adapter.Get("org.bluez.Adapter1", "Discovering")
        if (discovering):
            print("Already discovering...")
            return True
        else:
            UUIDs_Variant = Variant('as', UUIDs)
            self.adapter.SetDiscoveryFilter({'UUIDs': UUIDs_Variant})
            try:
                self.adapter.StartDiscovery()
                print("Started disco")
            except:
                print("Unable to start discovery")
                return False
            return True

    def stop_discovery(self):
        try:
            self.adapter.StopDiscovery()
            print("Stopped disco")
        except:
            print("Unable to stop discovery")

    def is_clear(self):
        """ Returns a list of statuses for sensors
            -1 -> device not connected
             0 -> device not clear
             1 -> device is clear
        """
        if self.bt_dev.connected:
            zero_count = self.count_zeros(self.bt_dev)
            if zero_count == -1:
                self.bt_dev.connected = False
            status = zero_count
        else:
            status = -1
        return status

    def count_zeros(self, bt_dev):
        """ 0 means nothing within 4 meters of the sensor
            Return 1 if 6+ readings show nothing in the way
            Return 0 if 2+ readings show something in the way
            Return -1 if the sensor disconnects
        """
        zero_count = 0
        for ii in range(0,5):
            try:
                distance = bt_dev.chrc_obj.ReadValue({})[0]
                if (distance == 0):
                    zero_count += 1
            except Exception as err:
                return -1
        if zero_count >= 4:
            return 1
        else:
            return 0

    def filter_by_uuid_and_iface(self, objects, uuid, iface):
        # Takes a list of bluetooth objects and returns 
        #   a subset of our devices
        return_objects = {}
        for path, ifaces in objects.items():
            if iface in ifaces.keys():
                properties = ifaces[iface]
                if "UUIDs" in properties:
                    uuid_list = properties["UUIDs"]
                    if uuid in uuid_list:
                        return_objects[path] = objects[path]
                        continue
                elif "UUID" in properties:
                    if uuid == properties["UUID"]:
                        return_objects[path] = objects[path]
                        #print("Found " + str(path))
                        continue
        return return_objects

    def find_adapter(self, pattern=None):
        objs = self.bluez.GetManagedObjects()
        for path, ifaces in objs.iteritems():
            adapter = ifaces.get(ADAPTER_IFACE)
            if adapter is None:
                continue
            if (not pattern or pattern == adapter["Address"]
                    or path.endswith(pattern)):
                obj = self.bus.get(BLUEZ_SVC_NAME, path)
                return obj
        raise Exception("Bluetooth adapter not found")

    
    def scan_devices(self):
        #print "Scanning devices..."
        
        objs = self.bluez.GetManagedObjects()
        dev_objs = self.filter_by_uuid_and_iface(objs, SONAR_SVC_UUID, DEVICE_IFACE)
        chrc_objs = self.filter_by_uuid_and_iface(objs, DIST_CHRC_UUID, GATT_CHRC_IFACE)
        
        """
        for path, ifaces in chrc_objs.iteritems():
            address = address_from_path(path)
            device_path = path_from_gatt_path(path)
            chrc_path = path
            self.update_device(address=address, device_path=device_path, chrc_path=chrc_path)
        """
        """
        for path, ifaces in dev_objs.iteritems():
            address = address_from_path(path)
            device_path = path_from_gatt_path(path)
            self.update_device(address=address, device_path=device_path)
        """

        for path, ifaces in dev_objs.iteritems():
            dev_address = address_from_path(path)
            if dev_address == self.bt_dev.address:
                print("Found dev: " + dev_address)
                self.bt_dev.path = path
                self.bt_dev.object = self.bus.get(BLUEZ_SVC_NAME, path)
                self.connect(self.bt_dev)
                # Do stuff here ...
                #address = address_from_path(path)
                #device_path = path_from_gatt_path(path)
                break

        for path, ifaces in chrc_objs.iteritems():
            dev_address = address_from_path(path)
            if dev_address == self.bt_dev.address:
                print("Found dev: " + dev_address)
                self.bt_dev.chrc_path = path
                self.bt_dev.chrc_obj = self.bus.get('org.bluez', self.bt_dev.chrc_path)
                # Do stuff here ...
                break

    """
    def update_device(self, address, device_path, chrc_path=None):
        #print("update device: " + str(address))
        device = self.find_device(address)
        if device == None:
            device = BluetoothSensor(address, device_path)
            device.bind_to("connected", self.on_connection)
            device.object = self.bus.get(BLUEZ_SVC_NAME, device_path)
            device.connected = device.object.Get(DEVICE_IFACE, "Connected")

            self.sensors.append(device)
            alias = device.object.Get("org.bluez.Device1", "Alias")
            self.handle_cb("found", device.address, True, alias)
            device.en_notifications(device_path)
            #print("en_notifications: " + str(kwargs["path"]))

        if chrc_path and (device.chrc_path == None):
            device.chrc_path = chrc_path
    """
    '''
    def on_connection(self, address, state):
        self.handle_cb("connected", address, state)

    def _iface_added(self, path, obj_dict):
        #print("IFACE added: " + str(path))
        self.scan_devices()

    def _iface_removed(self, path, interfaces):
        address = address_from_path(path) 
        device = self.find_device(address)
        
    def bind_to(self, key, cb):
        self._observers[key].append(cb)

    def handle_cb(self, key, *args):
        for callback in self._observers[key]:
            GLib.idle_add(callback, *args)

    def get_our_devs(self):
            objs = self.bluez.GetManagedObjects()
            for path, ifaces in dev_objs.iteritems():
                dev_address = address_from_path(path)
                for bt_dev in bt_devs:
                    if dev_address == bt_dev.address:
                        print("Found dev: " + dev_address)
                        self.connect(bt_dev)
                        # Do stuff here ...
                        break
                address = address_from_path(path)
                device_path = path_from_gatt_path(path)
    '''
def address_from_path(path):
    return path[20:37].replace("_",":")

def path_from_gatt_path(gatt_path):
    return gatt_path[0:37]


def main():
    pass

if __name__ == '__main__':
    main()
