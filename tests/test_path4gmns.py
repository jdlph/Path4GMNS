import path4gmns as pg
from time import time


def test_find_shortest_path():
    load_demand = False
    network = pg.read_network(load_demand)
    print('\nshortest path (external node sequence) from node 1 to node 2 is '
          +str(pg.find_shortest_path(network, 1, 2)))


def test_find_shortest_path_for_agents():
    # read_network() will load demand by default
    # if there is no any other specification
    network = pg.read_network()

    st = time()

    pg.find_path_for_agents(network)
    print('\nprocessing time of finding shortest paths for all agents:{0: .2f}'
          .format(time()-st)+ 's')

    agent_no = 300
    agent = network.agent_list[agent_no]
    print('orig node id of agent is '+str(agent.o_node_id))
    print('dest node id of agent is '+str(agent.d_node_id))
    print('shortest path (internal node sequence) of agent is ' 
          + str(agent.path_node_seq_no_list))
    print('shortest path (internal link sequence) of agent is ' 
          + str(agent.path_link_seq_no_list))


def test_column_generation_py():
    network = pg.read_network()
    
    print('\nstart column generation')
    
    st = time()
    iter_num = 2
    colum_update_num = 2
    pg.perform_network_assignment(1, iter_num, colum_update_num, network)
    print('processing time of column generation:{0: .2f}'
          .format(time()-st)+ 's'
          f' for {iter_num} assignment iterations and '
          f'{colum_update_num} iterations in column generation')

    pg.output_columns(network.zones, network.column_pool)
    pg.output_link_performance(network.link_list)


def test_column_generation_dtalite():
    """ validation using DTALite """ 
    print('\nstart column generation')

    iter_num = 2
    colum_update_num = 2
    pg.perform_network_assignment_DTALite(1, iter_num, colum_update_num)


def demo_mode(mode):
    print(f'the selected mode is {mode}\n')

    if mode == 1:
        # option 1: find shortest path between O and D on Chicago network
        test_find_shortest_path()
    elif mode == 2:
        # option 2: find shortest paths for all agents on Chicago network
        test_find_shortest_path_for_agents()
    elif mode == 3:
        # option 3: perform column generation using Python engine 
        # on Chicago network
        test_column_generation_py()
    else:
        # option 4: perform column generation using DTALite on Chicago network
        test_column_generation_dtalite()


if __name__=="__main__":
    
    demo_mode(3)