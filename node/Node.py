from socket import gethostname, gethostbyname
from typing import Any

from middleware.BroadcastInterface import BroadcastInterface
from middleware.MulticastPublisher import MulticastPublisher
from middleware.UnicastListener import UnicastListener
from middleware.UnicastPublisher import UnicastPublisher
from middleware.types.MessageTypes import RequestDiscover, ResponseDiscover, Member


class Node:

    def __init__(self, id, state):
        # middleware
        hostname = gethostname()
        self.ipAddress = gethostbyname(hostname)
        self.broadcastPort = 12004
        self.unicastPort = 12005
        ## Interface
        self.broadcastInterface = BroadcastInterface(self.broadcastPort)
        self.broadcastInterface.start()
        ## publisher
        self.multicastPub = MulticastPublisher()
        self.multicastPub.start()
        self.unicastPub = UnicastPublisher()
        self.unicastPub.start()
        ## listener
        self.unicastList = UnicastListener(host=self.ipAddress, port=self.unicastPort)
        self.unicastList.start()

        # raft
        self.id = id
        self.state = state
        self.log = []  # logEntry = [( 2: 'do something'), ...]

        self.commitIndex = 0
        self.currentTerm = 0

        self.state.setNode(self)

        self.peers = {}

    def sendMessageBroadcast(self, message: Any):
        self.broadcastInterface.appendMessage(message)

    def sendMessageMulticast(self, message: Any):
        self.multicastPub.appendMessage(message)

    def sendMessageUnicast(self, message: Any):
        self.unicastPub.appendMessage(message)

    def onMessage(self, message):
        state, response = self.state.onMessage(message)
        self.state = state

        return state, response

    def getIpByID(self, id: int):
        return [member for member in self.peers if member.id == id]

    def sendDiscovery(self):
        message = RequestDiscover(Member(senderID=self.id, host=self.ipAddress, port=self.unicastPort))
        self.broadcastInterface.appendMessage(message)

    def onDiscoveryResponseReceived(self, message: ResponseDiscover):
        self.peers = self.peers | {message.member}
        self.peers = self.peers | message.memberList

    def shutdown(self):
        self.multicastPub.shutdown()
        self.multicastPub.join()
        self.unicastPub.shutdown()
        self.unicastPub.join()
        self.broadcastInterface.shutdown()
        self.broadcastInterface.join()
        self.unicastList.shutdown()
        self.unicastList.join()
