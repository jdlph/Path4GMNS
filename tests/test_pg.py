from os import chdir
from shutil import rmtree

from path4gmns.accessibility import evaluate_accessibility, evaluate_equity
from path4gmns.colgen import perform_column_generation
from path4gmns.dtaapi import perform_network_assignment_DTALite
from path4gmns.simulation import perform_simple_simulation

from path4gmns.utils import download_sample_data_sets, load_columns, load_demand,\
                            output_agent_paths, output_agent_trajectory,\
                            output_columns, output_link_performance, \
                            output_synthesized_demand, output_zones, \
                            read_network, read_zones

from path4gmns.zonesyn import network_to_zones


def test_download_sample_data_sets():
    download_sample_data_sets()
    rmtree('data')


def test_find_shortest_path():
    network = read_network(input_dir='fixtures')

    print('\nshortest path (node id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2))
    print('\nshortest path (link id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, seq_type='link'))

    # retrieve the shortest path under a specific mode (which must be defined
    # in settings.yaml)
    print('\nshortest path (node id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, mode='a'))
    print('\nshortest path (link id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, mode='a', seq_type='link'))


def test_find_shortest_path_for_agents():
    """ DEPRECATED """

    print("DEPRECATED")

    # network = read_network(load_demand=True)

    # # find agent paths under a specific mode defined in settings.yaml,
    # # say, a (i.e., auto)
    # # network.find_path_for_agents('a') or network.find_path_for_agents('auto')
    # network.find_path_for_agents()

    # agent_id = 300
    # print('\norigin node id of agent is '
    #       f'{network.get_agent_orig_node_id(agent_id)}')
    # print('destination node id of agent is '
    #       f'{network.get_agent_dest_node_id(agent_id)}')
    # print('shortest path (node id) of agent, '
    #       f'{network.get_agent_node_path(agent_id)}')
    # print('shortest path (link id) of agent, '
    #       f'{network.get_agent_link_path(agent_id)}')

    # agent_id = 1000
    # print('\norigin node id of agent is '
    #       f'{network.get_agent_orig_node_id(agent_id)}')
    # print('destination node id of agent is '
    #       f'{network.get_agent_dest_node_id(agent_id)}')
    # print('shortest path (node id) of agent, '
    #       f'{network.get_agent_node_path(agent_id)}')
    # print('shortest path (link id) of agent, '
    #       f'{network.get_agent_link_path(agent_id)}')

    # # output unique agent paths to a csv file
    # # if you do not want to include geometry info in the output file,
    # # you can do output_agent_paths(network, False)
    # output_agent_paths(network)


def test_column_generation_py():
    network = read_network(load_demand=True, input_dir='fixtures')

    column_gen_num = 20
    column_update_num = 20
    perform_column_generation(column_gen_num, column_update_num, network)

    # use output_columns(network, False) to exclude geometry info in the output file,
    output_columns(network)
    output_link_performance(network)


def test_column_generation_dtalite():
    chdir('fixtures')

    mode = 1
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir('..')


def test_loading_columns():
    network = read_network(input_dir='fixtures')
    load_columns(network)

    column_gen_num = 0
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    output_columns(network)
    output_link_performance(network)


def test_accessibility():
    network = read_network(input_dir='fixtures')

    # multimodal accessibility evaluation
    evaluate_accessibility(network)
    # accessibility evaluation for a target mode
    # evaluate_accessibility(network, single_mode=True, mode='auto')

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto (i.e., 'auto')
    network.get_accessible_nodes(1, 5)
    network.get_accessible_links(1, 5)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w')
    network.get_accessible_nodes(1, 15, 'w')
    network.get_accessible_links(1, 15, 'w')

    # time-dependent accessibility under the default mode auto
    # for demand period 0 (i.e., VDF_fftt1 in link.csv will be used in the
    # evaluation)
    # evaluate_accessibility(network, single_mode=True, time_dependent=True)

    # it is equivalent to
    # evaluate_accessibility(network, single_mode=True,
    #                           time_dependent=True, demand_period_id=0)

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto for demand period 0
    # network.get_accessible_nodes(1, 5, time_dependent=True)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w') for demand period 0
    # network.get_accessible_nodes(1, 15, 'w', time_dependent=True)


def test_equity():
    network = read_network(input_dir='fixtures')

    # multimodal equity evaluation under default time budget (60 min)
    evaluate_equity(network)
    # equity evaluation for a target mode with time budget as 30 min
    # evaluate_equity(network, single_mode=True, mode='auto', time_budget=30)


def test_zone_synthesis():
    network = read_network(input_dir='fixtures')
    network_to_zones(network)

    output_zones(network)
    output_synthesized_demand(network)


def test_loading_synthesized_zones_demand():
    network = read_network(input_dir='fixtures')

    read_zones(network)
    load_demand(network, filename='demand.csv')

    column_gen_num = 20
    column_update_num = 20
    perform_column_generation(column_gen_num, column_update_num, network)

    output_columns(network)
    output_link_performance(network)


def test_simulation():
    network = read_network(load_demand=True, input_dir='fixtures')

    # column_gen_num = 20
    # column_update_num = 20
    # perform_column_generation(column_gen_num, column_update_num, network)

    # you can bypass the above perform_column_generation() and call
    # load_columns(network) if you have route_assignment.csv
    load_columns(network)
    perform_simple_simulation(network, 'uniform')

    output_agent_trajectory(network)


def test_routing_engine():
    network = read_network(input_dir='fixtures')
    network.benchmark_apsp()