# NetLogo-to-Python Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strictly port the existing NetLogo pedestrian movement ABM to Python + Pygame, preserving all simulation logic and real-time visualization.

**Architecture:** Single Python package with four modules: graph (data model), agents (pedestrian + plow logic), simulation (tick loop + parameter management), and visualization (Pygame renderer). The graph file parser reads the existing `complete-graph` file. All agent decision logic is ported line-by-line from the NetLogo code.

**Tech Stack:** Python 3.11+, Pygame 2.x, heapq (stdlib)

---

## File Structure

```
src/
  __init__.py
  graph.py          — Node, Link, Graph classes; complete-graph parser
  agents.py         — Pedestrian, Plow classes with all decision logic
  simulation.py     — SimulationEngine: tick loop, agent generation, parameter management
  visualization.py  — PygameRenderer: drawing, UI controls (sliders/switches)
  main.py           — Entry point: parse args, wire everything, run
```

Supporting files (already exist, not modified):
- `campus_map.png` — background image
- `complete-graph` — node-link graph data

---

### Task 1: Graph Data Model and Parser

**Files:**
- Create: `src/__init__.py`
- Create: `src/graph.py`
- Create: `tests/test_graph.py`

This task builds the Node, Link, and Graph classes, plus the parser for the `complete-graph` file format.

- [ ] **Step 1: Create empty package**

```bash
mkdir -p src tests
touch src/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write test for graph parser**

```python
# tests/test_graph.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import Graph

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')

def test_load_node_count():
    g = Graph()
    g.load(GRAPH_FILE)
    assert len(g.nodes) == 193  # node IDs 0..192, but some IDs may be missing

def test_load_building_nodes():
    g = Graph()
    g.load(GRAPH_FILE)
    buildings = [n for n in g.nodes.values() if n.node_type == "building"]
    assert len(buildings) == 56

def test_load_road_nodes():
    g = Graph()
    g.load(GRAPH_FILE)
    roads = [n for n in g.nodes.values() if n.node_type == "road"]
    assert len(roads) == 135

def test_load_link_count():
    g = Graph()
    g.load(GRAPH_FILE)
    assert len(g.links) == 287

def test_node_attributes():
    g = Graph()
    g.load(GRAPH_FILE)
    n0 = g.nodes[0]
    assert n0.x == 101
    assert n0.y == 1484
    assert n0.node_type == "building"
    assert n0.building_type == "Academic"

def test_link_attributes():
    g = Graph()
    g.load(GRAPH_FILE)
    # Link between node 0 and 55
    link = g.get_link(0, 55)
    assert link is not None
    assert abs(link.length - 72.2496) < 0.01
    assert link.snow == False
    assert link.walkability == 0

def test_node_neighbors():
    g = Graph()
    g.load(GRAPH_FILE)
    # Node 0 connects to 55 and 57
    nbr_ids = {n.node_id for n in g.get_neighbors(0)}
    assert nbr_ids == {55, 57}

if __name__ == "__main__":
    test_load_node_count()
    test_load_building_nodes()
    test_load_road_nodes()
    test_load_link_count()
    test_node_attributes()
    test_link_attributes()
    test_node_neighbors()
    print("All graph tests passed.")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_graph.py -v`
Expected: FAIL (no module `src.graph`)

- [ ] **Step 4: Implement graph.py**

```python
# src/graph.py
import math
import ast

class Node:
    __slots__ = ['node_id', 'x', 'y', 'node_type', 'building_type', 'neighbors', 'links']

    def __init__(self, node_id, x, y, node_type, building_type):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.node_type = node_type
        self.building_type = building_type
        self.neighbors = []  # list of Node
        self.links = {}      # neighbor_node_id -> Link

class Link:
    __slots__ = ['node1_id', 'node2_id', 'snow', 'walkability', 'length']

    def __init__(self, node1_id, node2_id, snow, walkability, length):
        self.node1_id = node1_id
        self.node2_id = node2_id
        self.snow = snow
        self.walkability = walkability
        self.length = length

class Graph:
    def __init__(self):
        self.nodes = {}  # node_id -> Node
        self.links = []  # list of Link

    def load(self, filepath):
        """Parse the NetLogo complete-graph file format."""
        self.nodes.clear()
        self.links.clear()

        with open(filepath, 'r') as f:
            lines = f.readlines()

        mode = "none"
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Strip "observer: " prefix if present
            if line.startswith("observer: "):
                line = line[len("observer: "):]

            if line.startswith("NEXT"):
                continue
            if line == "NODES":
                mode = "nodes"
                continue
            if line == "LINKS":
                mode = "links"
                continue

            if mode == "nodes":
                row = ast.literal_eval(line)
                # row: [id, x, y, node_type, building_type]
                node = Node(
                    node_id=row[0],
                    x=row[1],
                    y=row[2],
                    node_type=row[3],
                    building_type=row[4],
                )
                self.nodes[node.node_id] = node

            elif mode == "links":
                row = ast.literal_eval(line)
                # row: [id1, id2, snow?, walkability, length]
                link = Link(
                    node1_id=row[0],
                    node2_id=row[1],
                    snow=row[2],
                    walkability=row[3],
                    length=row[4],
                )
                self.links.append(link)

                # Wire up adjacency
                n1 = self.nodes[link.node1_id]
                n2 = self.nodes[link.node2_id]
                n1.neighbors.append(n2)
                n2.neighbors.append(n1)
                n1.links[n2.node_id] = link
                n2.links[n1.node_id] = link

    def get_link(self, id1, id2):
        """Get the link between two nodes, or None."""
        node = self.nodes.get(id1)
        if node is None:
            return None
        return node.links.get(id2)

    def get_neighbors(self, node_id):
        """Get neighbor nodes of a given node."""
        node = self.nodes.get(node_id)
        if node is None:
            return []
        return node.neighbors

    def get_buildings_by_type(self, building_type):
        """Get all building nodes of a given type."""
        return [n for n in self.nodes.values()
                if n.node_type == "building" and n.building_type == building_type]

    def get_all_buildings(self):
        """Get all building nodes."""
        return [n for n in self.nodes.values() if n.node_type == "building"]

    def reset_links(self, snowed):
        """Reset all links for a new simulation run."""
        for link in self.links:
            link.snow = snowed
            link.walkability = 0
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_graph.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/__init__.py src/graph.py tests/__init__.py tests/test_graph.py
git commit -m "feat: add graph data model and complete-graph parser"
```

---

### Task 2: Dijkstra Shortest Path

**Files:**
- Modify: `src/graph.py`
- Create: `tests/test_dijkstra.py`

Port the Dijkstra's algorithm from the NetLogo code. Uses Python's `heapq` instead of the custom `pqueue.nls`.

- [ ] **Step 1: Write test for Dijkstra**

```python
# tests/test_dijkstra.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import Graph

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')

def make_graph():
    g = Graph()
    g.load(GRAPH_FILE)
    return g

def test_shortest_path_same_node():
    g = make_graph()
    path = g.shortest_path(0, 0)
    assert path == [g.nodes[0]]

def test_shortest_path_direct_neighbor():
    g = make_graph()
    # Node 0 connects directly to node 55
    path = g.shortest_path(0, 55)
    assert len(path) == 2
    assert path[0].node_id == 0
    assert path[1].node_id == 55

def test_shortest_path_multi_hop():
    g = make_graph()
    # Node 0 to node 3 requires multiple hops
    path = g.shortest_path(0, 3)
    assert len(path) >= 2
    assert path[0].node_id == 0
    assert path[-1].node_id == 3
    # Verify path is connected: each consecutive pair has a link
    for i in range(len(path) - 1):
        link = g.get_link(path[i].node_id, path[i+1].node_id)
        assert link is not None, f"No link between {path[i].node_id} and {path[i+1].node_id}"

def test_shortest_path_is_optimal():
    g = make_graph()
    # Node 1 connects to 2 directly (len ~68.4) and via 119 (81.6 + 60.1 = 141.7)
    path = g.shortest_path(1, 2)
    assert len(path) == 2  # direct is shorter
    assert path[0].node_id == 1
    assert path[1].node_id == 2

def test_shortest_path_returns_node_objects():
    g = make_graph()
    path = g.shortest_path(0, 55)
    from src.graph import Node
    for p in path:
        assert isinstance(p, Node)

if __name__ == "__main__":
    test_shortest_path_same_node()
    test_shortest_path_direct_neighbor()
    test_shortest_path_multi_hop()
    test_shortest_path_is_optimal()
    test_shortest_path_returns_node_objects()
    print("All Dijkstra tests passed.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_dijkstra.py -v`
Expected: FAIL (no `shortest_path` method)

- [ ] **Step 3: Implement shortest_path in graph.py**

Add to the `Graph` class in `src/graph.py`:

```python
import heapq

# Add this method to class Graph:

    def shortest_path(self, start_id, dest_id):
        """Dijkstra's algorithm. Returns list of Node objects from start to dest.
        
        Mirrors the NetLogo implementation:
        - Weight = link.length (physical distance)
        - Returns empty list if unreachable
        - Returns [start_node] if start == dest
        """
        if start_id == dest_id:
            return [self.nodes[start_id]]

        dist = {nid: float('inf') for nid in self.nodes}
        parent = {nid: None for nid in self.nodes}
        dist[start_id] = 0

        # Priority queue: (distance, node_id)
        pq = [(0, start_id)]

        while pq:
            d, cur_id = heapq.heappop(pq)

            if d > dist[cur_id]:
                continue  # stale entry

            if cur_id == dest_id:
                # Reconstruct path
                path = []
                nid = dest_id
                while nid is not None:
                    path.append(self.nodes[nid])
                    nid = parent[nid]
                path.reverse()
                return path

            cur_node = self.nodes[cur_id]
            for nbr in cur_node.neighbors:
                link = cur_node.links[nbr.node_id]
                alt = dist[cur_id] + link.length
                if alt < dist[nbr.node_id]:
                    dist[nbr.node_id] = alt
                    parent[nbr.node_id] = cur_id
                    heapq.heappush(pq, (alt, nbr.node_id))

        return []  # unreachable
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_dijkstra.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph.py tests/test_dijkstra.py
git commit -m "feat: add Dijkstra shortest path to Graph"
```

---

### Task 3: Agent Classes (Pedestrian + Plow)

**Files:**
- Create: `src/agents.py`
- Create: `tests/test_agents.py`

Port all agent state and movement logic. Each agent stores position as floating-point (x, y) for smooth animation between nodes, exactly as NetLogo's `fd` command works.

- [ ] **Step 1: Write tests for agent creation and movement**

```python
# tests/test_agents.py
import os
import sys
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import Graph
from src.agents import Pedestrian, Plow

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')

def make_graph():
    g = Graph()
    g.load(GRAPH_FILE)
    return g

def test_pedestrian_creation():
    g = make_graph()
    origin = g.nodes[0]
    dest = g.nodes[3]
    route = g.shortest_path(0, 3)
    ped = Pedestrian(origin=origin, final_destination=dest, route=route)
    assert ped.x == origin.x
    assert ped.y == origin.y
    assert ped.current_node == origin
    assert ped.final_destination == dest
    assert ped.route_index == 1
    assert ped.temp_destination == route[1]
    assert ped.walking_time == 0

def test_pedestrian_move_toward_target():
    g = make_graph()
    origin = g.nodes[0]  # (101, 1484)
    dest = g.nodes[55]   # (29, 1490)
    route = g.shortest_path(0, 55)
    ped = Pedestrian(origin=origin, final_destination=dest, route=route)

    speed = 10
    dx = dest.x - origin.x
    dy = dest.y - origin.y
    dist = math.sqrt(dx*dx + dy*dy)

    ped.move_toward_target(speed)

    # Should have moved 'speed' units toward node 55
    moved_dist = math.sqrt((ped.x - origin.x)**2 + (ped.y - origin.y)**2)
    assert abs(moved_dist - speed) < 0.01

def test_pedestrian_arrive_at_node():
    g = make_graph()
    origin = g.nodes[1]  # (189, 1582)
    dest = g.nodes[2]    # (255, 1600) - direct neighbor, dist ~68.4
    route = g.shortest_path(1, 2)
    ped = Pedestrian(origin=origin, final_destination=dest, route=route)

    # Move with speed larger than distance -> should snap to destination
    arrived = ped.move_toward_target(100)
    assert arrived == True
    assert ped.x == dest.x
    assert ped.y == dest.y

def test_plow_creation():
    g = make_graph()
    node = g.nodes[10]
    plow = Plow(start_node=node)
    assert plow.x == node.x
    assert plow.y == node.y
    assert plow.current_node == node
    assert plow.temp_destination is None

if __name__ == "__main__":
    test_pedestrian_creation()
    test_pedestrian_move_toward_target()
    test_pedestrian_arrive_at_node()
    test_plow_creation()
    print("All agent tests passed.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_agents.py -v`
Expected: FAIL (no module `src.agents`)

- [ ] **Step 3: Implement agents.py**

```python
# src/agents.py
import math

class Pedestrian:
    """Port of NetLogo pedestrian breed.
    
    Position (x, y) is floating-point for smooth movement between nodes,
    matching NetLogo's `face` + `fd` behavior.
    """
    __slots__ = [
        'x', 'y', 'current_node', 'prev_node', 'final_destination',
        'temp_destination', 'route', 'route_index', 'need_reroute_on',
        'walking_time', 'alive',
    ]

    def __init__(self, origin, final_destination, route):
        self.x = origin.x
        self.y = origin.y
        self.current_node = origin
        self.prev_node = origin
        self.final_destination = final_destination
        self.route = route          # list of Node objects
        self.route_index = 1        # next node to reach in route
        self.temp_destination = route[1] if len(route) > 1 else final_destination
        self.need_reroute_on = None # Node or None
        self.walking_time = 0
        self.alive = True

    def move_toward_target(self, speed):
        """Move toward temp_destination at given speed.
        
        Mirrors NetLogo: face temp-destination, then fd speed.
        Returns True if arrived at temp_destination this step.
        """
        target = self.temp_destination
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= speed:
            # Arrived: snap to target node
            self.x = target.x
            self.y = target.y
            return True
        else:
            # Move speed units toward target
            ratio = speed / dist
            self.x += dx * ratio
            self.y += dy * ratio
            return False


class Plow:
    """Port of NetLogo plow breed."""
    __slots__ = ['x', 'y', 'current_node', 'temp_destination', 'alive']

    def __init__(self, start_node):
        self.x = start_node.x
        self.y = start_node.y
        self.current_node = start_node
        self.temp_destination = None
        self.alive = True

    def move_toward_target(self, speed):
        """Same movement logic as Pedestrian."""
        if self.temp_destination is None:
            return False
        target = self.temp_destination
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= speed:
            self.x = target.x
            self.y = target.y
            return True
        else:
            ratio = speed / dist
            self.x += dx * ratio
            self.y += dy * ratio
            return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_agents.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents.py tests/test_agents.py
git commit -m "feat: add Pedestrian and Plow agent classes"
```

---

### Task 4: Simulation Engine — Core Tick Logic

**Files:**
- Create: `src/simulation.py`
- Create: `tests/test_simulation.py`

This is the largest task. It ports `generate-pedestrians`, `move-pedestrians`, `generate-plow`, `move-plow`, and all the helper reporters (`choose-origin-type`, `choose-dest-type`, `weighted-choice`, `pick-final-destination`). Every decision must strictly match the NetLogo code.

- [ ] **Step 1: Write tests for simulation**

```python
# tests/test_simulation.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import Graph
from src.simulation import SimulationEngine

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')

def make_sim(**kwargs):
    defaults = dict(
        graph_file=GRAPH_FILE,
        num_ped=10,
        speed_ped=10,
        speed_snow=5,
        speed_walkable_snow=7,
        reroute_p_when_snow=0.3,
        faster_threshold=200,
        snowed=False,
        snow_plow=False,
        num_plow=1,
        speed_plow=15,
        plow_strategy="clean-more-walked",
    )
    defaults.update(kwargs)
    return SimulationEngine(**defaults)

def test_generate_pedestrians_count():
    sim = make_sim(num_ped=10)
    sim.generate_pedestrians()
    assert len(sim.pedestrians) == 10

def test_pedestrians_start_on_buildings():
    sim = make_sim(num_ped=20)
    sim.generate_pedestrians()
    for ped in sim.pedestrians:
        assert ped.current_node.node_type == "building"

def test_pedestrians_destination_is_building():
    sim = make_sim(num_ped=20)
    sim.generate_pedestrians()
    for ped in sim.pedestrians:
        assert ped.final_destination.node_type == "building"
        assert ped.final_destination != ped.route[0]  # not same as origin

def test_pedestrians_have_valid_route():
    sim = make_sim(num_ped=20)
    sim.generate_pedestrians()
    for ped in sim.pedestrians:
        assert len(ped.route) >= 2
        assert ped.route[-1] == ped.final_destination

def test_tick_moves_pedestrians():
    sim = make_sim(num_ped=5)
    sim.generate_pedestrians()
    old_positions = [(p.x, p.y) for p in sim.pedestrians]
    sim.tick()
    new_positions = [(p.x, p.y) for p in sim.pedestrians]
    # At least some should have moved
    moved = sum(1 for o, n in zip(old_positions, new_positions) if o != n)
    assert moved > 0

def test_pedestrian_dies_at_destination():
    sim = make_sim(num_ped=5)
    sim.generate_pedestrians()
    # Run many ticks - some pedestrians should reach destination and be replaced
    for _ in range(500):
        sim.tick()
    # Should still have 5 pedestrians (dead ones replaced)
    assert len(sim.pedestrians) == 5

def test_snowed_links():
    sim = make_sim(snowed=True)
    for link in sim.graph.links:
        assert link.snow == True

def test_walkability_increases():
    sim = make_sim(num_ped=20, snowed=False)
    sim.generate_pedestrians()
    for _ in range(200):
        sim.tick()
    total_walk = sum(link.walkability for link in sim.graph.links)
    assert total_walk > 0

def test_plow_generation_at_tick_2000():
    sim = make_sim(snow_plow=True, num_plow=2, snowed=True)
    assert len(sim.plows) == 0
    # Run to tick 2000
    for _ in range(2001):
        sim.tick()
    assert len(sim.plows) == 2

def test_average_walking_time():
    sim = make_sim(num_ped=10)
    sim.generate_pedestrians()
    for _ in range(50):
        sim.tick()
    assert sim.average_walking_time > 0

if __name__ == "__main__":
    test_generate_pedestrians_count()
    test_pedestrians_start_on_buildings()
    test_pedestrians_destination_is_building()
    test_pedestrians_have_valid_route()
    test_tick_moves_pedestrians()
    test_pedestrian_dies_at_destination()
    test_snowed_links()
    test_walkability_increases()
    test_plow_generation_at_tick_2000()
    test_average_walking_time()
    print("All simulation tests passed.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_simulation.py -v`
Expected: FAIL (no module `src.simulation`)

- [ ] **Step 3: Implement simulation.py**

```python
# src/simulation.py
import random
import math
from src.graph import Graph
from src.agents import Pedestrian, Plow


class SimulationEngine:
    """Port of the NetLogo simulation logic.
    
    All decision logic strictly mirrors the NetLogo code.
    """

    # Origin/destination probabilities — match NetLogo globals
    P_ORIGIN = {"Academic": 0.3, "Dining": 0.3, "Residential": 0.3, "Other": 0.1}
    P_DEST = {"Academic": 0.3, "Dining": 0.3, "Residential": 0.3, "Other": 0.1}

    def __init__(self, graph_file, num_ped, speed_ped, speed_snow,
                 speed_walkable_snow, reroute_p_when_snow, faster_threshold,
                 snowed, snow_plow, num_plow, speed_plow, plow_strategy):
        self.graph = Graph()
        self.graph.load(graph_file)

        self.num_ped = num_ped
        self.speed_ped = speed_ped
        self.speed_snow = speed_snow
        self.speed_walkable_snow = speed_walkable_snow
        self.reroute_p_when_snow = reroute_p_when_snow
        self.faster_threshold = faster_threshold
        self.snowed = snowed
        self.snow_plow = snow_plow
        self.num_plow = num_plow
        self.speed_plow = speed_plow
        self.plow_strategy = plow_strategy

        self.pedestrians = []
        self.plows = []
        self.tick_count = 0
        self.average_walking_time = 0

        # Apply initial snow state
        self.graph.reset_links(snowed)

    def reset(self):
        """Mirrors reset-simulation."""
        self.pedestrians.clear()
        self.plows.clear()
        self.tick_count = 0
        self.average_walking_time = 0
        self.graph.reset_links(self.snowed)

    # ---- Weighted random choice (mirrors NetLogo weighted-choice) ----

    @staticmethod
    def _weighted_choice(options, weights):
        """Pick from options using weighted probability."""
        total = sum(weights.values())
        r = random.random() * total
        acc = 0
        for label, w in weights.items():
            acc += w
            if r <= acc:
                return label
        return list(weights.keys())[-1]  # fallback

    def _choose_origin_type(self):
        return self._weighted_choice(self.P_ORIGIN, self.P_ORIGIN)

    def _choose_dest_type(self):
        return self._weighted_choice(self.P_DEST, self.P_DEST)

    def _pick_final_destination(self, origin_node):
        """Mirrors pick-final-destination reporter."""
        dest_type = self._choose_dest_type()
        candidates = [n for n in self.graph.nodes.values()
                      if n.node_type == "building"
                      and n.building_type == dest_type
                      and n is not origin_node]
        if not candidates:
            candidates = [n for n in self.graph.nodes.values()
                          if n.node_type == "building"
                          and n is not origin_node]
        if not candidates:
            return None
        return random.choice(candidates)

    # ---- Pedestrian generation (mirrors generate-pedestrians) ----

    def generate_pedestrians(self):
        """Generate pedestrians until count reaches num_ped."""
        while len(self.pedestrians) < self.num_ped:
            origin_type = self._choose_origin_type()
            buildings_of_type = self.graph.get_buildings_by_type(origin_type)
            if not buildings_of_type:
                continue
            origin = random.choice(buildings_of_type)
            dest = self._pick_final_destination(origin)
            if dest is None:
                continue
            route = self.graph.shortest_path(origin.node_id, dest.node_id)
            if len(route) < 2:
                continue
            ped = Pedestrian(origin=origin, final_destination=dest, route=route)
            self.pedestrians.append(ped)

    # ---- Pedestrian movement (mirrors move-pedestrians) ----

    def _move_pedestrians(self):
        """Strictly mirrors the NetLogo move-pedestrians procedure."""
        for ped in self.pedestrians:
            if not ped.alive:
                continue

            # Get current link
            link = self.graph.get_link(ped.current_node.node_id,
                                       ped.temp_destination.node_id)

            # Determine speed based on road condition
            step_speed = self.speed_ped
            if link.snow:
                step_speed = self.speed_snow
                if link.walkability > self.faster_threshold:
                    step_speed = self.speed_walkable_snow

            arrived = ped.move_toward_target(step_speed)

            if arrived:
                # Increase walkability of the road just walked
                link.walkability += 1

                # Update tracking
                ped.prev_node = ped.current_node
                ped.current_node = ped.temp_destination

                # Check if reached final destination
                if ped.current_node is ped.final_destination:
                    ped.alive = False
                    continue

                # Advance to next node in route
                ped.route_index += 1
                if ped.route_index >= len(ped.route):
                    ped.alive = False
                    continue
                ped.temp_destination = ped.route[ped.route_index]

                # Check if next road is snowy -> possibly reroute
                next_link = self.graph.get_link(ped.current_node.node_id,
                                                 ped.temp_destination.node_id)
                if next_link and next_link.snow:
                    if random.random() < self.reroute_p_when_snow:
                        # Find neighbors excluding prev_node
                        nbrs = [n for n in ped.current_node.neighbors
                                if n is not ped.prev_node]
                        if nbrs:
                            # Find neighbor with highest walkability
                            best_walk = max(
                                self.graph.get_link(ped.current_node.node_id, n.node_id).walkability
                                for n in nbrs
                            )
                            # All neighbors with that walkability
                            bests = [n for n in nbrs
                                     if self.graph.get_link(ped.current_node.node_id, n.node_id).walkability == best_walk]
                            # Pick the one closest to final destination
                            best_candidate = min(
                                bests,
                                key=lambda n: math.sqrt(
                                    (n.x - ped.final_destination.x)**2 +
                                    (n.y - ped.final_destination.y)**2
                                )
                            )
                            # Only reroute if better than current path
                            if next_link.walkability != best_walk:
                                ped.need_reroute_on = best_candidate

        # Handle reroutes (mirrors the while loop outside ask pedestrians)
        for ped in self.pedestrians:
            if ped.need_reroute_on is not None and ped.alive:
                new_route = self.graph.shortest_path(
                    ped.need_reroute_on.node_id,
                    ped.final_destination.node_id
                )
                if new_route:
                    ped.route = [ped.current_node] + new_route
                    ped.route_index = 1
                    ped.temp_destination = ped.route[1]
                ped.need_reroute_on = None

        # Remove dead pedestrians
        self.pedestrians = [p for p in self.pedestrians if p.alive]

    # ---- Plow logic (mirrors generate-plow and move-plow) ----

    def _generate_plows(self):
        """Mirrors generate-plow: create plows on random nodes."""
        all_nodes = list(self.graph.nodes.values())
        for _ in range(self.num_plow):
            node = random.choice(all_nodes)
            self.plows.append(Plow(start_node=node))

    def _move_plows(self):
        """Strictly mirrors the NetLogo move-plow procedure."""
        for plow in self.plows:
            if plow.temp_destination is None:
                # Plan next move
                nbrs = plow.current_node.neighbors
                if not nbrs:
                    continue

                # Find snowy neighbors
                snowy = [n for n in nbrs
                         if self.graph.get_link(plow.current_node.node_id, n.node_id).snow]

                if snowy:
                    if self.plow_strategy == "clean-more-walked":
                        # Pick snowy neighbor with highest walkability
                        plow.temp_destination = max(
                            snowy,
                            key=lambda n: self.graph.get_link(
                                plow.current_node.node_id, n.node_id
                            ).walkability
                        )
                    elif self.plow_strategy == "clean-less-walked":
                        # Pick snowy neighbor with lowest walkability
                        plow.temp_destination = min(
                            snowy,
                            key=lambda n: self.graph.get_link(
                                plow.current_node.node_id, n.node_id
                            ).walkability
                        )
                else:
                    # No snowy path: move to random neighbor
                    plow.temp_destination = random.choice(nbrs)
            else:
                arrived = plow.move_toward_target(self.speed_plow)
                if arrived:
                    # Clean the road just traversed
                    link = self.graph.get_link(
                        plow.current_node.node_id,
                        plow.temp_destination.node_id
                    )
                    if link:
                        link.snow = False

                    plow.current_node = plow.temp_destination
                    plow.temp_destination = None

    # ---- Main tick (mirrors go) ----

    def tick(self):
        """One simulation tick. Mirrors the NetLogo go procedure."""
        self.generate_pedestrians()
        self._move_pedestrians()
        self._move_plows()

        # Generate plows at tick 2000
        if self.tick_count == 2000:
            if self.snow_plow:
                self._generate_plows()

        # Increment walking time for all living pedestrians
        for ped in self.pedestrians:
            ped.walking_time += 1

        # Update average walking time
        if self.pedestrians:
            self.average_walking_time = (
                sum(p.walking_time for p in self.pedestrians) / self.num_ped
            )
        else:
            self.average_walking_time = 0

        self.tick_count += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_simulation.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/simulation.py tests/test_simulation.py
git commit -m "feat: add SimulationEngine with full pedestrian and plow logic"
```

---

### Task 5: Pygame Visualization

**Files:**
- Create: `src/visualization.py`

Renders the simulation in real-time using Pygame. Draws `campus_map.png` as background, nodes, links (with walkability coloring), pedestrians, and plows. Includes a basic control panel with parameter display.

Note: NetLogo y=0 is bottom; Pygame y=0 is top. Conversion: `screen_y = 1799 - netlogo_y`.

- [ ] **Step 1: Implement visualization.py**

```python
# src/visualization.py
import pygame
import sys

# Colors matching NetLogo defaults
COLOR_BUILDING = (255, 165, 0)    # orange
COLOR_ROAD_NODE = (0, 0, 0)       # black
COLOR_LINK_DEFAULT = (255, 255, 0) # yellow
COLOR_LINK_SNOW = (100, 100, 255)  # blue
COLOR_PEDESTRIAN = (0, 0, 0)       # black
COLOR_PLOW = (255, 0, 0)           # red
COLOR_PANEL_BG = (40, 40, 40)
COLOR_PANEL_TEXT = (255, 255, 255)

NODE_RADIUS = 5
PED_RADIUS = 4
PLOW_SIZE = 8
LINK_WIDTH = 2

PANEL_WIDTH = 300


class PygameRenderer:
    """Real-time visualization of the simulation, matching NetLogo's appearance."""

    def __init__(self, simulation, map_image_path, target_fps=30):
        self.sim = simulation
        self.target_fps = target_fps

        pygame.init()

        # Load map image
        self.map_surface = pygame.image.load(map_image_path)
        self.map_w = self.map_surface.get_width()   # 1738
        self.map_h = self.map_surface.get_height()  # 1800

        # Scale down for screen (1800px is too tall for most screens)
        self.scale = min(900 / self.map_h, 1.0)
        self.display_w = int(self.map_w * self.scale) + PANEL_WIDTH
        self.display_h = int(self.map_h * self.scale)

        self.screen = pygame.display.set_mode((self.display_w, self.display_h))
        pygame.display.set_caption("Pedestrian Movement Simulation")

        # Pre-scale the map
        self.scaled_map = pygame.transform.scale(
            self.map_surface,
            (int(self.map_w * self.scale), int(self.map_h * self.scale))
        )

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.running = True
        self.paused = False

    def _to_screen(self, nx, ny):
        """Convert NetLogo coords to screen coords.
        
        NetLogo: y=0 is bottom. Screen: y=0 is top.
        """
        sx = int(nx * self.scale)
        sy = int((1799 - ny) * self.scale)
        return sx, sy

    def _draw_links(self):
        """Draw all links. Color by walkability if show_walkability, else default."""
        max_walk = max((lk.walkability for lk in self.sim.graph.links), default=1)
        if max_walk == 0:
            max_walk = 1

        for link in self.sim.graph.links:
            n1 = self.sim.graph.nodes[link.node1_id]
            n2 = self.sim.graph.nodes[link.node2_id]
            p1 = self._to_screen(n1.x, n1.y)
            p2 = self._to_screen(n2.x, n2.y)

            if self.show_walkability:
                # NetLogo: color = (1 - ratio) * 9.9 on grayscale
                # Translate: ratio=0 -> white, ratio=1 -> black
                ratio = link.walkability / max_walk
                gray = int((1 - ratio) * 255)
                color = (gray, gray, gray)
            elif link.snow:
                color = COLOR_LINK_SNOW
            else:
                color = COLOR_LINK_DEFAULT

            pygame.draw.line(self.screen, color, p1, p2, LINK_WIDTH)

    def _draw_nodes(self):
        """Draw all nodes."""
        for node in self.sim.graph.nodes.values():
            pos = self._to_screen(node.x, node.y)
            color = COLOR_BUILDING if node.node_type == "building" else COLOR_ROAD_NODE
            pygame.draw.circle(self.screen, color, pos, NODE_RADIUS)

    def _draw_pedestrians(self):
        """Draw all pedestrians at their current floating-point position."""
        if self.show_walkability:
            return  # NetLogo hides pedestrians when show-walkability is on
        for ped in self.sim.pedestrians:
            pos = self._to_screen(ped.x, ped.y)
            pygame.draw.circle(self.screen, COLOR_PEDESTRIAN, pos, PED_RADIUS)

    def _draw_plows(self):
        """Draw all plows as red squares."""
        for plow in self.sim.plows:
            pos = self._to_screen(plow.x, plow.y)
            rect = pygame.Rect(
                pos[0] - PLOW_SIZE // 2,
                pos[1] - PLOW_SIZE // 2,
                PLOW_SIZE, PLOW_SIZE
            )
            pygame.draw.rect(self.screen, COLOR_PLOW, rect)

    def _draw_panel(self):
        """Draw info panel on the right side."""
        panel_x = self.display_w - PANEL_WIDTH
        pygame.draw.rect(self.screen, COLOR_PANEL_BG,
                         (panel_x, 0, PANEL_WIDTH, self.display_h))

        lines = [
            f"Tick: {self.sim.tick_count}",
            f"Avg Walk Time: {self.sim.average_walking_time:.1f}",
            f"Pedestrians: {len(self.sim.pedestrians)}",
            f"Plows: {len(self.sim.plows)}",
            "",
            f"num-ped: {self.sim.num_ped}",
            f"speed-ped: {self.sim.speed_ped}",
            f"speed-snow: {self.sim.speed_snow}",
            f"speed-walkable-snow: {self.sim.speed_walkable_snow}",
            f"reroute-p: {self.sim.reroute_p_when_snow}",
            f"faster-threshold: {self.sim.faster_threshold}",
            f"snowed: {self.sim.snowed}",
            f"snow-plow: {self.sim.snow_plow}",
            f"num-plow: {self.sim.num_plow}",
            f"speed-plow: {self.sim.speed_plow}",
            f"plow-strategy: {self.sim.plow_strategy}",
            "",
            "[SPACE] Pause/Resume",
            "[W] Toggle walkability",
            "[R] Reset simulation",
            "[Q] Quit",
        ]

        y = 10
        for line in lines:
            surf = self.font.render(line, True, COLOR_PANEL_TEXT)
            self.screen.blit(surf, (panel_x + 10, y))
            y += 20

    def run(self):
        """Main render loop."""
        self.show_walkability = False

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_w:
                        self.show_walkability = not self.show_walkability
                    elif event.key == pygame.K_r:
                        self.sim.reset()

            # Simulation step
            if not self.paused:
                self.sim.tick()

            # Draw
            self.screen.blit(self.scaled_map, (0, 0))
            self._draw_links()
            self._draw_nodes()
            self._draw_pedestrians()
            self._draw_plows()
            self._draw_panel()

            pygame.display.flip()
            self.clock.tick(self.target_fps)

        pygame.quit()
```

- [ ] **Step 2: Manually verify visualization**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -c "
from src.simulation import SimulationEngine
from src.visualization import PygameRenderer
sim = SimulationEngine(
    graph_file='complete-graph', num_ped=100, speed_ped=10,
    speed_snow=5, speed_walkable_snow=7, reroute_p_when_snow=0.3,
    faster_threshold=200, snowed=False, snow_plow=False,
    num_plow=1, speed_plow=15, plow_strategy='clean-more-walked')
renderer = PygameRenderer(sim, 'campus_map.png')
renderer.run()
"`

Expected: Pygame window opens showing the campus map with orange building nodes, black road nodes, yellow links, and black dots (pedestrians) moving along the links. Press SPACE to pause, W to toggle walkability view, Q to quit.

- [ ] **Step 3: Commit**

```bash
git add src/visualization.py
git commit -m "feat: add Pygame real-time visualization"
```

---

### Task 6: Main Entry Point

**Files:**
- Create: `src/main.py`

Wire everything together with command-line argument support for all parameters.

- [ ] **Step 1: Implement main.py**

```python
# src/main.py
import argparse
import os
from src.simulation import SimulationEngine
from src.visualization import PygameRenderer


def main():
    parser = argparse.ArgumentParser(
        description="Pedestrian Movement Simulation (Python port)"
    )
    parser.add_argument("--num-ped", type=int, default=100)
    parser.add_argument("--speed-ped", type=float, default=10)
    parser.add_argument("--speed-snow", type=float, default=5)
    parser.add_argument("--speed-walkable-snow", type=float, default=7)
    parser.add_argument("--reroute-p", type=float, default=0.3)
    parser.add_argument("--faster-threshold", type=float, default=200)
    parser.add_argument("--snowed", action="store_true")
    parser.add_argument("--snow-plow", action="store_true")
    parser.add_argument("--num-plow", type=int, default=1)
    parser.add_argument("--speed-plow", type=float, default=15)
    parser.add_argument("--plow-strategy", choices=["clean-more-walked", "clean-less-walked"],
                        default="clean-more-walked")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--graph-file", default=None,
                        help="Path to graph file (default: complete-graph in project root)")
    parser.add_argument("--map-image", default=None,
                        help="Path to map image (default: campus_map.png in project root)")

    args = parser.parse_args()

    # Resolve default paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    graph_file = args.graph_file or os.path.join(project_root, "complete-graph")
    map_image = args.map_image or os.path.join(project_root, "campus_map.png")

    sim = SimulationEngine(
        graph_file=graph_file,
        num_ped=args.num_ped,
        speed_ped=args.speed_ped,
        speed_snow=args.speed_snow,
        speed_walkable_snow=args.speed_walkable_snow,
        reroute_p_when_snow=args.reroute_p,
        faster_threshold=args.faster_threshold,
        snowed=args.snowed,
        snow_plow=args.snow_plow,
        num_plow=args.num_plow,
        speed_plow=args.speed_plow,
        plow_strategy=args.plow_strategy,
    )

    renderer = PygameRenderer(sim, map_image, target_fps=args.fps)
    renderer.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the full simulation**

Run these commands to verify different configurations:

```bash
# Default (no snow)
cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m src.main

# With snow
python3 -m src.main --snowed

# With snow + plow
python3 -m src.main --snowed --snow-plow --num-plow 2

# With different plow strategy
python3 -m src.main --snowed --snow-plow --plow-strategy clean-less-walked
```

Expected: Each launch opens a Pygame window with correct behavior matching NetLogo.

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: add main entry point with CLI argument support"
```

---

### Task 7: End-to-End Validation

**Files:**
- Create: `tests/test_e2e.py`

Run a full simulation for enough ticks and validate that emergent behavior matches expectations from the NetLogo model.

- [ ] **Step 1: Write end-to-end tests**

```python
# tests/test_e2e.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulation import SimulationEngine

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')

def make_sim(**kwargs):
    defaults = dict(
        graph_file=GRAPH_FILE,
        num_ped=100,
        speed_ped=10,
        speed_snow=5,
        speed_walkable_snow=7,
        reroute_p_when_snow=0.3,
        faster_threshold=200,
        snowed=False,
        snow_plow=False,
        num_plow=1,
        speed_plow=15,
        plow_strategy="clean-more-walked",
    )
    defaults.update(kwargs)
    return SimulationEngine(**defaults)

def test_no_snow_average_walking_time():
    """Without snow, average walking time should stabilize around 40-80 ticks
    (matching NetLogo's ~60 tick average)."""
    sim = make_sim(snowed=False)
    for _ in range(3000):
        sim.tick()
    # Should be reasonable - not 0, not extremely high
    assert 20 < sim.average_walking_time < 150, \
        f"avg_walk={sim.average_walking_time}, expected 20-150"

def test_snow_increases_walking_time():
    """Snow should increase average walking time compared to no snow."""
    sim_clear = make_sim(snowed=False)
    sim_snow = make_sim(snowed=True)
    for _ in range(3000):
        sim_clear.tick()
        sim_snow.tick()
    assert sim_snow.average_walking_time > sim_clear.average_walking_time

def test_walkability_pattern_emerges():
    """After many ticks, some links should have much higher walkability than others."""
    sim = make_sim(snowed=False)
    for _ in range(3000):
        sim.tick()
    walks = sorted([lk.walkability for lk in sim.graph.links], reverse=True)
    # Top links should be significantly more walked than bottom
    assert walks[0] > walks[-1] + 10

def test_plow_clears_snow():
    """After plow is active, some roads should become snow-free."""
    sim = make_sim(snowed=True, snow_plow=True, num_plow=3)
    for _ in range(2500):
        sim.tick()
    # Some links should now be clear
    cleared = sum(1 for lk in sim.graph.links if not lk.snow)
    assert cleared > 0, "Plow should have cleared at least some roads"

def test_pedestrian_count_maintained():
    """Pedestrian count should stay at num_ped throughout simulation."""
    sim = make_sim(num_ped=50)
    for _ in range(1000):
        sim.tick()
        assert len(sim.pedestrians) == 50

if __name__ == "__main__":
    test_no_snow_average_walking_time()
    test_snow_increases_walking_time()
    test_walkability_pattern_emerges()
    test_plow_clears_snow()
    test_pedestrian_count_maintained()
    print("All e2e tests passed.")
```

- [ ] **Step 2: Run e2e tests**

Run: `cd /Users/aurora/Desktop/Pedestrian-Movement-Simulation && python3 -m pytest tests/test_e2e.py -v --timeout=120`
Expected: All 5 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end validation tests"
```

---

## Summary

| Task | What it builds | Files |
|------|---------------|-------|
| 1 | Graph data model + parser | `src/graph.py`, `tests/test_graph.py` |
| 2 | Dijkstra shortest path | `src/graph.py` (modify), `tests/test_dijkstra.py` |
| 3 | Pedestrian + Plow agents | `src/agents.py`, `tests/test_agents.py` |
| 4 | Simulation engine (all logic) | `src/simulation.py`, `tests/test_simulation.py` |
| 5 | Pygame visualization | `src/visualization.py` |
| 6 | CLI entry point | `src/main.py` |
| 7 | End-to-end validation | `tests/test_e2e.py` |
