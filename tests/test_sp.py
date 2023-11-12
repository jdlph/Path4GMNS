import os
import pytest
from random import choice

from path4gmns.utils import output_agent_paths, read_network


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


def test_routing_engine():
    network = read_network(input_dir='tests/fixtures')
    network.benchmark_apsp()


def test_find_shortest_path():
    network = read_network(input_dir='tests/fixtures')

    # shortest path (node id) from node 1 to node 2
    network.find_shortest_path(1, 2)
    # shortest path (link id) from node 1 to node 2
    network.find_shortest_path(1, 2, seq_type='link')

    # retrieve the shortest path under a specific mode (which must be defined
    # in settings.yaml)
    if os.path.isfile('tests/fixtures/settings.yml'):
        # shortest path (node id) from node 1 to node 2
        network.find_shortest_path(1, 2, mode='a')
        # shortest path (link id) from node 1 to node 2
        network.find_shortest_path(1, 2, mode='a', seq_type='link')


def test_find_shortest_path_for_agents(tmp_dir):
    """ find_path_for_agents has been DEPRECATED """
    network = read_network(load_demand=True, input_dir='tests/fixtures')

    # find agent paths under a specific mode defined in settings.yaml,
    # say, a (i.e., auto)
    # network.find_path_for_agents('a') or network.find_path_for_agents('auto')
    network.find_path_for_agents()

    agent_id = choice(network.get_agent_num())
    # origin node id of agent
    network.get_agent_orig_node_id(agent_id)
    # destination node id of agent
    network.get_agent_dest_node_id(agent_id)
    # shortest path (node id) of agent
    network.get_agent_node_path(agent_id)
    # shortest path (link id) of agent
    network.get_agent_link_path(agent_id)

    # output unique agent paths to a csv file
    output_agent_paths(network, output_dir=tmp_dir)
    # exclude geometry info from the output file
    output_agent_paths(network, False, output_dir=tmp_dir)


@pytest.fixture(autouse=True)
def cleanup(tmp_dir):
    for tmp_file in tmp_dir.iterdir():
        if tmp_file.isfile():
            yield
            os.remove(tmp_file)