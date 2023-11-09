from os import chdir

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

from time import time


def test_download_sample_data_sets():
    download_sample_data_sets()


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

    # st = time()
    # # find agent paths under a specific mode defined in settings.yaml,
    # # say, a (i.e., auto)
    # # network.find_path_for_agents('a') or network.find_path_for_agents('auto')
    # network.find_path_for_agents()
    # print('\nprocessing time of finding shortest paths for all agents: '
    #       f'{time()-st:.2f} s')

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

    print('\nstart column generation\n')
    st = time()

    column_gen_num = 20
    column_update_num = 20
    perform_column_generation(column_gen_num, column_update_num, network)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {column_gen_num} iterations in column generation and '
          f'{column_update_num} iterations in column update')

    # if you do not want to include geometry info in the output file,
    # use output_columns(network, False)
    output_columns(network)
    output_link_performance(network)


def test_column_generation_dtalite():
    """ validation using DTALite """
    print('start column generation using DTALite')
    st = time()

    chdir('fixtures')

    mode = 1
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {column_gen_num} iterations in column generation and '
          f'{column_update_num} iterations in column update')

    print('\npath finding results can be found in route_assignment.csv')

    chdir('..')


def test_loading_columns():
    network = read_network(input_dir='fixtures')

    print('\nstart loading columns\n')
    st = time()

    load_columns(network)

    print(f'processing time of loading columns: {time()-st:.2f} s')

    print('\nstart column generation')
    st = time()

    column_gen_num = 0
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {column_gen_num} iterations in column generation and '
          f'{column_update_num} iterations in column update')

    output_columns(network)
    output_link_performance(network)


def test_accessibility():
    network = read_network(input_dir='fixtures')

    print('\nstart accessibility evaluation\n')
    st = time()

    # multimodal accessibility evaluation
    evaluate_accessibility(network)
    # accessibility evaluation for a target mode
    # evaluate_accessibility(network, single_mode=True, mode='auto')

    print('complete accessibility evaluation.\n')
    print(f'processing time of accessibility evaluation: {time()-st:.2f} s')

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

    print('\nstart equity evaluation')
    st = time()
    # multimodal equity evaluation under default time budget (60 min)
    evaluate_equity(network)
    # equity evaluation for a target mode with time budget as 30 min
    # evaluate_equity(network, single_mode=True, mode='auto', time_budget=30)

    print('complete equity evaluation.\n')
    print(f'processing time of equity evaluation: {time()-st:.2f} s')


def test_zone_synthesis():
    network = read_network(input_dir='fixtures')

    print('\nstart zone synthesis')
    st = time()
    network_to_zones(network)
    output_zones(network)
    output_synthesized_demand(network)

    print('complete zone and demand synthesis.\n')
    print(f'processing time of zone and demand synthesis: {time()-st:.2f} s')


def test_loading_synthesized_zones_demand():
    network = read_network(input_dir='fixtures')

    print('\nstart loading synthesized zones and demand')
    st = time()
    read_zones(network)
    load_demand(network, filename='syn_demand.csv')

    print('complete loading synthesized zone and demand.\n')
    print(f'processing time of loading synthesized zone and demand: {time()-st:.2f} s')

    # perform some other functionalities from Path4GMNS, e.g., traffic assignment
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
    print('complete simple simulation.\n')

    print('writing agent trajectories')
    output_agent_trajectory(network)


def test_routing_engine():
    print('finding all-pairs shortest paths in the network\n')
    network = read_network(input_dir='fixtures')
    network.benchmark_apsp()


# if __name__=="__main__":
#     # test 0: download the sample data set from GitHub
#     test_download_sample_data_sets()
#     # test 1: find shortest path between O and D on Chicago network
#     test_find_shortest_path()
#     # test 2: find shortest paths for all agents on Chicago network
#     test_find_shortest_path_for_agents()
#     # test 3: perform column generation using Python engine on Chicago network
#     test_column_generation_py()
#     # test 4: perform column generation using DTALite on Chicago network
#     test_column_generation_dtalite()
#     # test 5: load columns generated from test 3 or 4 on Chicago network
#     test_loading_columns()
#     # test 6: evaluate multimodal accessibility on Chicago network
#     test_accessibility()
#     # test 7: evaluate multimodal equity on Chicago network
#     test_equity()
#     # test 8: synthesize zones and demand
#     test_zone_synthesis()
#     # test 9: load synthesized zones and demand
#     test_loading_synthesized_zones_demand()
#     # test 10: perform the simple DTA
#     test_simulation()
#     # test 11: test the C++ routing engine
#     test_routing_engine()