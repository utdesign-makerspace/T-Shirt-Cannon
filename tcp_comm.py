import socket
import json
from threading import Thread, Lock
import signal
import sys
import time
import Queue

SERVER_IP = "192.168.3.16"
IFACE = ""
PORT = 65000
BUFFER_SIZE = 1024

class TCPObject(object):
    def __init__(self):
        # Outgoing message queues (socket: Queue)
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.conn = None
        self.conn_lock = Lock()
        self.thread = Thread(target=self.loop)
        self.thread.setDaemon(True)
        self.connected = False

    def start(self):
        self.thread.start()

    def speaker(self, conn):
        """ Thread that sends message over TCP connection
            Sleeps until something is added to the queue
        """
        while(1):
            msg = self.output_queue.get()
            try:
                self.send_message(conn, msg)
            except Exception as err:
                print(err)
                self.reset_conn()
                break

    def listener(self, conn):
        """ Thread that listens for messages incoming on TCP connection
            Messages are added to the input queue on arrival
        """
        while(1):
            try:
                msg = self.get_message(conn)
            except Exception as err:
                print err
                self.reset_conn()
                break

            if msg:
                #print(msg)
                self.input_queue.put_nowait(msg)
            else:
                break

    def reset_conn(self):
        if self.conn_lock.locked():
            self.connected = False
            self.input_queue.put_nowait({"status": "Disconnected"})
            self.conn_lock.release()
        else:
            return

    def send_message(self, sock, message):
        """ Send a serialized message (protobuf Message interface)
            to a socket, prepended by its length packed in 4
            bytes (big endian).
        """
        packed_len = "{0:4d}".format(len(message))
        sock.sendall(packed_len + message)

    def get_message(self, sock):
        """ Read a message from a socket. msgtype is a subclass of
            of protobuf Message.
        """
        len_buf = self.socket_read_n(sock, 4)
        msg_len = int(len_buf)
        msg_buf = self.socket_read_n(sock, msg_len)
        return self.de_serialize(msg_buf)

    def socket_read_n(self, sock, n):
        """ Read exactly n bytes from the socket.
            Raise RuntimeError if the connection closed before
            n bytes were read.
        """
        buf = ''
        while n > 0:
            data = sock.recv(n)
            if data == '':
                raise RuntimeError('unexpected connection close')
            buf += data
            n -= len(data)
        return buf

    def post(self, data):
        #print("Post: " + str(data))
        ''' This adds data to an output queue for each active connection
            Return 0 if there are no active connections
        '''
        self.output_queue.put_nowait(self.serialize(data))

    def get(self):
        """ Used to get a message from the input queue
        """
        try:
            data = self.input_queue.get_nowait()
        except Queue.Empty:
            data = 0
        return data

    def de_serialize(self, serial_data):
        """ Try to de-serialize data using json.
            Return 0 if data cannot be de-serialized.
        """
        try:
            data = json.loads(serial_data)
        except ValueError:
            data = 0
        finally:
            return data

    def serialize(self, data):
        """ Try to serialize data for transport over TCP.
            Serialized using json, returns 0 if data cannot be serialized.
        """
        try:
            serial_data = json.dumps(data)
        except ValueError:
            serial_data = 0
        finally:
            return serial_data

    def conn_handler(self, conn):
        self.connected = True
        t1 = Thread(target=self.listener, args=[conn])
        t1.setDaemon(True)
        t1.start()
        t2 = Thread(target=self.speaker, args=[conn])
        t2.setDaemon(True)
        t2.start()


class TCPClient(TCPObject):
    '''
        This class handles sending and receiving messages via TCP
        Messages are in json dictionary format: {"key1": val1, "key2": val2 ...}

        **Each send is blocked while waiting on a recceive.
          Need to add second thread to handle receiving messages.
    '''
    def __init__(self):
        super(TCPClient, self).__init__()
        self.stop = False
        self.tcp_sock = None
        self.start()

    def stop_threads(self):
        self.tcp_sock.close()
        self.stop = True

    def loop(self):
        self.input_queue.put_nowait({"status": "Connecting"})
        while(1):
            self.conn_lock.acquire()
            while(1):
                try:
                    self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.tcp_sock.connect((SERVER_IP, PORT))

                except Exception as err:
                    print("ERROR: " + str(err))# + str(sock_error.errno))
                    time.sleep(1)
                    continue

                conn = self.tcp_sock
                self.conn_handler(conn)
                self.input_queue.put_nowait({"status": "Connected"})
                break

class TCPServer(TCPObject):
    def __init__(self):
        super(TCPServer, self).__init__()
        self.stop = False
        self.conn = None
        self.running = False

        try:
            # Create a TCP/IP socket for serving connections
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((IFACE, PORT))
            self.server.listen(0)
            self.start()
            
        except socket.error as sock_error:
            print(sock_error)
            self.exit()

    def loop(self):
        self.running = True
        while self.running:
            print(self.server)
            self.conn, addr = self.server.accept()
            self.conn_handler(self.conn)

    def exit(self):
        self.conn.close()
        self.server.close()


def main():
    global server
    server = TCPServer()

    signal.signal(signal.SIGINT, sig_handler)
    while(server.running):
        time.sleep(1)

def sig_handler(*args):
    print("run: " + str(server.running))
    server.running = False
    #server.inputs = 0
    #server.exit()


if __name__ == '__main__':
    global running
    main()