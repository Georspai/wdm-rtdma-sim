"""Experiment B: Buffer size sweep.

Sweeps L in {1, 2, 4, 8, 16, 32, 64}.
Produces line plots (log-2 x-axis) for drop_rate, avg_delay, p95_delay,
avg_queue_length (averaged across nodes), and throughput.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from SimulatorConfig import SimulatorConfig
from Simulator import Simulator

BUFFER_SIZES = [1, 2, 4, 8, 16, 32, 64]

NUM_NODES = 16
NUM_WAVELENGTHS = 4
RHO_T = 1.0
RHO_R = 0.25
ARRIVAL_PROB = 0.12
NUM_SLOTS = 100_000
SEED = 42


def run_simulation(buffer_size):
    config = SimulatorConfig(
        num_time_slots=NUM_SLOTS,
        num_nodes=NUM_NODES,
        num_wavelengths=NUM_WAVELENGTHS,
        buffer_sizes=buffer_size,
        buffer_policies="fifo-compatible",
        arrival_probabilities=ARRIVAL_PROB,
        tx_channel_ratios=RHO_T,
        rx_channel_ratios=RHO_R,
        tx_assignment_policy="round-robin",
        rx_assignment_policy="round-robin",
        destination_policy="uniform",
        seed=SEED,
        require_full_connectivity=True,
        channel_assignment_attempts=100,
    )
    sim = Simulator(config=config)
    metrics = sim.run()
    return metrics.summarize()


def main():
    drop_rates = []
    avg_delays = []
    p95_delays = []
    avg_queue_lengths = []
    throughputs = []

    total = len(BUFFER_SIZES)
    for idx, L in enumerate(BUFFER_SIZES):
        print(f"[{idx + 1}/{total}] L={L}")
        s = run_simulation(L)
        drop_rates.append(s["drop_rate"])
        avg_delays.append(s["avg_delay"])
        p95_delays.append(s["p95_delay"])
        avg_queue_lengths.append(np.mean(s["avg_queue_length"]))
        throughputs.append(s["throughput"])

    x = np.log2(BUFFER_SIZES)
    x_labels = [str(b) for b in BUFFER_SIZES]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))

    # Drop rate
    ax = axes[0, 0]
    ax.plot(x, drop_rates, "o-", color="tab:red")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Buffer Size L")
    ax.set_ylabel("Drop Rate")
    ax.set_title("Drop Rate vs Buffer Size")
    ax.grid(True)

    # Avg delay
    ax = axes[0, 1]
    ax.plot(x, avg_delays, "s-", color="tab:blue")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Buffer Size L")
    ax.set_ylabel("Avg Delay (slots)")
    ax.set_title("Average Delay vs Buffer Size")
    ax.grid(True)

    # P95 delay
    ax = axes[0, 2]
    ax.plot(x, p95_delays, "^-", color="tab:purple")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Buffer Size L")
    ax.set_ylabel("P95 Delay (slots)")
    ax.set_title("P95 Delay vs Buffer Size")
    ax.grid(True)

    # Avg queue length
    ax = axes[1, 0]
    ax.plot(x, avg_queue_lengths, "D-", color="tab:orange")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Buffer Size L")
    ax.set_ylabel("Avg Queue Length")
    ax.set_title("Avg Queue Length vs Buffer Size")
    ax.grid(True)

    # Throughput
    ax = axes[1, 1]
    ax.plot(x, throughputs, "v-", color="tab:green")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Buffer Size L")
    ax.set_ylabel("Throughput (pkt/slot)")
    ax.set_title("Throughput vs Buffer Size")
    ax.grid(True)

    # Remove empty subplot
    axes[1, 2].axis("off")

    fig.suptitle(f"Experiment B: Buffer Size Sweep (N={NUM_NODES}, W={NUM_WAVELENGTHS}, "
                 f"rho_T={RHO_T}, rho_R={RHO_R}, lambda={ARRIVAL_PROB})", fontsize=12)
    plt.tight_layout()
    out_path = Path(__file__).resolve().parent / "experiment_b_results.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
