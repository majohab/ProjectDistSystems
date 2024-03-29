import time
import unittest
from unittest.mock import MagicMock
from middleware.types.MessageTypes import RequestVoteMessage
from node.Node import Node
from states.Voter import Voter


class TestVoter(unittest.TestCase):

    def setUp(self):
        self.voter = Voter(MagicMock())
        self.voter.node.lastLogIndex.return_value = 9
        self.voter.node.currentTerm = 1

    def tearDown(self):
        self.voter.shutdown()

    def test_onVoteRequestReceived_votedFor_is_None(self):
        message = RequestVoteMessage(senderID=1, receiverID=0, term=1, lastLogIndex=9, lastLogTerm=1)
        stateClass, response = self.voter.onRaftMessage(message)

        self.assertEqual(stateClass, Voter)
        self.assertTrue(response.voteGranted)
        self.assertEqual(self.voter.votedFor[1], 1)

    def test_onVoteRequestReceived_votedFor_is_not_None(self):
        message = RequestVoteMessage(senderID=1, receiverID=0, term=1, lastLogIndex=9, lastLogTerm=1)
        self.voter.votedFor[1] = 2
        stateClass, response = self.voter.onRaftMessage(message)

        self.assertEqual(stateClass, Voter)
        self.assertFalse(response.voteGranted)
        self.assertEqual(self.voter.votedFor[1], 2)

    def test_onVoteRequestReceived_less_up_to_date_log(self):
        message = RequestVoteMessage(senderID=1, receiverID=0, term=1, lastLogIndex=8, lastLogTerm=1)
        stateClass, response = self.voter.onRaftMessage(message)

        self.assertEqual(stateClass, Voter)
        self.assertFalse(response.voteGranted)
        self.assertFalse(hasattr(self.voter.votedFor, str(1)))

    def test_resetElectionTimeout(self):
        self.voter.recurringProcedure.resetTimeout()
        self.assertAlmostEqual(self.voter.recurringProcedure.nextTimeout, time.time() + self.voter.recurringProcedure.timeout)
