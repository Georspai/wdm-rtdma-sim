from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import random


@dataclass
class Packet:
    """
    Represents a network packet with essential attributes such as id, source, destination, size, and timestamp.
    Attributes:
        id (int): Unique identifier for the packet.
        source (int): The source node of the packet.
        destination (int): The destination node of the packet.
        size (int): The size of the packet in bytes.
        time (int): The time at which the packet was generated or received.
    """
    id: int
    source: int
    destination: int
    size: int
    arrival_time: int


@dataclass
class Buffer:
    """
    Represents a buffer that holds packets for a node in the network. It manages the storage and retrieval of packets.
    """
    packets: List[Packet]
    max_size: int
    policy: str  # e.g., 'fifo', 'fifo-compatible', 'uniform-random'
    rng: random.Random = field(default_factory=random.Random)

    _valid_buffer_policies = ("fifo", "fifo-compatible", "uniform")

    def __post_init__(self):
        """Initialize the buffer with an empty list of packets."""
        self.packets = []

    @property
    def is_full(self) -> bool:
        """Check if the buffer is full."""
        return len(self.packets) >= self.max_size

    @property
    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return len(self.packets) == 0

    def add_packet(self, packet: Packet) -> bool:
        """Add a packet to the buffer if there is space."""
        if not self.is_full:
            self.packets.append(packet)
            return True
        return False

    def pop_packet(self, valid_destinations) -> Optional[Packet]:
        """Remove and return the first packet from the buffer if it is not empty."""
        if not self.is_empty:
            if self.policy == "fifo-compatible":
                return self.fifo_compatible_policy(valid_destinations)
            elif self.policy == "fifo":
                return self.fifo_policy(valid_destinations)
            elif self.policy == "uniform":
                return self.uniform_random_policy(valid_destinations)
            else:
                raise ValueError(f"Unknown policy: {self.policy}.\nThe available valid buffer selection policies are:{self._valid_buffer_policies} ")
        return None

    def fifo_policy(self, valid_destinations) -> Optional[Packet]:
        """Implement FIFO policy to pop a packet from the buffer."""
        if self.packets[0].destination in valid_destinations:
            return self.packets.pop(0)
        return None

    def fifo_compatible_policy(self, valid_destinations) -> Optional[Packet]:
        """Implement FIFO-compatible policy to pop a packet from the buffer."""
        for packet in self.packets:
            if packet.destination in valid_destinations:
                self.packets.remove(packet)
                return packet
        return None

    def uniform_random_policy(self, valid_destinations) -> Optional[Packet]:
        """Implement uniform random policy to pop a packet from the buffer."""
        valid_packets = [packet for packet in self.packets if packet.destination in valid_destinations]
        if valid_packets:
            selected_packet = self.rng.choice(valid_packets)
            self.packets.remove(selected_packet)
            return selected_packet
        return None
