from dataclasses import dataclass, field
from typing import Optional, Set
import random
from Packet import Packet, Buffer


@dataclass
class Node:
    """
    Represents a node in the network with an identifier and a buffer to hold packets.
    Attributes:
        id (int): Unique identifier for the node.
        buffer (Buffer): The buffer associated with the node to store packets.
    """
    id: int
    tx_channels: Set[int]
    rx_channels: Set[int]
    buffer_size: int
    rng: random.Random

    buffer: Buffer = field(init=False)
    buffer_selection_policy: str = "fifo"
    arrival_probability: float = 0.0
    num_nodes: int = 1
    destination_policy: str = "uniform"
    hotspot_node: int = 0
    hotspot_probability: float = 0.5

    def __post_init__(self):
        self.buffer = Buffer(packets=[],
                             max_size=self.buffer_size,
                             policy=self.buffer_selection_policy,
                             rng=self.rng)

    def maybe_generate_packet(self, slot: int, packet_id: int) -> Optional[Packet]:
        """
        Bernoulli trial with self.arrival_probability.
        If generated: sample destination, create Packet.
        Returns the generated Packet if created, else None.
        The caller calls buffer.add_packet separately to track drops.
        """
        if self.rng.random() >= self.arrival_probability:
            return None

        # sample destination (excluding self)
        destinations = [j for j in range(self.num_nodes) if j != self.id]
        if self.destination_policy == "uniform":
            dest = self.rng.choice(destinations)
        elif self.destination_policy == "hotspot":
            if self.id != self.hotspot_node:
                if self.rng.random() < self.hotspot_probability:
                    dest = self.hotspot_node
                else:
                    others = [j for j in destinations if j != self.hotspot_node]
                    dest = self.rng.choice(others)
            else:
                dest = self.rng.choice(destinations)
        else:
            dest = self.rng.choice(destinations)

        packet = Packet(id=packet_id, source=self.id,
                        destination=dest, size=1, arrival_time=slot)
        return packet

    def send_packet(self, valid_destinations: set) -> Optional[Packet]:
        """Attempt to transmit a packet whose destination is in valid_destinations."""
        return self.buffer.pop_packet(valid_destinations)
