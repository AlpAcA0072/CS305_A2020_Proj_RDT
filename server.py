# server_address = ('127.0.0.1', 12345)
# server_address2 = ('127.0.0.1', 8081)
# from USocket import UnreliableSocket
# from rdt import RDTSocket
# import socket
#
# # s=socket.socket()
# # s.connect()
# if __name__ == '__main__':
#     socket = RDTSocket()
#     socket.bind(server_address2)
#     socket.accept()
#     while True:
#         socket.recv(2048)
#         # socket.recv(1446)
from rdt import RDTSocket
import time

if __name__ == '__main__':
    server = RDTSocket()
    server.bind(('127.0.0.1', 9999))

    while True:
        conn, client_addr = server.accept()
        start = time.perf_counter()
        while True:
            data = conn.recv(2048)
            if data:
                conn.send(data)
            else:
                break
        '''
        make sure the following is reachable
        '''
        conn.close()
        print(f'connection finished in {time.perf_counter() - start}s')
