import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from SimulatorConfig import SimulatorConfig
from Simulator import Simulator

import matplotlib.pyplot as plt

# --- Custom channel assignments for each system (8 nodes, 4 wavelengths) ---
# Each system defines tx and rx sets that guarantee full connectivity.

SYSTEMS = [
    {
        "name": "System 1 (tx=0.5, rx=0.5)",
        "tx_sets": {
            0: {0, 1}, 1: {0, 1}, 2: {0, 1},
            3: {1, 2}, 4: {1, 2}, 5: {1, 2},
            6: {2, 3}, 7: {2, 3},
        },
        "rx_sets": {
            0: {1, 2}, 1: {1, 3}, 2: {1, 3},
            3: {0, 2}, 4: {1, 3}, 5: {0, 2},
            6: {1, 3}, 7: {0, 2},
        },
    },
    {
        "name": "System 2 (tx=0.25, rx=1.0)",
        "tx_sets": {
            0: {0}, 1: {1}, 2: {2}, 3: {3},
            4: {0}, 5: {1}, 6: {2}, 7: {3},
        },
        "rx_sets": {i: {0, 1, 2, 3} for i in range(8)},
    },
    {
        "name": "System 3 (tx=1.0, rx=0.25)",
        "tx_sets": {i: {0, 1, 2, 3} for i in range(8)},
        "rx_sets": {
            0: {0}, 1: {1}, 2: {2}, 3: {3},
            4: {0}, 5: {1}, 6: {2}, 7: {3},
        },
    },
]

ARRIVAL_PROBS = [0.0125, 0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60 , 0.65 , 0.7]


def build_simulator(arrival_prob, tx_sets, rx_sets):
    """Build a Simulator with custom channel assignments.

    Constructs with policy='all' so assignment always succeeds,
    then overrides tx/rx sets, rebuilds channel maps, and recreates nodes.
    """
    config = SimulatorConfig(
        num_time_slots=1_000_000,
        num_nodes=8,
        num_wavelengths=4,
        buffer_sizes=4,
        buffer_policies="fifo-compatible",
        arrival_probabilities=arrival_prob,
        tx_channel_ratios=1.0,
        rx_channel_ratios=1.0,
        tx_assignment_policy="all",
        rx_assignment_policy="all",
        destination_policy="uniform",
        seed=42,
        require_full_connectivity=True,
        channel_assignment_attempts=100,
    )
    sim = Simulator(config=config)

    # Override with custom channel assignments
    sim.tx_sets = tx_sets
    sim.rx_sets = rx_sets
    sim.build_channel_sets()
    sim.scheduler.A = sim.A
    sim.nodes = []
    sim.create_nodes()

    return sim


def main():
    results = {s["name"]: {"throughput": [], "avg_delay": []} for s in SYSTEMS}

    total = len(SYSTEMS) * len(ARRIVAL_PROBS)
    run_num = 0

    for system in SYSTEMS:
        for prob in ARRIVAL_PROBS:
            run_num += 1
            print(f"[{run_num}/{total}] {system['name']}  arrival_prob={prob}")

            sim = build_simulator(prob, system["tx_sets"], system["rx_sets"])
            metrics = sim.run()
            s = metrics.summarize()

            results[system["name"]]["throughput"].append(s["throughput"])
            results[system["name"]]["avg_delay"].append(s["avg_delay"])

    # --- Plot: Throughput vs Average Delay ---
    markers = ["o", "s", "^"]
    colors = ["tab:blue", "tab:orange", "tab:green"]

    plt.figure(figsize=(9, 6))
    for i, system in enumerate(SYSTEMS):
        data = results[system["name"]]
        plt.plot(
            data["throughput"],
            data["avg_delay"],
            marker=markers[i],
            color=colors[i],
            label=system["name"],
        )

    plt.xlabel("Throughput (pkt/slot)")
    plt.ylabel("Average Delay (slots)")
    plt.title("RTDMA: Throughput vs Average Delay")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("sweep_results.png", dpi=150)
    print("Saved sweep_results.png")
    plt.show()


if __name__ == "__main__":
    main()
