 #!/usr/bin/env python

from collections import MutableMapping, MutableSequence

class BindDict(MutableMapping):
    """
        dictionary with observers for add / delete and remove methods
        Callback returns a dictionary with {key: value} pair that has changed
        "update" observers called on add / modify
        "remove" observers called on del()
    """
    def __init__(self, elements=None):
        if (elements != None):
            self._dict = elements
        else:
            self._dict = dict()
        self._observers = {"update": list(), "remove": list()}

    def __getitem__(self,key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value
        for callback in self._observers["update"]:
            callback({key: value})

    def __delitem__(self, key):
        value = self._dict.pop(key)
        #dict.__delitem__(self,key)
        for callback in self._observers["remove"]:
            callback({key: value})
    
    def __iter__(self):
        return self._dict.__iter__()
    
    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return self._dict.contains(key)

    def bind_to(self, key, cb):
        self._observers[key].append(cb)
    
    def __repr__(self):
        return self._dict.__repr__()
   
    def __str__(self):
        return str(self._dict)
    
'''
class BindList(MutableSequence):
    def __init__(self, data=None):
        super(SensorDB, self).__init__()
        if (data is not None):
            self._list = list(data)
        else:
            self._list = list()

        self._observers = []

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value
        for callback in self._observers:
            callback(index, value)

    def __delitx.em__(self, index):
        del(self._list[index])
        for callback in self._observers:
            callback(index, None)

    def insert(self, index, value):
        self._list.insert(index, value)

    def __len__(self):
        return len(self._list)

    def __contains__(self, x):
        return dict.__contains__(self,x)

    def bind_to(self, cb):
        self._observers.append(cb)

    def __str__(self):
        return str(self._list)
'''

def main():
    def removed_cb(item):
        print("remove... " + str(item))

    def added_cb(item):
        print("update... " + str(item))
    global a
    a = BindDict()
    a.bind_to("remove", removed_cb)
    a.bind_to("update", added_cb)

    dict2 = {"derrick": 5000, "mun": 10000}

    print("__ add derrick")
    a['derrick'] = 100

    print("\n__ add mun")
    a['mun'] = 20


    print("\n__ chg mun")
    a['mun'] = 400    


    print("\n__ rem derrick")
    del a['derrick']

    print("\n__ chg mun & chg derrick")
    a.update(dict2)
    print("")

if __name__ == '__main__':
    main()