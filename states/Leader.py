import json
import threading
import time
from collections import defaultdict

from middleware.types.JsonCoding import EnhancedJSONEncoder
from middleware.types.MessageTypes import AppendEntriesRequest, AppendEntriesResponse, RequestVoteMessage, LogEntry, NavigationRequest
from node.RecurringProcedure import RecurringProcedure
from states.State import State


class Leader(State):

    def __init__(self, node):
        super().__init__(node)
        self.nextIndex = {}  # for each server, index of the next log entry to send to that server
        self.matchIndex = {}  # for each server, index of highest log entry known to be replicated on server

        self.newEntries = []

        heartbeatTimeout = 0.1
        self.recurringProcedure = RecurringProcedure(heartbeatTimeout, self.sendHeartbeat)

        # Upon election: send initial heartbeat
        self.sendHeartbeat()
        self.recurringProcedure.start()

    def onClientRequestReceived(self, message: NavigationRequest):
        print(f"[{self.node.id}](Leader) onClientRequestReceived: {message}")

        newEntry = LogEntry(
            term=self.node.currentTerm,
            action=json.dumps(message, cls=EnhancedJSONEncoder)
        )
        self.newEntries.append(newEntry)

        self.node.log += newEntry  # ToDo: This should only happen after commit right?
        self.node.commitIndex = self.node.lastLogIndex()

        return self.__class__, None

    def onResponseReceived(self, message: AppendEntriesResponse):
        print(f"[{self.node.id}](Leader) onResponseReceived: {message}")

        if message.senderID not in self.nextIndex.keys():
            self.nextIndex[message.senderID] = self.node.lastLogIndex() + 1
        if message.senderID not in self.matchIndex.keys():
            self.matchIndex[message.senderID] = 0

        if not message.success:  # AppendEntries did not succeed
            if self.node.lastLogIndex() > -1:  # We can actually send a past log (maybe we just shouldn't be the Leader)
                self.nextIndex[message.senderID] -= 1

                previousIndex = max(0, self.nextIndex[message.senderID] - 1)
                previous = self.node.log[previousIndex]
                current = self.node.log[self.nextIndex[message.senderID]]

                appendEntry = AppendEntriesRequest(
                    senderID=self.node.id,
                    receiverID=message.senderID,
                    term=self.node.currentTerm,
                    commitIndex=self.node.commitIndex,
                    prevLogIndex=previousIndex,
                    prevLogTerm=previous.term,
                    entries=[current]
                )
                return self.__class__, appendEntry

        self.nextIndex[message.senderID] += 1

        if self.nextIndex[message.senderID] > self.node.lastLogIndex():
            self.nextIndex[message.senderID] = self.node.lastLogIndex()

        return self.__class__, None

    def sendHeartbeat(self):
        print(f"[{self.node.id}](Leader) sendHeartbeat")
        message = AppendEntriesRequest(
            senderID=self.node.id,
            receiverID=-1,
            term=self.node.currentTerm,
            commitIndex=self.node.commitIndex,
            prevLogIndex=len(self.node.log) - 1,
            prevLogTerm=self.node.lastLogTerm(),
            entries=self.newEntries
        )
        self.newEntries = []
        self.node.sendMessageBroadcast(message)
        self.recurringProcedure.resetTimeout()

    def onVoteRequestReceived(self, message: RequestVoteMessage):
        return self.__class__, self.generateVoteResponseMessage(message, False)

    def shutdown(self):
        # print(f"[{self.node.id}](Leader) shutdown")
        self.recurringProcedure.shutdown()
