import math
import random

from USocket import UnreliableSocket
import threading
import time
import logging
import signal
import struct
from collections import deque
from socket import timeout as TimeoutException
from typing import Tuple, Union


class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)

    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode.
    https://docs.python.org/3/library/socket.html#socket-timeouts

    """
    """
    Reliable Data Transfer Segment

    Segment Format:

      0   1   2   3   4   5   6   7   8   9   a   b   c   d   e   f
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |VERSION|SYN|FIN|ACK|                  LENGTH                   |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |             SEQ #             |             ACK #             |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |                           CHECKSUM                            |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |                                                               |
    /                            PAYLOAD                            /
    /                                                               /
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

    Protocol Version:           1

    Flags:
     - SYN                      Synchronize
     - FIN                      Finish
     - ACK                      Acknowledge

    Ranges:
     - Payload Length           0 - 1440  (append zeros to the end if length < 1440)
     - Sequence Number          0 - 255
     - Acknowledgement Number   0 - 255

    Checksum Algorithm:         16 bit one's complement of the one's complement sum

    Size of sender's window     16
    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self.window_size = 5
        self.debug = debug

        self.ack_num = 0

        self.recv_base = 0
        self.send_base = 0

        self.recv_seq_num = 0
        self.send_seq_num = 0

        self._rate = rate

        self.address = None
        self._connect_addr = None

        self.syn = False
        self.ack_list = []
        self.content_list = []
        self.ack_content = {}

    def accept(self) -> ('RDTSocket', (str, int)):
        """
        Accept a connection. The socket must be bound to an address and listening for
        connections. The return value is a pair (conn, address) where conn is a new
        socket object usable to send and receive data on the connection, and address
        is the address bound to the socket on the other end of the connection.

        This function should be blocking.
        """
        conn, addr = RDTSocket(self._rate), None
        while True:
            while not self.syn:
                recv, addr = self.recvfrom(2048)
                recv = RDTSegment.parse(recv)
                # print(recv)
                if recv.syn:
                    self.syn = True
                    self.ack_num = recv.SEGMENT_LEN
                    print("Ready")
                else:
                    print("Fail")
            rdt_seg = RDTSegment(ack=True, seq_num=0, syn=True, ack_num=0, payload=b'')
            conn.sendto(rdt_seg.encode(), addr)
            while True:
                recv, addr2 = conn.recvfrom(2048)
                recv = RDTSegment.parse(recv)
                if recv.ack and addr == addr2 and recv.ack_num + len(recv.payload) == 0:
                    conn._connect_addr = addr
                    # self._connect_addr=addr
                    break
            break

        # send fsm初始状态,将所有值都重设为0
        logging.info("ok")
        return conn, addr

    def set_connect_addr(self, addr):
        self._connect_addr = addr

    def set_zero(self):
        self.ack_num = 0

        self.recv_base = 0
        self.send_base = 0

        self.recv_seq_num = 0
        self.send_seq_num = 0

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """

        self._connect_addr = address
        rdt_seg = RDTSegment(ack=False, seq_num=0, syn=True, ack_num=0, payload=b'')
        # print(type(rdt_seg.payload))
        # print(len(rdt_seg.payload))
        # if type(rdt_seg.payload) is not 'NoneT':
        self.sendto(rdt_seg.encode(), address)
        recv, addr = self.recvfrom(2048)
        recv = RDTSegment.parse(recv)
        if recv.ack_num == 0 and recv.ack and recv.syn and recv.seq_num == 0:
            self.ack_num = 0
            rdt_seg = RDTSegment(ack=True, seq_num=0, syn=False, ack_num=0, payload=b'')
            self.sendto(rdt_seg.encode(), addr)
        self._connect_addr = addr
        while True:
            # timer=threading.Timer(2.0,self.sendsyn,args=[address])
            #             # timer.start()

            t = threading.Thread(target=self.recv_ack)
            # t.start()

            # timer.cancel()

            break
        self.set_zero()
        logging.info("ok")

    def recv_ack(self):
        recv, addr = self.recvfrom(2048)
        recv = RDTSegment.parse(recv)
        if recv.ack_num == 0 and recv.ack and recv.syn and recv.seq_num == 0:
            self.ack_num = 0
            rdt_seg = RDTSegment(ack=True, seq_num=0, syn=False, ack_num=0, payload=b'')
            self.sendto(rdt_seg.encode(), self._connect_addr)

    # def sendsyn(self,address:(str,int )):
    #     rdt_seg = RDTSegment(ack=False, seq_num=0, syn=True, ack_num=0, payload=b'')
    #     self.sendto(rdt_seg.encode(),address)
    #     global timer
    #     timer = threading.Timer(2.0, self.sendsyn, (address))
    #     timer.start()
    def recv(self, bufsize: int) -> bytes:

        data = b''
        # recv, addr = self.recvfrom(2048)
        threading.Thread(target=self.receing).start()
        while True:
            while self.content_list:
                recv = self.content_list[0]
                self.content_list.pop(0)

                print('recv_seq_num' + str(recv.seq_num))
                print('self.ack_num' + str(self.ack_num))
                if recv.fin:
                    self.close()
                    return None
                if recv.seq_num == self.ack_num:
                    data = recv.payload
                    send_seg = RDTSegment(seq_num=self.send_seq_num, ack_num=self.ack_num, ack=True, payload=b'', )
                    self.ack_num += 1
                    self.send_seq_num += 1
                    self.sendto(send_seg.encode(), self._connect_addr)
                    self.ack_content[str(recv.seq_num)] = recv.payload
                    return data
                elif recv.seq_num > self.ack_num:
                    data = recv.payload
                    send_seg = RDTSegment(seq_num=self.send_seq_num, ack_num=self.ack_num, ack=True, payload=b'', )
                    self.sendto(send_seg.encode(), self._connect_addr)
                else:
                    data = recv.payload
                    send_seg = RDTSegment(seq_num=self.send_seq_num, ack_num=self.ack_num, ack=True, payload=b'', )
                    self.sendto(send_seg.encode(), self._connect_addr)

    def receing(self):
        while 1:
            recv, addr = self.recvfrom(2048)
            recv = RDTSegment.parse(recv)
            if len(recv.payload) == 0:
                self.ack_list.append(recv)
            else:
                self.content_list.append(recv)

    def send(self, bytes: bytes):
        number_of_segments = math.ceil(len(bytes) / RDTSegment.SEGMENT_LEN)
        window = []
        for i in range(number_of_segments + 1):
            if i != number_of_segments:
                index = i * RDTSegment.MAX_PAYLOAD_LEN
                payload = bytes[index:index + RDTSegment.MAX_PAYLOAD_LEN]
                window.append(payload)
            else:
                last_payload = bytes[i * RDTSegment.MAX_PAYLOAD_LEN:]
                if len(last_payload) != 0:
                    window.append(last_payload)

        max_ack = -1
        max_len = len(window)
        base = 0
        threading.Thread(target=self.receing).start()
        print(max_len)
        print(len(window))

        while base != max_len - 1:
            send_seg = RDTSegment(payload=window[base], ack=True, ack_num=self.ack_num, seq_num=base)
            self.sendto(send_seg.encode(), self._connect_addr)
            print('send_seq: ' + str(base))
            temp = base
            while temp == base:
                if self.ack_list:
                    receive_seq = self.ack_list[0].ack_num
                    self.ack_list.pop(0)
                    if receive_seq < base:
                        send_seg = RDTSegment(payload=window[base], ack=True, ack_num=self.ack_num, seq_num=base)
                        self.sendto(send_seg.encode(), self._connect_addr)

                    else:
                        base += 1
                # time.sleep(0.5)

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        fin_seg = RDTSegment(fin=True, seq_num=0, ack_num=0, payload=b'')
        self.sendto(fin_seg.encode(), self._connect_addr)
        super().close()

    def set_send_to(self, send_to):
        self._send_to = send_to

    def set_recv_from(self, recv_from):
        self._recv_from = recv_from


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""


class RDTSegment:
    """
    Reliable Data Transfer Segment

    Segment Format:

      0   1   2   3   4   5   6   7   8   9   a   b   c   d   e   f
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |VERSION|SYN|FIN|ACK|                  LENGTH                   |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |             SEQ #             |             ACK #             |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |                           CHECKSUM                            |
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    |                                                               |
    /                            PAYLOAD                            /
    /                                                               /
    +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

    Protocol Version:           1

    Flags:
     - SYN                      Synchronize
     - FIN                      Finish
     - ACK                      Acknowledge

    Ranges:
     - Payload Length           0 - 1440  (append zeros to the end if length < 1440)
     - Sequence Number          0 - 255
     - Acknowledgement Number   0 - 255

    Checksum Algorithm:         16 bit one's complement of the one's complement sum

    Size of sender's window     16
    """

    HEADER_LEN = 6
    MAX_PAYLOAD_LEN = 1440
    SEGMENT_LEN = MAX_PAYLOAD_LEN + HEADER_LEN
    SEQ_NUM_BOUND = 256

    def __init__(self, payload: bytes, seq_num: int, ack_num: int, syn: bool = False, fin: bool = False,
                 ack: bool = False):
        self.syn = syn
        self.fin = fin
        self.ack = ack
        self.seq_num = seq_num % RDTSegment.SEQ_NUM_BOUND
        self.ack_num = ack_num % RDTSegment.SEQ_NUM_BOUND
        if payload is not None and len(payload) > RDTSegment.MAX_PAYLOAD_LEN:
            raise ValueError
        self.payload = payload

    def encode(self) -> bytes:
        """Returns fixed length bytes"""
        head = 0x4000 | (len(self.payload) if self.payload else 0)  # protocol version: 1
        if self.syn:
            head |= 0x2000
        if self.fin:
            head |= 0x1000
        if self.ack:
            head |= 0x0800
        arr = bytearray(struct.pack('!HBBH', head, self.seq_num, self.ack_num, 0))
        if self.payload:
            arr.extend(self.payload)
        checksum = RDTSegment.calc_checksum(arr)
        arr[4] = checksum >> 8
        arr[5] = checksum & 0xFF
        arr.extend(b'\x00' * (RDTSegment.SEGMENT_LEN - len(arr)))  # so that the total length is fixed
        return bytes(arr)

    @staticmethod
    def parse(segment: Union[bytes, bytearray]) -> 'RDTSegment':
        """Parse raw bytes into an RDTSegment object"""
        try:
            assert len(segment) == RDTSegment.SEGMENT_LEN
            # assert 0 <= len(segment) - 6 <= RDTSegment.MAX_PAYLOAD_LEN
            assert RDTSegment.calc_checksum(segment) == 0
            head, = struct.unpack('!H', segment[0:2])
            version = (head & 0xC000) >> 14
            assert version == 1
            syn = (head & 0x2000) != 0
            fin = (head & 0x1000) != 0
            ack = (head & 0x0800) != 0
            length = head & 0x07FF
            # assert length + 6 == len(segment)
            seq_num, ack_num, checksum = struct.unpack('!BBH', segment[2:6])
            payload = segment[6:6 + length]
            return RDTSegment(payload, seq_num, ack_num, syn, fin, ack)
        except AssertionError as e:
            raise ValueError from e

    @staticmethod
    def calc_checksum(segment: Union[bytes, bytearray]) -> int:
        """
        :param segment: raw bytes of a segment, with its checksum set to 0
        :return: 16-bit unsigned checksum
        """
        i = iter(segment)
        bytes_sum = sum(((a << 8) + b for a, b in zip(i, i)))  # for a, b: (s[0], s[1]), (s[2], s[3]), ...
        if len(segment) % 2 == 1:  # pad zeros to form a 16-bit word for checksum
            bytes_sum += segment[-1] << 8
        # add the overflow at the end (adding twice is sufficient)
        bytes_sum = (bytes_sum & 0xFFFF) + (bytes_sum >> 16)
        bytes_sum = (bytes_sum & 0xFFFF) + (bytes_sum >> 16)
        return ~bytes_sum & 0xFFFF
