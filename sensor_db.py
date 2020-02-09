#!/usr/bin/env python

from collections import MutableMapping

AVG_LENGTH = 10

class SensorDB(MutableMapping, dict):
    def __init__(self):
        self._observers = []

    def __getitem__(self,key):
        return dict.__getitem__(self,key)

    def __setitem__(self, key, value):
        dict.__setitem__(self,key,value)
        for callback in self._observers:
            callback(key, value)

    def __delitem__(self, key):
        dict.__delitem__(self,key)
        for callback in self._observers:
            callback(key, None)
    
    def __iter__(self):
        return dict.__iter__(self)
    
    def __len__(self):
        return dict.__len__(self)
    
    def __contains__(self, x):
        return dict.__contains__(self,x)

    def bind_to(self, cb):
        self._observers.append(cb)

    def __str__(self):
        print_str = "{"
        for value, key in dict.items(self):
            print_str = print_str + str(value) +": " + str(key) + ", "
        print_str = print_str + "}"
        return print_str

class Sensor(object):
    def __init__(self, address, name=None):
        if name==None:
            name = address
        self.name = name
        self.path = None
        self.svc_path = None
        self.chrc_path = None
        self.object = None
        self.canvas = None
        self.value_list = []
        self.avg_value = 0
        self.address = address
        self._position = None        
        self._active = False
        self._connected = False
        self._value = 0
        self._observers = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        self.update_avg()
        self.call_cb("value", val)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.call_cb("position", pos)

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, conn):
        self._connected = conn
        self.call_cb("connected", conn)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        self._active = active
        self.call_cb("active", active)

    def update_avg(self):
        if (len(self.value_list) > AVG_LENGTH):
            del(self.value_list[0])
        self.value_list.append(self._value)
        self.avg_value = sum(self.value_list)/len(self.value_list)

    def bind_to(self, key, cb):
        self._observers.append({"var": key, "callback": cb})

    def clear_binds(self, key):
        for i in range(0, len(self._observers)):
            if self._observers[i]["var"] == key:
                self._observers.remove(self._observers[i])

    def call_cb(self, key, value):
        for observer in self._observers:
            if key == observer['var']:
                observer["callback"](self, key, value)

    def __str__(self):
        return str(self.name)

if __name__ == '__main__':
    def test_cb(self, key, value=None):
        print("cb... " + str(key) + ": " + str(value))

    a = SensorDB()
    a.bind_to(test_cb)

    mysensor = Sensor(address="cc:ee:ff:aa:11:dd")
    a['Mun'] = Sensor(address="28:af:56:aD:17:bc")
    a['derrick'] = mysensor

    
    a['derrick'].bind_to('value', test_cb)
    a['derrick'].bind_to('connected', test_cb)

    a['derrick'].connected = 50
    a['derrick'].value = 500
    del a['derrick']

    length = len(a)
    a[length+1] = Sensor(length+1)
    length = len(a)
    a[length+1] = Sensor(length+1)
    length = len(a)
    a[length+1] = Sensor(length+1)
    length = len(a)
    a[length+1] = Sensor(length+1)
