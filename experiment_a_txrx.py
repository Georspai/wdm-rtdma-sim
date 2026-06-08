"""Experiment A: Tx/Rx flexibility sweep.

Sweeps rho_T x rho_R over {0.25, 0.5, 0.75, 1.0}^2 = 16 combos.
Produces 2D heatmaps for throughput, avg_delay, waste_ratio,
incompatible_waste_ratio, and drop_rate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from SimulatorConfig import SimulatorConfig
from Simulator import Simulator

RATIOS = [0.25, 0.5, 0.75, 1.0]
N_RATIOS = len(RATIOS)

NUM_NODES = 16
NUM_WAVELENGTHS = 4
BUFFER_SIZE = 16
ARRIVAL_PROB = 0.08
NUM_SLOTS = 100_000
SEED = 42


def run_simulation(rho_t, rho_r):
    config = SimulatorConfig(
        num_time_slots=NUM_SLOTS,
        num_nodes=NUM_NODES,
        num_wavelengths=NUM_WAVELENGTHS,
        buffer_sizes=BUFFER_SIZE,
        buffer_policies="fifo-compatible",
        arrival_probabilities=ARRIVAL_PROB,
        tx_channel_ratios=rho_t,
        rx_channel_ratios=rho_r,
        tx_assignment_policy="random",
        rx_assignment_policy="random",
        destination_policy="uniform",
        seed=SEED,
        require_full_connectivity=False,
        channel_assignment_attempts=1000,
    )
    sim = Simulator(config=config)
    metrics = sim.run()
    return metrics.summarize()


def main():
    metric_names = ["throughput", "avg_delay", "waste_ratio",
                    "incompatible_waste_ratio", "drop_rate"]
    grids = {name: np.zeros((N_RATIOS, N_RATIOS)) for name in metric_names}

    total = N_RATIOS * N_RATIOS
    run_num = 0

    for i, rho_t in enumerate(RATIOS):
        for j, rho_r in enumerate(RATIOS):
            run_num += 1
            print(f"[{run_num}/{total}] rho_T={rho_t}, rho_R={rho_r}")
            s = run_simulation(rho_t, rho_r)
            for name in metric_names:
                grids[name][i, j] = s[name]

    # --- Plot heatmaps ---
    fig, axes = plt.subplots(1, 5, figsize=(26, 5))
    titles = ["Throughput (pkt/slot)", "Avg Delay (slots)", "Waste Ratio",
              "Incompatible Waste Ratio", "Drop Rate"]
    cmaps = ["YlGn", "YlOrRd", "YlOrRd", "YlOrRd", "YlOrRd"]

    for ax, name, title, cmap in zip(axes, metric_names, titles, cmaps):
        data = grids[name]
        im = ax.imshow(data, origin="lower", cmap=cmap, aspect="equal")
        ax.set_xticks(range(N_RATIOS))
        ax.set_xticklabels([str(r) for r in RATIOS])
        ax.set_yticks(range(N_RATIOS))
        ax.set_yticklabels([str(r) for r in RATIOS])
        ax.set_xlabel(r"$\rho_R$")
        ax.set_ylabel(r"$\rho_T$")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        # Annotate cells
        for ii in range(N_RATIOS):
            for jj in range(N_RATIOS):
                val = data[ii, jj]
                ax.text(jj, ii, f"{val:.3f}", ha="center", va="center",
                        fontsize=7, color="black")

    fig.suptitle(f"Experiment A: Tx/Rx Flexibility Sweep (N={NUM_NODES}, W={NUM_WAVELENGTHS}, "
                 f"L={BUFFER_SIZE}, lambda={ARRIVAL_PROB})", fontsize=12)
    plt.tight_layout()
    out_path = Path(__file__).resolve().parent / "experiment_a_results.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
