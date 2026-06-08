from dataclasses import dataclass, field
from SimulatorConfig import SimulatorConfig
from Node import Node
from Scheduler import RTDMAScheduler
import random


@dataclass
class SimulationMetrics:
    num_nodes: int
    num_wavelengths: int
    num_time_slots: int

    # Global counters
    packets_generated: int = 0
    packets_dropped: int = 0
    packets_transmitted: int = 0
    scheduled_opportunities: int = 0
    wasted_slots: int = 0
    wasted_empty_buffer: int = 0
    wasted_incompatible_buffer: int = 0

    # Per-node counters (indexed by node_id)
    node_generated: list[int] = field(init=False)
    node_dropped: list[int] = field(init=False)
    node_transmitted: list[int] = field(init=False)
    node_wasted: list[int] = field(init=False)
    node_wasted_empty: list[int] = field(init=False)
    node_wasted_incompatible: list[int] = field(init=False)

    # Per-wavelength counters (indexed by channel_id)
    channel_transmitted: list[int] = field(init=False)
    channel_wasted: list[int] = field(init=False)

    # Per-destination received counter
    destination_received: list[int] = field(init=False)

    # Delay tracking
    delays: list[int] = field(default_factory=list)
    node_delays: list[list[int]] = field(init=False)

    # Queue length snapshots: list of per-node arrays, one per slot
    queue_lengths: list[list[int]] = field(default_factory=list)

    def __post_init__(self):
        self.node_generated = [0] * self.num_nodes
        self.node_dropped = [0] * self.num_nodes
        self.node_transmitted = [0] * self.num_nodes
        self.node_wasted = [0] * self.num_nodes
        self.node_wasted_empty = [0] * self.num_nodes
        self.node_wasted_incompatible = [0] * self.num_nodes
        self.channel_transmitted = [0] * self.num_wavelengths
        self.channel_wasted = [0] * self.num_wavelengths
        self.destination_received = [0] * self.num_nodes
        self.node_delays = [[] for _ in range(self.num_nodes)]

    def summarize(self) -> dict:
        s = {}

        s["waste_ratio"] = (
            self.wasted_slots / self.scheduled_opportunities
            if self.scheduled_opportunities > 0 else 0.0
        )
        s["empty_waste_ratio"] = (
            self.wasted_empty_buffer / self.scheduled_opportunities
            if self.scheduled_opportunities > 0 else 0.0
        )
        s["incompatible_waste_ratio"] = (
            self.wasted_incompatible_buffer / self.scheduled_opportunities
            if self.scheduled_opportunities > 0 else 0.0
        )
        s["channel_utilization"] = (
            self.packets_transmitted / (self.num_time_slots * self.num_wavelengths)
        )
        s["throughput"] = self.packets_transmitted / self.num_time_slots
        s["drop_rate"] = (
            self.packets_dropped / self.packets_generated
            if self.packets_generated > 0 else 0.0
        )

        if self.delays:
            sorted_d = sorted(self.delays)
            n = len(sorted_d)
            s["avg_delay"] = sum(sorted_d) / n
            s["max_delay"] = sorted_d[-1]
            s["p50_delay"] = sorted_d[n // 2]
            s["p95_delay"] = sorted_d[int(n * 0.95)]
            s["p99_delay"] = sorted_d[int(n * 0.99)]
        else:
            s["avg_delay"] = s["max_delay"] = 0
            s["p50_delay"] = s["p95_delay"] = s["p99_delay"] = 0

        s["node_throughput"] = [
            self.node_transmitted[i] / self.num_time_slots
            for i in range(self.num_nodes)
        ]

        s["wavelength_utilization"] = [
            self.channel_transmitted[k] / self.num_time_slots
            for k in range(self.num_wavelengths)
        ]

        if self.queue_lengths:
            num_slots = len(self.queue_lengths)
            s["avg_queue_length"] = [
                sum(self.queue_lengths[t][i] for t in range(num_slots)) / num_slots
                for i in range(self.num_nodes)
            ]
        else:
            s["avg_queue_length"] = [0.0] * self.num_nodes

        s["destination_received"] = list(self.destination_received)

        return s


@dataclass
class Simulator:

    config: SimulatorConfig

    rng: random.Random = field(init=False)
    wavelengths: list[int] = field(init=False)
    tx_sets: dict[int, set[int]] = field(init=False)
    rx_sets: dict[int, set[int]] = field(init=False)
    A: dict[int, set[int]] = field(init=False)
    B: dict[int, set[int]] = field(init=False)
    nodes: list[Node] = field(init=False)
    scheduler: RTDMAScheduler = field(init=False)
    current_slot: int = field(default=0, init=False)
    packet_counter: int = field(default=0, init=False)
    metrics: SimulationMetrics = field(init=False)

    def __post_init__(self):
        self.rng = random.Random(self.config.seed)

        self.wavelengths = list(range(self.config.num_wavelengths))
        self.tx_sets = {node_id: set()
                        for node_id in range(self.config.num_nodes)}
        self.rx_sets = {node_id: set()
                        for node_id in range(self.config.num_nodes)}
        self.A = {channel_id: set()
                  for channel_id in range(self.config.num_wavelengths)}
        self.B = {channel_id: set()
                  for channel_id in range(self.config.num_wavelengths)}

        self.nodes = []
        self.metrics = SimulationMetrics(
            num_nodes=self.config.num_nodes,
            num_wavelengths=self.config.num_wavelengths,
            num_time_slots=self.config.num_time_slots,
        )

        self.scheduler = RTDMAScheduler(A=self.A,
                                        wavelengths=self.wavelengths,
                                        num_nodes=self.config.num_nodes,
                                        rng=self.rng)

        self.assign_node_sets()

        self.create_nodes()

    def _num_channels_from_ratio(self, ratio: float) -> int:
        num = int(ratio * self.config.num_wavelengths + 0.999999)
        return max(1, min(self.config.num_wavelengths, num))

    def _assign_sets(self, ratios: list[float], policy: str) -> dict[int, set[int]]:
        sets = {node_id: set() for node_id in range(self.config.num_nodes)}
        for node_id in range(self.config.num_nodes):
            num_channels = self._num_channels_from_ratio(ratios[node_id])
            if policy == "random":
                sets[node_id] = set(self.rng.sample(self.wavelengths, num_channels))
            elif policy == "round-robin":
                start_channel = (
                    node_id * num_channels) % self.config.num_wavelengths
                sets[node_id] = set(
                    (start_channel + i) % self.config.num_wavelengths for i in range(num_channels))
            elif policy == "all":
                sets[node_id] = set(self.wavelengths)
            else:
                raise ValueError(f"Invalid assignment policy: {policy}")
        return sets

    def assign_node_sets(self):

        valid_sets = False
        for attempt in range(self.config.channel_assignment_attempts):
            self.tx_sets = self._assign_sets(
                ratios=self.config.tx_channel_ratios,
                policy=self.config.tx_assignment_policy,
            )

            self.rx_sets = self._assign_sets(
                ratios=self.config.rx_channel_ratios,
                policy=self.config.rx_assignment_policy,
            )

            valid_sets = self.validate_node_sets()
            if valid_sets:
                print(
                    f"Successfully assigned node sets after {attempt+1} attempts.")
                break

        if not valid_sets:
            raise ValueError("Exhausted all assignmnent attempts and could not get valid Tx/Rx sets for each node.")
        # Build channel sets and update the scheduler reference
        self.build_channel_sets()
        self.scheduler.A = self.A

    def validate_node_sets(self) -> bool:

        wavelengths = set(self.wavelengths)
        for node_id in range(self.config.num_nodes):
            if node_id not in self.tx_sets:
                print(f"Missing Tx set for node {node_id}.")
                return False
            if node_id not in self.rx_sets:
                print(f"Missing Rx set for node {node_id}.")
                return False

            tx = self.tx_sets[node_id]
            rx = self.rx_sets[node_id]

            if not tx:
                print(f"Node {node_id} has empty Tx set.")
                return False
            if not rx:
                print(f"Node {node_id} has empty Rx set.")
                return False

            if not tx.issubset(wavelengths):
                print(
                    f"Node {node_id} has invalid Tx channels: {tx - wavelengths}.")
                return False
            if not rx.issubset(wavelengths):
                print(
                    f"Node {node_id} has invalid Rx channels: {rx - wavelengths}.")
                return False

        all_tx_channels = set().union(*self.tx_sets.values())
        all_rx_channels = set().union(*self.rx_sets.values())

        missing_tx_channels = wavelengths - all_tx_channels
        missing_rx_channels = wavelengths - all_rx_channels

        if missing_tx_channels:
            print(
                f"Some wavelengths have no transmitting nodes: {missing_tx_channels}"
            )
            return False

        if missing_rx_channels:
            print(
                f"Some wavelengths have no receiving nodes: {missing_rx_channels}"
            )
            return False

        if self.config.require_full_connectivity:
            for src in range(self.config.num_nodes):
                for dst in range(self.config.num_nodes):
                    if src == dst:
                        continue
                    can_reach = not self.tx_sets[src].isdisjoint(
                        self.rx_sets[dst])
                    if not can_reach:
                        return False
        return True

    def build_channel_sets(self):
        self.A = {channel_id: set() for channel_id in self.wavelengths}
        self.B = {channel_id: set() for channel_id in self.wavelengths}

        for node_id, tx_channels in self.tx_sets.items():
            for channel_id in tx_channels:
                self.A[channel_id].add(node_id)

        for node_id, rx_channels in self.rx_sets.items():
            for channel_id in rx_channels:
                self.B[channel_id].add(node_id)

    def create_nodes(self):
        for idx in range(self.config.num_nodes):
            self.nodes.append(Node(id=idx,
                                   tx_channels=self.tx_sets[idx],
                                   rx_channels=self.rx_sets[idx],
                                   buffer_size=self.config.buffer_sizes[idx],
                                   rng=self.rng,
                                   buffer_selection_policy=self.config.buffer_policies[idx],
                                   arrival_probability=self.config.arrival_probabilities[idx],
                                   num_nodes=self.config.num_nodes,
                                   destination_policy=self.config.destination_policy,
                                   hotspot_node=self.config.hotspot_node,
                                   hotspot_probability=self.config.hotspot_probability))

    def step(self):
        t = self.current_slot

        # 1. Packet arrivals
        for node in self.nodes:
            packet = node.maybe_generate_packet(t, self.packet_counter)
            if packet is not None:
                self.packet_counter += 1
                self.metrics.packets_generated += 1
                self.metrics.node_generated[node.id] += 1
                if not node.buffer.add_packet(packet):
                    self.metrics.packets_dropped += 1
                    self.metrics.node_dropped[node.id] += 1

        # 2. RTDMA scheduling
        trans = self.scheduler.schedule()

        # 3. Packet transmissions
        for node_id, channel_id in trans.items():
            if channel_id is None:
                continue
            self.metrics.scheduled_opportunities += 1
            valid_destinations = self.B[channel_id]
            packet = self.nodes[node_id].send_packet(valid_destinations)
            if packet is not None:
                delay = t - packet.arrival_time + 1
                self.metrics.packets_transmitted += 1
                self.metrics.delays.append(delay)
                self.metrics.node_transmitted[node_id] += 1
                self.metrics.channel_transmitted[channel_id] += 1
                self.metrics.node_delays[node_id].append(delay)
                self.metrics.destination_received[packet.destination] += 1
            else:
                self.metrics.wasted_slots += 1
                self.metrics.node_wasted[node_id] += 1
                self.metrics.channel_wasted[channel_id] += 1
                if self.nodes[node_id].buffer.is_empty:
                    self.metrics.wasted_empty_buffer += 1
                    self.metrics.node_wasted_empty[node_id] += 1
                else:
                    self.metrics.wasted_incompatible_buffer += 1
                    self.metrics.node_wasted_incompatible[node_id] += 1

        # 4. Queue length snapshot
        self.metrics.queue_lengths.append(
            [len(node.buffer.packets) for node in self.nodes]
        )

        # 5. Advance clock
        self.current_slot += 1

    def run(self) -> SimulationMetrics:
        self.metrics = SimulationMetrics(
            num_nodes=self.config.num_nodes,
            num_wavelengths=self.config.num_wavelengths,
            num_time_slots=self.config.num_time_slots,
        )
        while self.current_slot < self.config.num_time_slots:
            self.step()
        return self.metrics
