# server_address2 = ('127.0.0.1', 8081)
# from USocket import UnreliableSocket
# from rdt import RDTSocket
# import socket
#
# # s=socket.socket()
# # s.connect()
# if __name__ == '__main__':
#     socket2 = RDTSocket()
#     socket2.bind(('127.0.0.1', 8080))
#     socket2.connect(server_address2)
#     with open('alice.txt', 'r') as f:
#         data = f.read()
#     data = data.encode()
#     socket2.send(data)
#     # l = len(data)
#     # print(l)
#     # k = l / 1000
#     # print(k)
#     # for i in range(int(k + 1)):
#     #     print(i)
#     #     if i != k:
#     #         socket2.send(data[i * 1000:(i + 1) * 1000])
#     #         print(data[i * 1000:(i + 1) * 1000].decode())
#     #     else:
#     #         socket2.send(data[i * 1000:])
#     #         print(data[i * 1000:].decode())
from rdt import RDTSocket
import time
from difflib import Differ

client = RDTSocket()
client.connect(('127.0.0.1', 9999))

data_count = 0
echo = b''
count = 3

with open('alice.txt', 'r') as f:
    data = f.read()
    encoded = data.encode()
    assert len(data) == len(encoded)

start = time.perf_counter()
for i in range(count):  # send 'alice.txt' for count times
    data_count += len(data)
    client.send(encoded)

'''
blocking send works but takes more time 
'''

while True:
    reply = client.recv(2048)
    echo += reply
    print(reply)
    if len(echo) == len(encoded) * count:
        break
client.close()

'''
make sure the following is reachable
'''

print(f'transmitted {data_count}bytes in {time.perf_counter() - start}s')
diff = Differ().compare(data.splitlines(keepends=True), echo.decode().splitlines(keepends=True))
for line in diff:
    assert line.startswith('  ')  # check if data is correctly echoed
