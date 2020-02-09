from collections import MutableSequence

class MyList1(MutableSequence):
    def __init__(self, data):
        super(MyList1, self).__init__()
        if (data is not None):
            self._list = list(data)
        else:
            self._list = list()

        self._observers = []
        self.myList = []

    def __len__(self):
        return len(self.myList)

    def __delitem__(self, index):
        del(self.myList, index)

    def __setitem__(self, index, value):
        self.myList[index] = value

    def __getitem__(self, index):
        return self.myList[index]

    def insert(self, index, value):
        self.myList.insert(index, value)

    def append(self, value):
        self.myList.append(value)

    def pop(self, index):
        return self.myList.pop(index)


def main():
    x = MyList1()
    print("x: " + str(x))

    x.append(2)
    x.append(4)
    x.append(6)
    print("x: " + str(x))

    x.insert(1, 3)
    print("x: " + str(x))

    d = x.pop(1)
    x.remove(2)
    print("d: " + str(d))
    print("x: " + str(x))

    y = MyList()
    print("y: " + str(y))

    y.append(8)
    print("y: " + str(y))

    y.append(9)
    print("y: " + str(y))

    print("len x: " + str(len(x)))
    print("len y: " + str(len(y)))

if __name__ == '__main__':
    main()
