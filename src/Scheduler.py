from typing import Dict, Optional
import random


class RTDMAScheduler:
    A: dict[int, set[int]]
    wavelengths: list[int]
    num_nodes: int
    rng: random.Random

    def __init__(self, A: dict[int, set[int]], wavelengths: list[int], num_nodes: int, rng: random.Random):
        self.A = A
        self.wavelengths = wavelengths
        self.num_nodes = num_nodes
        self.rng = rng

    def schedule(self) -> Dict[int, Optional[int]]:

        trans: Dict[int, Optional[int]] = {node_id: None for node_id in range(self.num_nodes)}
        available_channels = list(self.wavelengths.copy())
        candidate_sets = {
            channel: set(nodes)
            for channel, nodes in self.A.items()
        }

        while len(available_channels) > 0:
            random_channel_index = self.rng.randrange(len(available_channels))
            available_channels[random_channel_index], available_channels[-1] = available_channels[-1], available_channels[random_channel_index]
            k = available_channels.pop()
            candidates = candidate_sets[k]

            if len(candidates) > 0:
                i = self.rng.choice(tuple(candidates))
                candidates.discard(i)

                trans[i] = k

                for other_channel in candidate_sets:
                    candidate_sets[other_channel].discard(i)

        assert self.validate_schedule(trans)
        return trans

    def validate_schedule(self, trans) -> bool:
        used_channels = []

        for node_id, channel_id in trans.items():
            if channel_id is None:
                continue

            if channel_id not in self.wavelengths:
                return False

            if node_id not in self.A[channel_id]:
                return False

            used_channels.append(channel_id)

        return len(used_channels) == len(set(used_channels))
