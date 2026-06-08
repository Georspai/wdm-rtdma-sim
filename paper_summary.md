# RTDMA Summary from `RTDMA-ALOHA.pdf`

## Scope

This summary covers the Random TDMA (RTDMA) portion of the paper, including the WDM passive-star system model, the RTDMA scheduling rule, the approximate analytical model, and the main performance conclusions. The ALOHA protocol is referenced only where it is needed for comparison.

## System Context

The paper studies a synchronous packet-switched WDM passive-star network with:

- `N` nodes interconnected by `W` wavelength channels.
- One tunable transmitter per node, with limited tuning range.
- Multiple fixed receivers per node.
- Finite per-node packet buffers.
- Nonhomogeneous node parameters, including buffer size, arrival probability, tuning range, and destination distribution.

For node `i`:

- `T_i` is the set of wavelengths its transmitter can tune to, with `|T_i| = t_i`.
- `R_i` is the set of wavelengths it can receive on, with `|R_i| = r_i`.
- `L_i` is its finite buffer capacity.
- `lambda_i` is its packet generation probability per slot.
- `d_im` is the probability that a packet generated at node `i` is destined to node `m`.

For wavelength `k`:

- `A_k = {n | k in T_n}` is the set of nodes that can transmit on channel `k`.
- `B_k = {m | k in R_m}` is the set of nodes that can receive on channel `k`.

The channel and receiver assignments are assumed to support single-hop communication: for every source-destination pair, the source can transmit on at least one wavelength that the destination can receive.

Time is slotted. In each slot, the order of events is:

1. Packet arrival.
2. Transmission attempt or scheduled transmission.
3. End of transmission.

The Markov chains used in the paper are embedded after arrivals and before transmission.

## RTDMA Protocol

RTDMA assigns collision-free transmit opportunities at the beginning of each slot. Each node has a slot schedule entry `trans[i]`:

- `trans[i] = k > 0` means node `i` is allowed to transmit on wavelength `k` in that slot.
- `trans[i] = 0` means node `i` is not scheduled in that slot.

If a busy node `i` is assigned channel `k`, it may transmit one packet to any destination in `B_k`. Unlike FIFO-only random access, RTDMA lets the node select any buffered packet whose destination can receive on the assigned channel. The transmission succeeds if at least one such packet exists in the buffer.

The paper constructs the per-slot transmission schedule as follows:

1. Initialize the set of unassigned channels as `Omega = {1, ..., W}` and copy each channel candidate set as `hat{A}_j = A_j`.
2. Randomly choose a remaining channel `k` from `Omega`.
3. Randomly choose a node `i` from `hat{A}_k`.
4. Set `trans[i] = k`.
5. Remove node `i` from every remaining candidate set `hat{A}_j`, and remove channel `k` from `Omega`.
6. Repeat until no channel remains.

This schedule has four important properties:

- Each wavelength is assigned to exactly one transmitting node per slot, so channel collisions are eliminated.
- Each node is assigned at most one wavelength per slot, respecting the single-transmitter constraint.
- A node is assigned only to a wavelength in its tuning range.
- The schedule can be generated independently by all nodes if they share the same random generator and seed, avoiding a pretransmission coordination channel.

## Why RTDMA Needs an Approximation

An exact RTDMA analysis would need to track not just the number of packets in a node buffer, but the destination of every buffered packet:

```text
(Y_1, ..., Y_{L_i})
```

where `Y_k = 0` means buffer position `k` is empty, and otherwise identifies the packet destination. This state space grows exponentially with buffer size and number of nodes.

The paper therefore approximates each node independently using only:

```text
X_i = number of packets in node i's buffer, 0 <= X_i <= L_i
```

Inter-node coupling is handled through average channel-assignment and success probabilities rather than a full joint state distribution.

## Markov Model

For each node `i`, the model defines a discrete-time Markov chain with transition matrix `P^(i)`. Let:

```math
\Pi^{(i)} P^{(i)} = \Pi^{(i)}, \qquad
\sum_{j=0}^{L_i} \Pi_j^{(i)} = 1
```

where `Pi_j^(i)` is the steady-state probability that node `i` has `j` packets at the embedded slot boundary.

The RTDMA success probability is state dependent. Let:

```math
S_j^{(i)} =
\Pr\{\text{node } i \text{ successfully transmits} \mid X_i = j\}
```

Then define the state-dependent birth and death probabilities:

```math
\beta_j^{(i)} = \lambda_i (1 - S_j^{(i)}), \qquad
\sigma_j^{(i)} = S_j^{(i)} (1 - \lambda_i)
```

The transition probabilities are:

```math
P_{jk}^{(i)} =
\begin{cases}
1 - \lambda_i, & j = k = 0 \\
\lambda_i, & j = 0,\ k = 1 \\
\sigma_j^{(i)}, & 0 < j \le L_i,\ k = j - 1 \\
1 - \beta_j^{(i)} - \sigma_j^{(i)}, & 0 < j < L_i,\ k = j \\
\beta_j^{(i)}, & 0 < j < L_i,\ k = j + 1 \\
1 - \sigma_j^{(i)}, & j = k = L_i \\
0, & \text{otherwise}
\end{cases}
```

The key distinction from slotted ALOHA is that RTDMA's `S_j^(i)` depends on both the node and the number of packets in its buffer. A node with more packets has a higher probability of having at least one packet whose destination is reachable through the scheduled wavelength.

## RTDMA Success Probability

Assume channel `k` has been assigned to node `i`. Define:

```math
\Delta_k^{(i)} = \sum_{m \in B_k} d_{im}
```

This is the probability that a randomly chosen packet at node `i` is destined to a node that can receive on channel `k`.

With `j` packets in the buffer, the probability that at least one packet can be transmitted on channel `k` is:

```math
1 - (1 - \Delta_k^{(i)})^j
```

Let:

```math
\alpha_k^{(i)}
```

be the probability that channel `k` is assigned to node `i` in a slot. The state-dependent success probability is:

```math
S_j^{(i)} =
\sum_{k=1}^{W}
\alpha_k^{(i)}
\left[1 - (1 - \Delta_k^{(i)})^j\right]
```

This expression captures the two conditions required for success:

- Node `i` must be scheduled on a channel `k`.
- Its buffer must contain at least one packet destined to a receiver on `k`.

## Channel-Assignment Approximation

The exact computation of `alpha_k^(i)` is combinatorial because of asymmetric tuning sets and because assigning one node removes it from consideration for other channels in the same slot.

The paper proposes a normalized approximation based on transmitter tunability. It assumes that the probability of assigning channel `k` to node `i`:

- decreases as node `i`'s tuning range `t_i` increases,
- increases as the tuning ranges of competing nodes in `A_k` increase.

The approximation is:

```math
\alpha_k^{(i)}
= C \frac{\prod_{j \in A_k,\ j \ne i} t_j}{t_i}
```

where `C` normalizes the assignment probabilities for channel `k`:

```math
\sum_{i \in A_k} \alpha_k^{(i)} = 1
```

Thus:

```math
C =
\left[
\sum_{i \in A_k}
\frac{\prod_{j \in A_k,\ j \ne i} t_j}{t_i}
\right]^{-1}
```

After computing `alpha_k^(i)`, the model computes `S_j^(i)`, fills `P^(i)`, solves the steady-state equations, and iterates until convergence.

## Performance Metrics

Once the steady-state vector is known, the node throughput under RTDMA is:

```math
TP_i =
\sum_{j=1}^{L_i}
\Pi_j^{(i)} S_j^{(i)}
```

The total system throughput is:

```math
TP = \sum_{i=1}^{N} TP_i
```

The average queue length at node `i` is:

```math
Q_i =
\sum_{j=0}^{L_i}
j \Pi_j^{(i)}
```

Using Little's theorem, the average packet delay at node `i` is:

```math
D_i = \frac{Q_i}{TP_i}
```

These metrics let the model compare hardware configurations and protocol choices without simulating the complete destination-level buffer state.

## Validation and Results

The paper validates the approximate model against detailed simulation for an `N = 8`, `W = 4` system with finite buffers and nonuniform traffic. The RTDMA validation uses the configuration where each transmitter can tune to all four wavelengths and each node has one fixed receiver assigned to one wavelength. Each simulation is run for 1,000,000 slots.

For the reported cases, the approximation error is:

- at most about 5% for node throughput,
- at most about 10% for average node delay.

The performance comparison shows:

- Slotted ALOHA has lower delay at light load because it does not impose a fixed schedule wait when contention is low.
- RTDMA has lower delay at moderate to high load because it avoids collisions and uses the scheduled channel opportunity to transmit any compatible packet in the buffer.
- Hardware configuration strongly affects RTDMA delay. The best reported performance occurs when every node can receive on every wavelength, reducing competition and improving scheduling efficiency.
- When every transmitter can tune to all wavelengths but each node has only one receiver, the TDMA frame effect is larger because more nodes compete for each wavelength, increasing delay.

## Engineering Interpretation

RTDMA is well suited to high-speed WDM packet networks where pretransmission coordination is expensive relative to packet time. Its core engineering tradeoff is deterministic collision avoidance versus scheduling delay:

- At low load, scheduled access can be inefficient because nodes may wait despite little contention.
- At higher load, eliminating collisions dominates, and RTDMA improves delay and throughput behavior.

The protocol also exploits buffer diversity. Because a scheduled node can choose any packet compatible with the assigned wavelength, larger buffers and broader destination diversity improve the chance that a scheduled slot carries useful traffic.

The analytical model is useful for design-space exploration because it includes finite buffers, asymmetric tuning ranges, receiver placement, and nonuniform traffic while avoiding the exponential state explosion of an exact model. Its main approximation risk is the independent per-node treatment and the heuristic channel-assignment probability `alpha_k^(i)`, but the paper's simulation comparison suggests that the error is acceptable for engineering-level evaluation in the studied cases.
