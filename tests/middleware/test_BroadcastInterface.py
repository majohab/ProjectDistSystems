import unittest
import socket
import json
from time import sleep

from middleware.BroadcastInterface import BroadcastInterface
from middleware.types.MessageTypes import Coordinate


class TestBroadcastInterface(unittest.TestCase):
    def setUp(self):
        self.port = 12000
        self.listener = BroadcastInterface(self.port)

    def test_message_queue(self):
        self.listener.start()
        message = {"x": 1, "y": 2}
        data = json.dumps(message).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(data, ("<broadcast>", self.port))
        sock.close()

        sleep(0.1)

        result = self.listener.popMessage()
        expected_result = Coordinate(1, 2)

        self.assertEqual(expected_result, result)

        self.listener.shutdown()
        self.listener.join()

    def test_shutdown(self):
        self.listener.start()
        self.listener.shutdown()
        self.listener.join()
        self.assertFalse(self.listener.is_alive())