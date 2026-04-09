import heapq
import re


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


def _parse_netlogo_list(s):
    """Parse a NetLogo space-separated list like: [0 101 1484 "building" "Academic"]"""
    s = s.strip()
    if s.startswith('['):
        s = s[1:]
    if s.endswith(']'):
        s = s[:-1]
    # Tokenize: respect quoted strings
    tokens = re.findall(r'"[^"]*"|\S+', s)
    result = []
    for t in tokens:
        if t.startswith('"') and t.endswith('"'):
            result.append(t[1:-1])  # strip quotes
        else:
            result.append(t)
    return result


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
                row = _parse_netlogo_list(line)
                # row: [id, x, y, node_type, building_type]
                node = Node(
                    node_id=int(row[0]),
                    x=int(row[1]),
                    y=int(row[2]),
                    node_type=row[3],
                    building_type=row[4],
                )
                self.nodes[node.node_id] = node

            elif mode == "links":
                row = _parse_netlogo_list(line)
                # row: [id1, id2, snow?, walkability, length]
                link = Link(
                    node1_id=int(row[0]),
                    node2_id=int(row[1]),
                    snow=(row[2] == "true"),
                    walkability=int(row[3]),
                    length=float(row[4]),
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
