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

    Flags:
     - self.ack_num             上次的ack_num
     - self.                      Finish
     - ACK                      Acknowledge

    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self.window_size = 5
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.debug = debug
        self.syn = False
        self.ack_num = 0
        self.seq = 0
        self.recv_seq_num = 0
        self.fin = False
        self.base = 0
        self.next_seq_num = 0
        self.address = None
        self._connect_addr = None
        #############################################################################
        # TODO: ADD YOUR NECESSARY ATTRIBUTES HERE
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def accept(self) -> ('RDTSocket', (str, int)):
        """
        Accept a connection. The socket must be bound to an address and listening for
        connections. The return value is a pair (conn, address) where conn is a new
        socket object usable to send and receive data on the connection, and address
        is the address bound to the socket on the other end of the connection.

        This function should be blocking.
        """
        conn, addr = RDTSocket(self._rate), None
        self.address = addr
        while True:
            while not self.syn:
                recv, addr = super().recvfrom(2048)
                recv = RDTSegment.parse(recv)
                # print(recv)
                if recv.syn:
                    self.syn = True
                    # print(type(recv.payload))
                    # print(len(recv.payload))
                    self.ack_num = recv.seq_num + len(recv.payload)
                    print("Ready")
                else:
                    print("Fail")
            rdt_seg = RDTSegment(ack=True, seq_num=self.seq, syn=True, ack_num=self.ack_num, payload=b'')
            self.sendto(rdt_seg.encode(), addr)
            self.seq += len(rdt_seg.payload)
            while True:
                recv, addr = super().recvfrom(2048)
                recv = RDTSegment.parse(recv)

                if recv.ack and recv.ack_num + len(recv.payload) == self.seq + 1:
                    break
            break

        # send fsm初始状态,将所有值都重设为0
        self.set_zero()
        self.next_seq_num = 1
        self.base = 1

        logging.info("ok")
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        conn._connect_addr = addr
        return conn, addr

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

    def set_zero(self):
        self.ack_num = 0
        self.seq = 0
        self.recv_seq_num = 0
        self.base = 0
        self.next_seq_num = 0

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        # raise NotImplementedError()

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        self._connect_addr = address
        rdt_seg = RDTSegment(ack=False, seq_num=self.seq, syn=True, ack_num=self.ack_num, payload=b'')
        # print(type(rdt_seg.payload))
        # print(len(rdt_seg.payload))
        # if type(rdt_seg.payload) is not 'NoneT':
        self.seq += len(rdt_seg.payload)
        self.sendto(rdt_seg.encode(), address)

        while True:
            timer = threading.Timer(2.0, self.sendsyn, (address))
            timer.start()
            recv, addr = super().recvfrom(2048)
            recv = RDTSegment.parse(recv)
            timer.cancel()
            if recv.ack_num == self.seq and recv.ack and recv.syn and recv.seq_num == self.recv_seq_num:
                self.ack_num = recv.seq_num + 1
                rdt_seg = RDTSegment(ack=True, seq_num=self.seq, syn=False, ack_num=self.ack_num, payload=b'')
                self.sendto(rdt_seg.encode(), address)
                break
        logging.info("ok")

    def sendsyn(self, address: (str, int)):
        rdt_seg = RDTSegment(ack=False, seq_num=self.seq, syn=True, ack_num=self.ack_num, payload=b'')
        global timer
        timer = threading.Timer(2.0, self.sendsyn, (address))
        timer.start()

    def recv(self, bufsize: int) -> bytes:
        """
        Receive data from the socket.
        The return value is a bytes object representing the data received.
        The maximum amount of data to be received at once is specified by bufsize.

        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        data = None
        recv, addr = super().recvfrom(2048)
        recv = RDTSegment.parse(recv)
        data = recv.payload
        print(data)
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return data

    def send(self, bytes: bytes):
        """
        Send data to the socket.
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """

        # 初始化发送窗口
        all_segments = []
        send_window_size = 1
        send_base = 0
        next_seq_num = 0
        temp = 0  # 这个变量只在拥塞控制的时候用

        # 分段
        number_of_segments = math.ceil(len(bytes) / RDTSegment.SEGMENT_LEN)
        for i in range(number_of_segments):
            index = i * RDTSegment.MAX_PAYLOAD_LEN
            payload = bytes[index:index + RDTSegment.MAX_PAYLOAD_LEN]
            rdt_seg = RDTSegment(ack=True, seq_num=0, syn=False, ack_num=0, payload=payload)
            self.seq += len(rdt_seg.payload)
            self.sendto(rdt_seg.encode(), self._connect_addr)

        last_payload = bytes[number_of_segments * RDTSegment.SEGMENT_LEN + 1:len(bytes)]
        rdt_seg = RDTSegment(ack=True, seq_num=0, syn=False, ack_num=0, payload=last_payload)
        self.seq += len(rdt_seg.payload)
        self.sendto(rdt_seg.encode(), self._connect_addr)
        # send_seg = RDTSegment(ack=False, seq_num=0, syn=False, ack_num=0, payload=bytes)
        # self.sendto(send_seg.encode(), self._connect_addr)

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

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
