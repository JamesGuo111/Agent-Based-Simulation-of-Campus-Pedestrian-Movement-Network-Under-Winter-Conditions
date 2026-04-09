import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
        assert ped.final_destination != ped.route[0]


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
    moved = sum(1 for o, n in zip(old_positions, new_positions) if o != n)
    assert moved > 0


def test_pedestrian_dies_at_destination():
    """Dead pedestrians are replaced at the start of the next tick."""
    sim = make_sim(num_ped=5)
    for _ in range(500):
        sim.tick()
    # At end of tick, some may have died; but generate fills at start of each tick
    # So count should be close to num_ped (between num_ped - a few deaths and num_ped)
    assert len(sim.pedestrians) <= 5
    assert len(sim.pedestrians) >= 1


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
    for _ in range(2001):
        sim.tick()
    assert len(sim.plows) == 2


def test_average_walking_time():
    sim = make_sim(num_ped=10)
    sim.generate_pedestrians()
    for _ in range(50):
        sim.tick()
    assert sim.average_walking_time > 0
