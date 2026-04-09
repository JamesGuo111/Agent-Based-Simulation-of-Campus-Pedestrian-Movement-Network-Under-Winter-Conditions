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
    def _weighted_choice(weights):
        """Pick from options using weighted probability.
        weights: dict of label -> weight
        """
        total = sum(weights.values())
        r = random.random() * total
        acc = 0
        for label, w in weights.items():
            acc += w
            if r <= acc:
                return label
        return list(weights.keys())[-1]

    def _choose_origin_type(self):
        return self._weighted_choice(self.P_ORIGIN)

    def _choose_dest_type(self):
        return self._weighted_choice(self.P_DEST)

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
                        plow.temp_destination = max(
                            snowy,
                            key=lambda n: self.graph.get_link(
                                plow.current_node.node_id, n.node_id
                            ).walkability
                        )
                    elif self.plow_strategy == "clean-less-walked":
                        plow.temp_destination = min(
                            snowy,
                            key=lambda n: self.graph.get_link(
                                plow.current_node.node_id, n.node_id
                            ).walkability
                        )
                else:
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
