server_address2 = ('127.0.0.1', 8081)
from USocket import UnreliableSocket
from rdt import RDTSocket
import socket

# s=socket.socket()
# s.connect()
if __name__ == '__main__':
    socket2 = RDTSocket()
    socket2.bind(('127.0.0.1', 8080))
    socket2.connect(server_address2)
    with open('alice.txt', 'r') as f:
        data = f.read()
    data = data.encode()
    socket2.send(data)
    # l = len(data)
    # print(l)
    # k = l / 1000
    # print(k)
    # for i in range(int(k + 1)):
    #     print(i)
    #     if i != k:
    #         socket2.send(data[i * 1000:(i + 1) * 1000])
    #         print(data[i * 1000:(i + 1) * 1000].decode())
    #     else:
    #         socket2.send(data[i * 1000:])
    #         print(data[i * 1000:].decode())
