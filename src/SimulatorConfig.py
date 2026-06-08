from dataclasses import dataclass, field
from typing import Set
import json
from pathlib import Path


@dataclass
class SimulatorConfig:
    """
    Represents the configuration for the RTDMA simulator, including parameters such as arrival rate, number of nodes, and time slots.

    Fields buffer_sizes, buffer_policies, arrival_probabilities, tx_channel_ratios,
    and rx_channel_ratios accept either a scalar (applied uniformly) or a per-node list.
    After initialization they are always normalized to list form.
    """
    num_time_slots: int
    num_nodes: int
    num_wavelengths: int
    buffer_sizes: list[int]
    buffer_policies: list[str]
    arrival_probabilities: list[float]
    tx_channel_ratios: list[float]
    rx_channel_ratios: list[float]
    tx_assignment_policy: str = "all"
    rx_assignment_policy: str = "all"
    destination_policy: str = "uniform"
    hotspot_node: int = 0
    hotspot_probability: float = 0.5

    warmup_time_slots: int = 0  # Number of initial time slots to ignore in performance metrics

    seed: int = 42  # Optional seed for reproducibility

    require_full_connectivity: bool = True  # Whether to ensure that all nodes can communicate with each other
    channel_assignment_attempts: int = 100  # Number of iterations for channel assignment algorithms

    _valid_assignment_policies: Set[str] = field(default_factory=lambda: {"all", "random", "round-robin"}, init=False, repr=False)
    _valid_buffer_policies: Set[str] = field(default_factory=lambda: {'fifo', 'fifo-compatible', 'uniform-random'}, init=False, repr=False)


    @classmethod
    def from_json(cls, path: str | Path) -> "SimulatorConfig":
        """Load a SimulatorConfig from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def __post_init__(self):
        """Validate the configuration parameters after initialization."""

        if isinstance(self.buffer_sizes, int):
            self.buffer_sizes = [self.buffer_sizes] * self.num_nodes

        elif isinstance(self.buffer_sizes, list):
            if len(self.buffer_sizes) != self.num_nodes:
                raise ValueError(
                    f"buffer_sizes must have length {self.num_nodes}, "
                    f"but got {len(self.buffer_sizes)}")
        else:
            raise TypeError(
                "buffer_sizes must be either an int or a list[int]"
            )
        
        if isinstance(self.arrival_probabilities, float):
            self.arrival_probabilities = [self.arrival_probabilities] * self.num_nodes
        elif isinstance(self.arrival_probabilities, list):
            if len(self.arrival_probabilities) != self.num_nodes:
                raise ValueError(
                    f"arrival_probabilities must have length {self.num_nodes}, "
                    f"but got {len(self.arrival_probabilities)}")
        else:
            raise TypeError(
                "arrival_probabilities must be either a float or a list[float]"
            )
        
        if isinstance(self.tx_channel_ratios, float):
            self.tx_channel_ratios = [self.tx_channel_ratios] * self.num_nodes
        elif isinstance(self.tx_channel_ratios, list):
            if len(self.tx_channel_ratios) != self.num_nodes:
                raise ValueError(
                    f"tx_channel_ratios must have length {self.num_nodes}, "
                    f"but got {len(self.tx_channel_ratios)}")
        else: 
            raise TypeError(
                "tx_channel_ratios must be either a float or a list[float]"
            ) 
        

        if isinstance(self.rx_channel_ratios, float):
            self.rx_channel_ratios = [self.rx_channel_ratios] * self.num_nodes
        elif isinstance(self.rx_channel_ratios, list):
            if len(self.rx_channel_ratios) != self.num_nodes:
                raise ValueError(
                    f"rx_channel_ratios must have length {self.num_nodes}, "
                    f"but got {len(self.rx_channel_ratios)}")
        else: 
            raise TypeError(
                "rx_channel_ratios must be either a float or a list[float]"
            )
        

        if self.tx_assignment_policy not in self._valid_assignment_policies:
            raise ValueError(
                f"Invalid tx_assignment_policy: {self.tx_assignment_policy}. "
                f"Valid options are: {self._valid_assignment_policies}"
            )
        if self.rx_assignment_policy not in self._valid_assignment_policies:
            raise ValueError(
                f"Invalid rx_assignment_policy: {self.rx_assignment_policy}. "
                f"Valid options are: {self._valid_assignment_policies}"
            )
        
        if isinstance(self.buffer_policies, str):
            self.buffer_policies = [self.buffer_policies] * self.num_nodes
        elif isinstance(self.buffer_policies, list):
            if len(self.buffer_policies) != self.num_nodes:
                raise ValueError(
                    f"buffer_policies must have length {self.num_nodes}, "
                    f"but got {len(self.buffer_policies)}")
            for policy in self.buffer_policies:
                if policy not in self._valid_buffer_policies:
                    raise ValueError(
                        f"Invalid buffer policy: {policy}. "
                        f"Valid options are: {self._valid_buffer_policies}"
                    )
        else:
            raise TypeError(
                "buffer_policies must be either a str or a list[str]"
            )
        
        # Validate that the probabilities for packet generation, transmission, and reception are between 0 and 1.
        for prob in self.arrival_probabilities:
            if not (0 <= prob <= 1):
                raise ValueError("Packet generation probabilities must be between 0 and 1.")
        for prob in self.tx_channel_ratios:
            if not (0 <= prob <= 1):
                raise ValueError("Transmission channel ratios must be between 0 and 1.")
        for prob in self.rx_channel_ratios:
            if not (0 <= prob <= 1):
                raise ValueError("Reception channel ratios must be between 0 and 1.")
            
            
        # Validate that the number of channels assigned to each node does not exceed the total number of wavelengths.
        if self.num_nodes < self.num_wavelengths:
            raise ValueError("Expected num_wavelengths <= num_nodes.")

        # Validate destination policy
        if self.destination_policy not in {"uniform", "hotspot"}:
            raise ValueError(
                f"Invalid destination_policy: {self.destination_policy}. "
                f"Valid options are: {{'uniform', 'hotspot'}}"
            )
        if self.destination_policy == "hotspot":
            if not (0 <= self.hotspot_node < self.num_nodes):
                raise ValueError(
                    f"hotspot_node must be in [0, {self.num_nodes - 1}], "
                    f"got {self.hotspot_node}"
                )
            if not (0.0 <= self.hotspot_probability <= 1.0):
                raise ValueError(
                    f"hotspot_probability must be in [0, 1], "
                    f"got {self.hotspot_probability}"
                )





        
        