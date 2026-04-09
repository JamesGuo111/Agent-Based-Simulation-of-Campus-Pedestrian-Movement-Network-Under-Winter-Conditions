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
    parser.add_argument("--plow-strategy",
                        choices=["clean-more-walked", "clean-less-walked"],
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
