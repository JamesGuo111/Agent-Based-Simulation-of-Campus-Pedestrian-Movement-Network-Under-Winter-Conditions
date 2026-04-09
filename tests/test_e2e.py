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
    """Without snow, average walking time should stabilize reasonably."""
    sim = make_sim(snowed=False)
    for _ in range(3000):
        sim.tick()
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
    """After many ticks, some links should have much higher walkability."""
    sim = make_sim(snowed=False)
    for _ in range(3000):
        sim.tick()
    walks = sorted([lk.walkability for lk in sim.graph.links], reverse=True)
    assert walks[0] > walks[-1] + 10


def test_plow_clears_snow():
    """After plow is active, some roads should become snow-free."""
    sim = make_sim(snowed=True, snow_plow=True, num_plow=3)
    for _ in range(2500):
        sim.tick()
    cleared = sum(1 for lk in sim.graph.links if not lk.snow)
    assert cleared > 0


def test_pedestrian_count_maintained():
    """Pedestrian count is refilled to num_ped at the start of each tick."""
    sim = make_sim(num_ped=50)
    for _ in range(1000):
        sim.tick()
    # After many ticks, count may be slightly below num_ped (deaths in current tick)
    # but should be close
    assert len(sim.pedestrians) >= 40
