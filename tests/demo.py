import path4gmns as pg
from time import time


def test_download_sample_data_sets():
    pg.download_sample_data_sets()


def test_find_shortest_path():
    network = pg.read_network(load_demand=False)

    print('\nshortest path (node id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2))
    print('\nshortest path (link id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, seq_type='link'))

    # retrieve the shortest path under a specific mode (which must be defined
    # in settings.yaml)
    print('\nshortest path (node id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, mode='w'))
    print('\nshortest path (link id) from node 1 to node 2, '
          +network.find_shortest_path(1, 2, mode='w', seq_type='link'))


def test_find_shortest_path_for_agents():
    network = pg.read_network()

    st = time()
    # find agent paths under a specific mode defined in settings.yaml,
    # say, w (i.e., walk)
    # network.find_path_for_agents('w') or network.find_path_for_agents('walk')
    network.find_path_for_agents()
    print('\nprocessing time of finding shortest paths for all agents: '
          f'{time()-st:.2f} s')

    agent_id = 300
    print('\norigin node id of agent is '
          f'{network.get_agent_orig_node_id(agent_id)}')
    print('destination node id of agent is '
          f'{network.get_agent_dest_node_id(agent_id)}')
    print('shortest path (node id) of agent, '
          f'{network.get_agent_node_path(agent_id)}')
    print('shortest path (link id) of agent, '
          f'{network.get_agent_link_path(agent_id)}')

    agent_id = 1000
    print('\norigin node id of agent is '
          f'{network.get_agent_orig_node_id(agent_id)}')
    print('destination node id of agent is '
          f'{network.get_agent_dest_node_id(agent_id)}')
    print('shortest path (node id) of agent, '
          f'{network.get_agent_node_path(agent_id)}')
    print('shortest path (link id) of agent, '
          f'{network.get_agent_link_path(agent_id)}')

    # output unique agent paths to a csv file
    # if you do not want to include geometry info in the output file,
    # you can do pg.output_agent_paths(network, False)
    pg.output_agent_paths(network)


def test_column_generation_py():
    # network = pg.read_network(input_dir='C:/Users/jdlph/Desktop/Chicago_Regional')
    network = pg.read_network()

    print('\nstart column generation\n')
    st = time()

    iter_num = 20
    column_update_num = 20
    # pg.perform_network_assignment(assignment_mode=1, assignment_num,
    #                               column_update_num, network)
    # has been deprecated starting from v0.7.2, and will be removed later.
    pg.perform_column_generation(iter_num, column_update_num, network)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    # if you do not want to include geometry info in the output file,
    # use pg.output_columns(network, False)
    pg.output_columns(network)
    pg.output_link_performance(network)


def test_column_generation_dtalite():
    """ validation using DTALite """
    print('start column generation using DTALite')
    st = time()

    mode = 1
    iter_num = 20
    column_update_num = 20
    pg.perform_network_assignment_DTALite(mode, iter_num, column_update_num)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    print('\npath finding results can be found in agent.csv')


def test_loading_columns():
    network = pg.read_network()

    print('\nstart loading columns\n')
    st = time()

    pg.load_columns(network)

    print(f'processing time of loading columns: {time()-st:.2f} s')

    print('\nstart column generation\n')
    st = time()

    iter_num = 0
    column_update_num = 10
    # pg.perform_network_assignment(assignment_mode=1, assignment_num,
    #                               column_update_num, network)
    # has been deprecated starting from v0.7.2, and will be removed in later.
    pg.perform_column_generation(iter_num, column_update_num, network)

    print(f'processing time of column generation: {time()-st:.2f} s'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    pg.output_columns(network)
    pg.output_link_performance(network)


def test_accessibility():
    network = pg.read_network(load_demand=False)

    print('\nstart accessibility evaluation\n')
    st = time()

    # multimodal accessibility evaluation
    pg.evaluate_accessibility(network, time_dependent=True, demand_period_id=1)
    # accessibility evalutation for a target mode
    # pg.evaluate_accessibility(network, multimodal=False, mode='p')

    print('complete accessibility evaluation.\n')
    print(f'processing time of accessibility evaluation: {time()-st:.2f} s')

    # get accessible nodes and links starting from node 1 with a 5-minitue
    # time window for the default mode auto (i.e., 'p')
    network.get_accessible_nodes(1, 5)
    network.get_accessible_links(1, 5)

    # get accessible nodes and links starting from node 1 with a 15-minitue
    # time window for mode walk (i.e., 'w')
    network.get_accessible_nodes(1, 15, 'w')
    network.get_accessible_links(1, 15, 'w')


def demo_mode(mode):
    print(f'the selected mode is {mode}\n')

    if mode == 0:
        # option 0: download the sample data set from GitHub
        test_download_sample_data_sets()
    elif mode == 1:
        # option 1: find shortest path between O and D on Chicago network
        test_find_shortest_path()
    elif mode == 2:
        # option 2: find shortest paths for all agents on Chicago network
        test_find_shortest_path_for_agents()
    elif mode == 3:
        # option 3: perform column generation using Python engine
        # on Chicago network
        test_column_generation_py()
    elif mode == 4:
        # option 4: perform column generation using DTALite on Chicago network
        test_column_generation_dtalite()
    elif mode == 5:
        # option 5: load columns generated from option 3 or 4
        # on Chicago network
        test_loading_columns()
    else:
        # option 6: evaluate multimodal accessibility on Chicago network
        test_accessibility()


if __name__=="__main__":

    demo_mode(6)