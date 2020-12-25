server_address = ('127.0.0.1', 12345)
server_address2 = ('127.0.0.1', 8081)
from USocket import UnreliableSocket
from rdt import RDTSocket
import socket

# s=socket.socket()
# s.connect()
if __name__ == '__main__':
    socket = RDTSocket()
    socket.bind(server_address2)
    socket.accept()
    while True:
        socket.recv(2048)
        # socket.recv(1446)
