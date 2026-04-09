import pygame
import sys

# Colors matching NetLogo defaults
COLOR_BUILDING = (255, 165, 0)     # orange
COLOR_ROAD_NODE = (0, 0, 0)        # black
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
        self.map_h = self.map_surface.get_height()   # 1800

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
        self.show_walkability = False

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
