import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import Graph, Node

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', 'complete-graph')


def test_load_node_count():
    g = Graph()
    g.load(GRAPH_FILE)
    assert len(g.nodes) == 191  # IDs 0-192, but 121 and 122 are missing

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
    link = g.get_link(0, 55)
    assert link is not None
    assert abs(link.length - 72.2496) < 0.01
    assert link.snow == False
    assert link.walkability == 0

def test_node_neighbors():
    g = Graph()
    g.load(GRAPH_FILE)
    nbr_ids = {n.node_id for n in g.get_neighbors(0)}
    assert nbr_ids == {55, 57}


# Dijkstra tests

def test_shortest_path_same_node():
    g = Graph()
    g.load(GRAPH_FILE)
    path = g.shortest_path(0, 0)
    assert path == [g.nodes[0]]

def test_shortest_path_direct_neighbor():
    g = Graph()
    g.load(GRAPH_FILE)
    path = g.shortest_path(0, 55)
    assert len(path) == 2
    assert path[0].node_id == 0
    assert path[1].node_id == 55

def test_shortest_path_multi_hop():
    g = Graph()
    g.load(GRAPH_FILE)
    path = g.shortest_path(0, 3)
    assert len(path) >= 2
    assert path[0].node_id == 0
    assert path[-1].node_id == 3
    for i in range(len(path) - 1):
        link = g.get_link(path[i].node_id, path[i+1].node_id)
        assert link is not None

def test_shortest_path_is_optimal():
    g = Graph()
    g.load(GRAPH_FILE)
    path = g.shortest_path(1, 2)
    assert len(path) == 2
    assert path[0].node_id == 1
    assert path[1].node_id == 2

def test_shortest_path_returns_node_objects():
    g = Graph()
    g.load(GRAPH_FILE)
    path = g.shortest_path(0, 55)
    for p in path:
        assert isinstance(p, Node)
