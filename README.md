# ❄️ Agent-Based Simulation of Campus Pedestrian Movement Network Under Winter Conditions

> **An agent-based model exploring how decentralized pedestrian decisions and snow-plow strategies shape emergent walkability patterns across a campus pedestrian movement network.**

---

## Why This Project Matters

Winter weather is one of the most disruptive yet under-studied factors affecting pedestrian mobility on college campuses and in urban environments. Poor snow management doesn't just slow people down — it creates cascading accessibility barriers that disproportionately affect individuals with disabilities, injuries, and time constraints. Yet decisions about where and when to plow are typically made with little empirical guidance, relying on institutional habit rather than data-driven strategy.

This project provides a **low-cost, zero-risk simulation framework** for answering questions that would be expensive or impractical to test in the real world: *Which roads should be cleared first? Does prioritizing high-traffic paths help or hurt overall campus mobility? How sensitive are outcomes to snow severity, pedestrian behavior, and plow allocation?* By modeling these dynamics computationally, campus planners and urban designers can **pre-test maintenance strategies, identify infrastructure bottlenecks, and optimize resource allocation** before committing to real-world changes.

Beyond the immediate campus application, the model demonstrates a generalizable methodology: **any pedestrian network** — a university, a hospital complex, a city district — can be imported as a node-link graph, parameterized with local data, and used to explore how individual movement decisions and institutional interventions interact to produce system-level outcomes. This makes the project a reusable research tool, not just a one-off simulation.

---

## Overview

CampusWalk is a spatially explicit agent-based model (ABM) built in **NetLogo 7.0** that simulates pedestrian route-choice behavior on a real campus pedestrian movement network under winter conditions. The model investigates a core question in complex systems research: **how do simple, local decisions made by individual agents produce complex system-level patterns — and how can institutional interventions reshape those patterns?**

Rather than imposing top-down equations to describe aggregate pedestrian flow, this model takes a bottom-up approach. Each pedestrian agent independently plans routes using Dijkstra's shortest-path algorithm, adapts to local snow conditions through probabilistic rerouting, and collectively generates emergent walkability patterns across the network. Snow-plow agents then introduce a second layer of complexity by following configurable clearing strategies, allowing the researcher to observe how maintenance interventions interact with organic pedestrian behavior.

The result is a rich simulation environment for studying the interplay between **individual adaptation**, **environmental constraints**, and **institutional strategy** — themes with broad relevance to urban planning, transportation research, and computational social science.

---

## Key Features

### Realistic Spatial Foundation
The model is built on a hand-crafted **node-link graph** overlaid on an actual campus map (Middlebury College). Building nodes are categorized by function (Academic, Dining, Residential, Other), with probabilistic origin-destination assignment reflecting real campus travel patterns. This grounding in real geography ensures that simulation results are spatially meaningful rather than abstract.

### Shortest-Path Routing with Adaptive Rerouting
Pedestrian agents compute optimal routes via a full implementation of **Dijkstra's algorithm** using a custom priority queue (`pqueue.nls`). The design rationale reflects domain knowledge: campus pedestrians, unlike urban tourists, possess near-complete knowledge of the road network. When snow degrades a road, agents probabilistically decide whether to abandon their shortest path in favor of a more walkable alternative — selecting the highest-walkability neighbor closest to their destination. This two-stage decision architecture captures the tension between optimality and adaptability that characterizes real pedestrian behavior.

### Dynamic Walkability Feedback Loop
A self-reinforcing feedback mechanism drives emergent pattern formation: each traversal of a road increments its walkability score, making it more attractive to future pedestrians. Under snow conditions, roads with walkability exceeding a configurable threshold (`faster-threshold`) grant improved movement speed, creating **positive feedback loops** where popular paths become increasingly preferred. This mechanism produces realistic "desire path" formation without any explicit path-popularity rule.

### Configurable Snow-Plow Strategies
Two plow strategies are implemented and extensible:

| Strategy | Behavior | Rationale |
|---|---|---|
| `clean-more-walked` | Prioritizes clearing roads with higher walkability | Reinforces existing pedestrian patterns; reduces friction on popular routes |
| `clean-less-walked` | Prioritizes clearing roads with lower walkability | Distributes walkability more evenly; opens underused paths |

Plows are introduced at tick 2,000, after baseline pedestrian patterns have stabilized — a deliberate experimental design choice that allows clean measurement of intervention effects against an established baseline.

### Systematic Experimentation via BehaviorSpace
The repository includes a full **BehaviorSpace experiment** (`plow-strategy-effectiveness`) testing both strategies across a parameter sweep of `speed-snow ∈ {1, 5}`, `speed-walkable-snow ∈ {5, 10}`, and `faster-threshold ∈ {10, 100, 500}`, with 5 replications per configuration (120 runs total). Results reveal that strategy effectiveness is **context-dependent**: `clean-more-walked` outperforms under high speed differentials with moderate thresholds, while `clean-less-walked` gains advantage under lighter snow conditions — a nuanced finding that resists simple policy prescriptions.

### Persistent Graph I/O
A custom file I/O system allows the node-link graph to be **saved and loaded** as structured text files, enabling reproducibility and collaborative extension. The serialization format preserves node positions, types, building classifications, link properties, and sequential ID tracking.

---

## Model Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Observer (Scheduler)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Pedestrians  │  │  Snow Plows   │  │    Nodes      │  │
│  │              │  │              │  │  (Building /  │  │
│  │ • Route plan │  │ • Strategy   │  │   Road)       │  │
│  │ • Reroute    │  │ • Snow clear │  │              │  │
│  │ • Adaptive   │  │ • Path       │  │ • Origin /    │  │
│  │   speed      │  │   selection  │  │   Destination │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────┘  │
│         │                 │                              │
│         └────────┬────────┘                              │
│                  ▼                                       │
│         ┌────────────────┐                               │
│         │     Links      │                               │
│         │ • snow?        │                               │
│         │ • walkability  │                               │
│         │ • len (weight) │                               │
│         └────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**Agent Types:**
- **Nodes** — Static graph vertices representing buildings (with type classification) or road intersections. Serve as origins, destinations, and waypoints.
- **Pedestrians** — Mobile agents with shortest-path planning, probabilistic rerouting under snow, and speed adaptation based on road conditions.
- **Snow Plows** — Mobile agents following configurable clearing strategies, introduced post-stabilization to measure intervention effects.

---

## Technical Implementation Highlights

- **Dijkstra's Algorithm** — Full weighted shortest-path implementation with a custom priority queue (`pqueue.nls`), supporting efficient route computation across the campus graph.
- **Context-Aware Design** — Careful management of NetLogo's observer/agent context boundaries, particularly for invoking observer-context procedures (e.g., `shortest-path`) from within agent-context blocks — a non-trivial challenge documented in inline comments.
- **Modular Graph Construction** — Interactive tools for building, editing, saving, and loading node-link graphs, enabling iterative map refinement and reproducibility.
- **Parameterized Experimentation** — Full BehaviorSpace integration with systematic parameter sweeps, multi-run replication, and CSV export for downstream statistical analysis.

---

## Getting Started

### Prerequisites
- [NetLogo 7.0+](https://ccl.northwestern.edu/netlogo/download.shtml)

### Running the Model
1. Clone this repository.
2. Open `Term_Project.nlogox` in NetLogo.
3. Press **Setup** to import the campus map and graph.
4. Adjust parameters using the interface sliders and switches.
5. Press **Go** to run the simulation.

> ⚠️ **Note:** If you are importing your own graph with a custom background image, remember to adjust the size of the NetLogo world (under Settings → World) to match the resolution of your image. Mismatched dimensions will cause nodes to appear in incorrect positions.

### Key Parameters

| Parameter | Default | Description |
|---|---|---|
| `num-ped` | 100 | Number of pedestrian agents |
| `speed-ped` | 10 | Pedestrian speed on clear roads |
| `speed-snow` | 5 | Pedestrian speed on snowy roads |
| `speed-walkable-snow` | 7 | Speed on walked snowy roads (above threshold) |
| `reroute-p-when-snow` | 0.3 | Probability of rerouting when encountering snow |
| `faster-threshold` | 200 | Walkability score required for speed improvement |
| `num-plow` | 1 | Number of snow-plow agents |
| `speed-plow` | 15 | Plow movement speed |
| `plow-strategy` | — | `clean-more-walked` or `clean-less-walked` |

### Switches
- **snowed?** — Toggle winter conditions on/off
- **snow-plow?** — Enable/disable plow agents
- **show-walkability?** — Visualize relative walkability (darker = more walked)

---

## Experimentation: Ready for Real-World Data

### Included Demo Experiment
The repository includes a demonstration **BehaviorSpace experiment** (`plow-strategy-effectiveness`) as a proof of concept, testing both plow strategies across a parameter sweep of `speed-snow ∈ {1, 5}`, `speed-walkable-snow ∈ {5, 10}`, and `faster-threshold ∈ {10, 100, 500}`, with 5 replications per configuration (120 runs total). Even with synthetic parameters, the results reveal a meaningful insight: **no single plow strategy universally dominates** — effectiveness is context-dependent, varying with snow severity and walkability thresholds. This demonstrates the model's capacity to surface non-obvious, nuanced findings.

### What Real-World Experiments Could Look Like
The model is architected to be **experiment-ready**. With real-world data incorporated, researchers and campus planners could run studies such as:

- **Optimal plow fleet sizing** — How many plows are needed to keep average walking time below a target threshold? At what point do additional plows yield diminishing returns?
- **Building-specific accessibility analysis** — Which buildings become disproportionately harder to reach under snow? Are dining halls or disability services offices on poorly maintained routes?
- **Peak-hour impact studies** — By incorporating time-of-day origin-destination distributions (e.g., class schedules, meal times), how does snow affect the 8:50 AM rush versus midday traffic?
- **Multi-campus comparison** — Import different campus graphs to compare which campus layouts are inherently more resilient to winter disruption and why.
- **Strategy A/B testing** — Develop and compare custom plow strategies (e.g., priority-clearing routes to medical facilities, clearing perimeter roads first vs. core roads first) against baseline strategies.
- **Pedestrian behavior sensitivity** — How much does average walking time improve if the reroute probability increases (e.g., through better signage or real-time walkability information)?
- **Climate scenario modeling** — Test how varying snow severity levels (light dusting vs. heavy accumulation) change the relative effectiveness of different maintenance approaches.

The graph I/O system, BehaviorSpace integration, and modular strategy architecture make it straightforward to plug in real-world parameters — pedestrian counts from campus surveys, actual building coordinates from GIS data, measured walking speeds from field studies — and generate actionable insights.

---

## Repository Structure

```
├── Term_Project.nlogox              # Main NetLogo model file
├── campus_map.png                   # Campus map background image
├── complete-graph                   # Serialized node-link graph
├── pqueue.nls                       # Priority queue implementation (included source)
├── plow-strategy-effectiveness.csv  # BehaviorSpace experiment results (120 runs)
└── README.md
```

---

## Extending the Model

The model is designed for extensibility:

- **New plow strategies** can be added directly to the `move-plow` procedure and registered in the interface chooser.
- **Time-of-day logic** — Origin/destination distributions could vary by hour to reflect class schedules and meal times.
- **Continuous snowfall** — Currently the model simulates a post-snowfall state; active snowfall (roads re-snowing after clearing) would add temporal dynamics.
- **Heterogeneous agents** — Varying pedestrian speeds, risk preferences, or physical abilities would enable equity-focused analysis.

---

## Responsible Computing

This model is a simplified representation of a complex socio-spatial system. While it provides valuable insights into how local decisions and institutional interventions interact, users should recognize key simplifying assumptions: homogeneous agents, perfect shortest-path knowledge, fixed pedestrian populations, and abstracted road geometry. The model is intended as an exploratory and educational tool — not a basis for direct policy implementation without validation against empirical data.

---

## References

- Jin, L., Lu, W., & Sun, P. (2022). Preference for street environment based on route choice behavior while walking. *Frontiers in Public Health*, 10, 880251.
- Fossum, M., & Ryeng, E. O. (2022). Pedestrians' and bicyclists' route choice during winter conditions. *Urban, Planning and Transport Research*, 10(1), 38–57.
- Liang, S., et al. (2020). How does weather and climate affect pedestrian walking speed during cool and cold seasons in severely cold areas? *Building and Environment*, 175, 106811.
- Ma, L., et al. (2024). Simple agents–complex emergent path systems. *Environment and Planning B*, 51(2), 479–495.

---

## Author

**Zijing Guo**

Built as a term project exploring agent-based modeling, complex systems, and computational approaches to spatial analysis.
