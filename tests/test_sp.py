from os.path import isfile
from random import randint

from path4gmns.utils import output_agent_paths, read_network


def test_routing_engine(sample_data_dir):
    network = read_network(input_dir=sample_data_dir)
    network.benchmark_apsp()


def test_find_shortest_path(sample_data_dir):
    network = read_network(input_dir=sample_data_dir)

    # shortest path (node id) from node 1 to node 2
    network.find_shortest_path(1, 2)
    # shortest path (link id) from node 1 to node 2
    network.find_shortest_path(1, 2, seq_type='link')

    # retrieve the shortest path under a specific mode (which must be defined
    # in settings.yaml)
    if isfile(sample_data_dir + '/settings.yml'):
        # shortest path (node id) from node 1 to node 2
        network.find_shortest_path(1, 2, mode='a')
        # shortest path (link id) from node 1 to node 2
        network.find_shortest_path(1, 2, mode='a', seq_type='link')


def test_find_shortest_path_for_agents(sample_data_dir, tmp_output_dir):
    """ find_path_for_agents has been DEPRECATED """
    network = read_network(load_demand=True, input_dir=sample_data_dir)

    # find agent paths under a specific mode defined in settings.yaml,
    # say, a (i.e., auto)
    # network.find_path_for_agents('a') or network.find_path_for_agents('auto')
    network.find_path_for_agents()

    agent_id = randint(0, network.get_agent_num() - 1)
    # origin node id of agent
    network.get_agent_orig_node_id(agent_id)
    # destination node id of agent
    network.get_agent_dest_node_id(agent_id)
    # shortest path (node id) of agent
    network.get_agent_node_path(agent_id)
    # shortest path (link id) of agent
    network.get_agent_link_path(agent_id)

    # output unique agent paths to a csv file
    output_agent_paths(network, output_dir=tmp_output_dir)
    # exclude geometry info from the output file
    output_agent_paths(network, False, output_dir=tmp_output_dir)