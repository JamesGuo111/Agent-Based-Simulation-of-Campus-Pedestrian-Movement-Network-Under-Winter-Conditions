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
        self.route = route
        self.route_index = 1
        self.temp_destination = route[1] if len(route) > 1 else final_destination
        self.need_reroute_on = None
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
            self.x = target.x
            self.y = target.y
            return True
        else:
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
