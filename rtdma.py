import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from SimulatorConfig import SimulatorConfig
from Simulator import Simulator, SimulationMetrics


# --- Configuration ---
# Either load from a JSON file:
#   config = SimulatorConfig.from_json("config.json")
# Or define inline:
# config = SimulatorConfig(
#     num_time_slots=1000,
#     num_nodes=4,
#     num_wavelengths=2,
#     buffer_sizes=10,
#     buffer_policies="fifo-compatible",
#     arrival_probabilities=0.3,
#     tx_channel_ratios=1.0,
#     rx_channel_ratios=1.0,
#     tx_assignment_policy="all",
#     rx_assignment_policy="all",
#     destination_policy="uniform",
#     seed=42,
# )

config = SimulatorConfig.from_json("config.json")


def print_metrics(metrics: SimulationMetrics) -> None:
    s = metrics.summarize()

    print("=== Global Metrics ===")
    print(f"  Packets generated:      {metrics.packets_generated}")
    print(f"  Packets dropped:        {metrics.packets_dropped}")
    print(f"  Packets transmitted:    {metrics.packets_transmitted}")
    print(f"  Scheduled opportunities:{metrics.scheduled_opportunities}")
    print(f"  Wasted slots:           {metrics.wasted_slots}")
    print(f"  Drop rate:              {s['drop_rate']:.4f}")
    print(f"  Waste ratio:            {s['waste_ratio']:.4f}")
    print(f"  Channel utilization:    {s['channel_utilization']:.4f}")
    print(f"  Throughput (pkt/slot):  {s['throughput']:.4f}")

    print("\n=== Delay Statistics ===")
    print(f"  Average:  {s['avg_delay']:.2f}")
    print(f"  Median:   {s['p50_delay']}")
    print(f"  P95:      {s['p95_delay']}")
    print(f"  P99:      {s['p99_delay']}")
    print(f"  Max:      {s['max_delay']}")

    print("\n=== Per-Node Throughput ===")
    for i, tp in enumerate(s["node_throughput"]):
        print(f"  Node {i}: {tp:.4f} pkt/slot")

    print("\n=== Per-Wavelength Utilization ===")
    for k, util in enumerate(s["wavelength_utilization"]):
        print(f"  Channel {k}: {util:.4f}")

    print("\n=== Average Queue Length (per node) ===")
    for i, ql in enumerate(s["avg_queue_length"]):
        print(f"  Node {i}: {ql:.2f}")


if __name__ == "__main__":
    sim = Simulator(config=config)
    metrics = sim.run()
    print_metrics(metrics)
