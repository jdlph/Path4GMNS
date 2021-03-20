import path4gmns as pg
from time import time


def test_find_shortest_path():
    load_demand = False
    network = pg.read_network(load_demand)
    print('\nshortest path (node id) from node 1 to node 2 is '
          +pg.find_shortest_path(network, 1, 2))


def test_find_shortest_path_for_agents():
    network = pg.read_network()

    st = time()

    pg.find_path_for_agents(network)
    print('\nprocessing time of finding shortest paths for all agents:{0: .2f}'
          .format(time()-st)+ 's')

    agent_no = 300
    agent1 = network.get_agent(agent_no)
    agent_no = 1000
    agent2 = network.get_agent(agent_no)

    print('\norigin node id of agent1 is '+str(agent1.get_orig_node_id()))
    print('destination node id of agent1 is '+str(agent1.get_dest_node_id()))
    print('shortest path (node id) of agent1 is ' 
          + str(agent1.get_node_path()))
    print('shortest path (link id) of agent1 is ' 
          + str(agent1.get_link_path()))

    print('\norigin node id of agent2 is '+str(agent2.get_orig_node_id()))
    print('destination node id of agent2 is '+str(agent2.get_dest_node_id()))
    print('shortest path (node id) of agent2 is ' 
          + str(agent2.get_node_path()))
    print('shortest path (link id) of agent2 is ' 
          + str(agent2.get_link_path()))


def test_column_generation_py():
    network = pg.read_network()
    
    print('\nstart column generation')
    
    st = time()
    iter_num = 1
    column_update_num = 1
    pg.perform_network_assignment(1, iter_num, column_update_num, network)
    print('processing time of column generation:{0: .2f}'
          .format(time()-st)+ 's'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    pg.output_columns(network.zones, network.column_pool)
    pg.output_link_performance(network.link_list)

    print('\npath finding results can be found in agent.csv')


def test_column_generation_dtalite():
    """ validation using DTALite """ 
    print('\nstart column generation')

    iter_num = 2
    column_update_num = 2
    pg.perform_network_assignment_DTALite(1, iter_num, column_update_num)


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
    
    demo_mode(2)