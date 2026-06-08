"""Experiment C: Hotspot vs uniform traffic.

Compares uniform, hotspot p=0.6, and hotspot p=0.8 scenarios.
Produces a 6-subplot figure with grouped bars and a metrics table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from SimulatorConfig import SimulatorConfig
from Simulator import Simulator

NUM_NODES = 16
NUM_WAVELENGTHS = 4
BUFFER_SIZE = 16
RHO_T = 1.0
RHO_R = 0.25
ARRIVAL_PROB = 0.08
NUM_SLOTS = 100_000
SEED = 42
HOTSPOT_NODE = 0

SCENARIOS = [
    {"label": "Uniform", "policy": "uniform", "hotspot_prob": 0.0},
    {"label": "Hotspot p=0.6", "policy": "hotspot", "hotspot_prob": 0.6},
    {"label": "Hotspot p=0.8", "policy": "hotspot", "hotspot_prob": 0.8},
]


def run_simulation(policy, hotspot_prob):
    config = SimulatorConfig(
        num_time_slots=NUM_SLOTS,
        num_nodes=NUM_NODES,
        num_wavelengths=NUM_WAVELENGTHS,
        buffer_sizes=BUFFER_SIZE,
        buffer_policies="fifo-compatible",
        arrival_probabilities=ARRIVAL_PROB,
        tx_channel_ratios=RHO_T,
        rx_channel_ratios=RHO_R,
        tx_assignment_policy="round-robin",
        rx_assignment_policy="round-robin",
        destination_policy=policy,
        hotspot_node=HOTSPOT_NODE,
        hotspot_probability=hotspot_prob,
        seed=SEED,
        require_full_connectivity=True,
        channel_assignment_attempts=100,
    )
    sim = Simulator(config=config)
    metrics = sim.run()
    return metrics.summarize()


def main():
    results = []
    for idx, sc in enumerate(SCENARIOS):
        print(f"[{idx + 1}/{len(SCENARIOS)}] {sc['label']}")
        s = run_simulation(sc["policy"], sc["hotspot_prob"])
        results.append(s)

    labels = [sc["label"] for sc in SCENARIOS]
    n_scenarios = len(SCENARIOS)
    colors = ["tab:blue", "tab:orange", "tab:red"]

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Throughput grouped bars
    ax = axes[0, 0]
    x = np.arange(n_scenarios)
    vals = [r["throughput"] for r in results]
    bars = ax.bar(x, vals, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Throughput (pkt/slot)")
    ax.set_title("Throughput")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{v:.4f}", ha="center", va="bottom", fontsize=7)

    # 2. Avg delay grouped bars
    ax = axes[0, 1]
    vals = [r["avg_delay"] for r in results]
    bars = ax.bar(x, vals, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Avg Delay (slots)")
    ax.set_title("Average Delay")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{v:.2f}", ha="center", va="bottom", fontsize=7)

    # 3. Drop rate + waste ratio grouped bars
    ax = axes[0, 2]
    width = 0.35
    x2 = np.arange(n_scenarios)
    drop_vals = [r["drop_rate"] for r in results]
    waste_vals = [r["waste_ratio"] for r in results]
    bars1 = ax.bar(x2 - width / 2, drop_vals, width, label="Drop Rate", color="tab:red")
    bars2 = ax.bar(x2 + width / 2, waste_vals, width, label="Waste Ratio", color="tab:gray")
    ax.set_xticks(x2)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Ratio")
    ax.set_title("Drop Rate & Waste Ratio")
    ax.legend(fontsize=7)
    for bar, v in zip(bars1, drop_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{v:.4f}", ha="center", va="bottom", fontsize=6)
    for bar, v in zip(bars2, waste_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{v:.4f}", ha="center", va="bottom", fontsize=6)

    # 4. Per-wavelength utilization
    ax = axes[1, 0]
    x_ch = np.arange(NUM_WAVELENGTHS)
    width_ch = 0.8 / n_scenarios
    for i, (r, label, color) in enumerate(zip(results, labels, colors)):
        offsets = x_ch + (i - n_scenarios / 2 + 0.5) * width_ch
        ax.bar(offsets, r["wavelength_utilization"], width_ch, label=label, color=color)
    ax.set_xticks(x_ch)
    ax.set_xticklabels([f"Ch {k}" for k in range(NUM_WAVELENGTHS)])
    ax.set_ylabel("Utilization")
    ax.set_title("Per-Wavelength Utilization")
    ax.legend(fontsize=7)

    # 5. Per-destination received packets
    ax = axes[1, 1]
    x_dst = np.arange(NUM_NODES)
    width_dst = 0.8 / n_scenarios
    for i, (r, label, color) in enumerate(zip(results, labels, colors)):
        offsets = x_dst + (i - n_scenarios / 2 + 0.5) * width_dst
        ax.bar(offsets, r["destination_received"], width_dst, label=label, color=color)
    ax.set_xticks(x_dst)
    ax.set_xticklabels([str(d) for d in range(NUM_NODES)], fontsize=6)
    ax.set_xlabel("Destination Node")
    ax.set_ylabel("Packets Received")
    ax.set_title("Per-Destination Received Packets")
    ax.legend(fontsize=7)

    # 6. Scalar metrics comparison table
    ax = axes[1, 2]
    ax.axis("off")
    row_labels = ["Throughput", "Avg Delay", "Drop Rate", "Waste Ratio",
                  "Empty Waste", "Incompat Waste", "P95 Delay", "Max Delay"]
    table_data = []
    for r in results:
        table_data.append([
            f"{r['throughput']:.4f}",
            f"{r['avg_delay']:.2f}",
            f"{r['drop_rate']:.4f}",
            f"{r['waste_ratio']:.4f}",
            f"{r['empty_waste_ratio']:.4f}",
            f"{r['incompatible_waste_ratio']:.4f}",
            f"{r['p95_delay']}",
            f"{r['max_delay']}",
        ])
    # Transpose: rows = metrics, columns = scenarios
    cell_text = [[table_data[j][i] for j in range(n_scenarios)] for i in range(len(row_labels))]
    table = ax.table(cellText=cell_text, rowLabels=row_labels, colLabels=labels,
                     loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1.0, 1.3)
    ax.set_title("Metrics Comparison", pad=20)

    fig.suptitle(f"Experiment C: Hotspot vs Uniform (N={NUM_NODES}, W={NUM_WAVELENGTHS}, "
                 f"L={BUFFER_SIZE}, rho_T={RHO_T}, rho_R={RHO_R}, lambda={ARRIVAL_PROB})",
                 fontsize=12)
    plt.tight_layout()
    out_path = Path(__file__).resolve().parent / "experiment_c_results.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
