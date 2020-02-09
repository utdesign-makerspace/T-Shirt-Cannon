#!/usr/bin/env python

# Profile
#    ^---Service
#           ^---Characteristic

from pydbus import SystemBus, Variant
import Queue
import time
import sys
import threading
from dbus.mainloop.glib import DBusGMainLoop

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

BT_ADAPTOR_HINT = None 
BLUEZ_SVC_NAME = 'org.bluez'
ADAPTER_IFACE = 'org.bluez.Adapter1'
DEVICE_IFACE = 'org.bluez.Device1'

DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

GATT_SVC_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'

LIDAR_SVC_UUID = '19b10012-e8f2-537e-4f6c-d104768a1214'
SONAR_SVC_UUID = '19b10010-e8f2-537e-4f6c-d104768a1214'
DIST_CHRC_UUID = '19b10011-e8f2-537e-4f6c-d104768a1214'

UUIDs = ['19b10012-e8f2-537e-4f6c-d104768a1214',
         '19b10010-e8f2-537e-4f6c-d104768a1214', 
         '19b10011-e8f2-537e-4f6c-d104768a1214']

MAX_RECONNECT = 1

class BluetoothSensor(object):
    def __init__(self, address):
        print("new sensor: " + str(address))
        self.address = address
        self.path = None
        self.svc_path = None
        self.chrc_path = None
        self.object = None
        self._connected = False
        self._active = False

        self._observers = {"connected": [],
                           "value": [],
                           "active": []}

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        self.handle_cb("active", value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        print("Value: " + str(new_value))
        self._value = new_value
        self.handle_cb("value", new_value)

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        self._connected = value
        self.handle_cb("connected", value)

    def connect(self, retries_left=MAX_RECONNECT):
        if not(self.connected):
            try:
                print("Trying to connect...")
                self.object['org.bluez.Device1'].Connect()
                print("Connection Sucessful")
                self.active = True
            except Exception as err:
                print("connection ERROR: " + str(err))
                return 0
        else:
            print("Already connected")
        return 1

    def disconnect(self):
        print("Disconnect device **STUB**")

    def handle_cb(self, key, value):
        for callback in self._observers[key]:
            callback(self.address, value)

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
                    print("***" + str(key) + ", " + str(value))
                    self.value = value[0] + 256*value[1]

    def en_notifications(self, path, bus):
        bus.subscribe(iface=DBUS_PROP_IFACE,
                      signal='PropertiesChanged',
                      object=path,
                      signal_fired=self.on_properties_changed)

    def start_notify(self, bus):
        #print("CHRC: " + str(chrc))
        print("CHRC path: " + str(self.chrc_path))

        chrc = bus.get(BLUEZ_SVC_NAME, self.chrc_path)
        try:
            chrc.StartNotify()
        except Exception as err:
            print("Unable to start notifying")

    def stop_notify(self, bus):
        """ Need to put in check to see if already notifying
        """
        chrc = bus.get(BLUEZ_SVC_NAME, self.chrc_path)
        try:
            chrc.StopNotify()
        except Exception as err:
            print("Unable to start notifying")

    def bind_to(self, key, cb):
        self._observers[key].append(cb)

class BluetoothController:
    def __init__(self, sys_bus=None):
        if sys_bus == None:
            sys_bus = SystemBus()
        self.bus = sys_bus
        BluetoothSensor.sys_bus = sys_bus

        self.bluez = self.bus.get(BLUEZ_SVC_NAME, '/')
        self.adapter = self.find_adapter()
        self.bluez.InterfacesAdded.connect(self._iface_added)
        self.bluez.InterfacesRemoved.connect(self._iface_removed)
        
        self.sensors = []
        
        self._observers = {"active": [], "new": []}

        self.count = 0

        self.connection_queue = Queue.Queue()
        self.conn_thread = threading.Thread(target=self.connection_monitor)
        self.conn_thread.setDaemon(True)
        self.conn_thread.start()

    def connect_device(self, address):
        print("CONNECT DEVICE")
        device = self.find_device(address)
        print("DEVICE: " + str(device) + ", address: " + str(address))
        print("device list" + str(self.sensors))
        if device:
            #threading.Thread(group=None, target=device.connect).start()
            self.connection_queue.put_nowait([device, MAX_RECONNECT])
            device.en_notifications(device.path, self.bus)
            device.en_notifications(device.chrc_path, self.bus)

    def bind_to_value(self, address, callback):
        device = self.find_device(address)
        device.bind_to("value", callback)

    def connection_monitor(self):
        while(1):
            device, retries_left = self.connection_queue.get()
            print("Starting thread...")
            threading.Thread(group=None, target=self.connect,
                             args=[device, retries_left]).start()

    def connect(self, device, retries_left=MAX_RECONNECT):
        try:
            device.bind_to("active", self.handle_cb)
            print("Trying to connect " + str(device.address))
            device.object['org.bluez.Device1'].Connect()
            print("Connection Successful")
            device.bind_to("connected", self.reconnect_device)
            device.active = True
        except Exception as err:
            err_str = str(err)
            if "Operation already in progress" in err_str:
                print("Connection in progress already")
                return
            elif "Software caused connection abort" in err_str:
                if (retries_left > 0):
                    print("Going to retry connection")
                    retries_left -= 1
                    self.connection_queue.put_nowait([device, retries_left])
                else:
                    print("Out of retries, device inactive")
                    device.active = False

    def reconnect_device(self, address, connected):
        """ Try to reconnect every 5 seconds until
            RECONNECT_TIMEOUT
            If unsuccessfull, remove device from bt cache
        """
        device = self.find_device(address)
        if device:
            if connected:
                return
            else:
                print("Lost connection, trying to reconnect")
                self.connection_queue.put_nowait([device, MAX_RECONNECT])

    def start_notify(self):
        print("NOTIFY ON")
        for sensor in self.sensors:
            sensor.start_notify(self.bus)
            print("notify dev: " + str(sensor))

    def stop_notify(self):
        for sensor in self.sensors:
            sensor.stop_notify(self.bus)

    def purge_cache(self):
        print("Purge cache")
        objs = self.bluez.GetManagedObjects()
        print("unfilterd")
        for path, ifaces in objs.items():
            print("path: " + str(path))
        objs = self.filter_devices(objs)

        for path, ifaces in objs.items():
            print("Purge? " + str(path))
            properties = ifaces[DEVICE_IFACE]
            if properties["Connected"]:
                continue
                print("NO")
            print("YES")
            self.adapter.RemoveDevice(path)
            #print("Purging: " + str(path))
            del(objs[path])

    def filter_devices(self, objects):
        """ Takes a list of bluetooth objects and returns 
            a subset of our devices
        """
        print("FILTER")
        for path, ifaces in objects.items():
            print(path)
            if DEVICE_IFACE in ifaces.keys():
                properties = ifaces[DEVICE_IFACE]
                if "UUIDs" in properties:
                    uuids = properties["UUIDs"]
                    if SONAR_SVC_UUID in uuids:
                        print("OUR device: " + str(path))
                        continue
            del(objects[path])
        print("-------------------------")
        return objects

    def find_adapter(self, pattern=None):
        objs = self.bluez.GetManagedObjects()
        for path, ifaces in objs.iteritems():
            adapter = ifaces.get(ADAPTER_IFACE)
            if adapter is None:
                continue
            if (not pattern or pattern == adapter["Address"]
                    or path.endswith(pattern)):
                obj = self.bus.get(BLUEZ_SVC_NAME, path)
                #print "Adapter: " + obj.Get("org.bluez.Adapter1", "Name")
                return obj
        raise Exception("Bluetooth adapter not found")

    def check_discovery(self):
        discovering = self.adapter.Get("org.bluez.Adapter1", "Discovering")
        return discovering

    def start_discovery(self):
        #self.purge_cache()
        #print("Setting disco filter")
        if not (self.check_discovery()):
            UUIDs_Variant = Variant('as', UUIDs)
            self.adapter.SetDiscoveryFilter({'UUIDs': UUIDs_Variant})
            #print("Starting disco")
            try:
                self.adapter.StartDiscovery()
            except:
                print("Unable to start discovery")
        #print "Discovery on"

    def stop_discovery(self):
        #print("disco off")
        if self.check_discovery():
            try:
                self.adapter.StopDiscovery()
            except:
                print("Unable to stop discovery")
                
    def scan_devices(self):
        #print "Scanning devices..."
        self.purge_cache()
        objects = self.bluez.GetManagedObjects()
        for path, ifaces in objects.iteritems():
            if GATT_CHRC_IFACE in ifaces.keys():
                self._process_chrc(path, ifaces[GATT_CHRC_IFACE])

            elif GATT_SVC_IFACE in ifaces.keys():
                self._process_svc(path, ifaces[GATT_SVC_IFACE])

            elif DEVICE_IFACE in ifaces.keys():
                self._process_dev(path, ifaces[DEVICE_IFACE])

    def _iface_added(self, path, obj_dict):
        print("Ifaces added___ " + str(path))
        address = address_from_path(path)
        o_path = path_from_gatt_path(path)
        
        if GATT_CHRC_IFACE in obj_dict.keys():
            self.update_device(address=address, path=o_path, chrc_path=path,
                object=self.bus.get(BLUEZ_SVC_NAME, o_path))

        elif GATT_SVC_IFACE in obj_dict.keys():
            self.update_device(address=address, path=o_path, svc_path=path,
                object=self.bus.get(BLUEZ_SVC_NAME, o_path))
        
        elif DEVICE_IFACE in obj_dict.keys():
            object=self.bus.get(BLUEZ_SVC_NAME, path)
            self.update_device(address=address, path=path,
                object=self.bus.get(BLUEZ_SVC_NAME, path))

    def find_device(self, address):
        for dev in self.sensors:
            if dev.address == address:
                break
        else:
            dev = None
        return dev

    def update_device(self, address, **kwargs):
        #print("update device: " + str(address))

        device = self.find_device(address)
        if device == None:
            device = BluetoothSensor(address)
            self.sensors.append(device)
            self.handle_cb("new", device.address)
        if "path" in kwargs:
            device.path = kwargs["path"]
        if "svc_path" in kwargs:
            device.svc_path = kwargs["svc_path"]
        if "chrc_path" in kwargs:
            device.chrc_path = kwargs["chrc_path"]
        if "object" in kwargs:
            device.object = kwargs["object"]

    def _iface_removed(self, path, interfaces):
        address = address_from_path(path)
        device = self.find_device(address)
        if device:
            print("Iface removed: " + str(path))
            self.sensors.remove(device)
            
    def _process_dev(self, path, dev):
        #print("Process dev: " + str(path))
        uuids = dev["UUIDs"]
        address = dev["Address"]
        
        if (uuids != None):
            for uuid in uuids:
                if (uuid == SONAR_SVC_UUID):
                    self.update_device(address=address, path=path,
                        object=self.bus.get(BLUEZ_SVC_NAME, path))
                    break

    def _process_svc(self, path, svc):
        address = address_from_path(path)
        if svc["UUID"] == SONAR_SVC_UUID:
            self.update_device(address=address, svc_path=path)

    def _process_chrc(self, path, chrc):
        address = address_from_path(path)
        if chrc["UUID"] == DIST_CHRC_UUID:
            self.update_device(address=address, chrc_path=path)

    def bind_to(self, key, cb):
        self._observers[key].append(cb)

    def handle_cb(self, key, value):
        for callback in self._observers[key]:
            print("callback: " + str(callback))
            print("value: " + str(value))
            callback(value)

def address_from_path(path):
    return path[20:37].replace("_",":")

def path_from_gatt_path(gatt_path):
    return gatt_path[0:37]
