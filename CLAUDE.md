# CLAUDE.md

Context for Claude Code sessions working on this repository.

## Project

Agent-based simulation of campus pedestrian movement under winter (snow) conditions. Originally authored in NetLogo by Zijing Guo; now being extended into a research project that combines the ABM with an LLM/VLM decision loop.

Upstream NetLogo repo: https://github.com/JamesGuo111/Agent-Based-Simulation-of-Campus-Pedestrian-Movement-Network-Under-Winter-Conditions

## Research Goal

Extend the existing ABM into a **vision-grounded LLM/VLM decision framework**. The core idea:

1. The simulation maintains a node–link graph of the campus with dynamic per-edge attributes — most importantly `walkability` (how well-trodden a path is) and `snow` (whether it is snowed over), plus `length`.
2. At decision points, the current state of the graph is **rendered as an image** (edges colored / styled by their attributes; pedestrians, plows, and buildings visualized) rather than being handed to the model as raw numbers.
3. A **VLM consumes the rendered image** and makes a decision — e.g. which road to plow next, which route a pedestrian should take, or higher-level policy choices — as if it were a human observer looking at a map.
4. The simulation applies the decision, advances, re-renders, and loops.

Questions the research aims to probe (to be deepened in later conversations):

- Can a VLM match or beat hand-crafted heuristics (e.g. `clean-more-walked` vs `clean-less-walked` plow strategies) when it only sees the visual state?
- Does the visual modality surface emergent patterns (desire lines, bottlenecks) more readably than tabular features?
- How sensitive are decisions to rendering choices (color scale for walkability, symbol for snow, etc.)?

## Current State

The NetLogo model has been ported to Python + Pygame. The port is complete and tested; the LLM/VLM integration has **not** been started.

**Ported modules** (all under [src/](src/)):
- [graph.py](src/graph.py) — `Node`, `Link`, and `Graph` with NetLogo `complete-graph` parser and Dijkstra shortest path (`heapq` replacing `pqueue.nls`). Link attributes: `snow: bool`, `walkability: int`, `length: float`.
- [agents.py](src/agents.py) — `Pedestrian` and `Plow` classes.
- [simulation.py](src/simulation.py) — generation, movement, stochastic rerouting under snow, plow strategies.
- [visualization.py](src/visualization.py) — Pygame real-time renderer on top of `campus_map.png`.
- [main.py](src/main.py) — CLI entry, 14 parameters including `--snowed`, `--snow-plow`, `--plow-strategy`.

**Tests** ([tests/](tests/)): 27 tests across `test_graph.py`, `test_simulation.py`, `test_e2e.py`.

**Original NetLogo artifacts** are kept in the repo root for reference: `Pedestrian Movement ABM under Winter Condition.nlogox`, `pqueue.nls`, `complete-graph`, `campus_map.png`, and the BehaviorSpace CSV.

## Working Branch

`claude/cool-jepsen-fb5714` tracks `origin/python-llm-migration` — i.e. all LLM-integration work should land on this branch line, not on `main` (which still reflects the NetLogo-only state).

## Conventions

- Respect the existing graph format and NetLogo parameter names (`walkability`, `snow`, `faster-threshold`, etc.) — they are the contract with the original model.
- Tests are run with `pytest` from the repo root.
- The simulation entry point is `python -m src.main` with CLI flags.

## Collaboration Notes

- The research direction is staged. Do not jump ahead to rendering-for-VLM, prompt design, or evaluation before the immediate step has been settled with the user.
- When extending the simulation, preserve the ability to run it headless (no Pygame window) — that will be needed for batched VLM experiments later.
