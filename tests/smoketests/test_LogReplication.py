from time import sleep

from client.Client import Client
from middleware.types.MessageTypes import Coordinate
from states.Follower import Follower
from states.Leader import Leader
from tests.smoketests.SmokeTest import SmokeTest


class TestLogReplication(SmokeTest):

    def test_LogReplication(self):
        """Start 3 nodes in the cluster, run the simulation with one client, verify that the commands are replicated to all
        followers"""
        self.createNodes(types=[Leader, Follower, Follower])

        sleep(1)  # Wait a short time until cluster has started

        client = Client(Coordinate(15, 15), [(self.nodes[1].ipAddress, self.nodes[1].unicastPort)], "localhost", 18011, 1000, 1000, 0)
        client.start()

        sleep(20)  # Let client send a few messages

        maxDuration = 20
        self.checkForDuration(
            passCondition=lambda: len(self.nodes[0].log) > 0,
            maxDuration=maxDuration,
            onFailedText=f"Leader did not append an action to its log after {maxDuration} seconds."
        )

        maxDuration = 20
        self.checkForDuration(
            passCondition=lambda: len(self.nodes[1].log) == len(self.nodes[2].log) == len(self.nodes[0].log),
            maxDuration=maxDuration,
            onFailedText=f"Followers did not replicate the log after {maxDuration} seconds."
        )
        client.shutdown()

    def test_LogCopy(self):
        """Start 3 Nodes in the cluster and simulate the failure of a follower.
        Run the simulation with one client. After some time, restart the node and
        verify that it copies all logs"""
        self.createNodes(types=[Leader, Follower, Follower])

        sleep(1)  # Wait a short time until cluster has started

        self.deleteNode(3)

        client = Client(Coordinate(15, 15), [(self.nodes[0].ipAddress, self.nodes[0].unicastPort)], "localhost", 18011,
                        1000, 1000, 0)
        client.start()

        sleep(5)

        self.startNode(3, Follower)

        sleep(10)



