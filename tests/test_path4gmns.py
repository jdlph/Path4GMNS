import path4gmns as pg
from time import time


def test_find_shortest_path():
    load_demand = False
    network = pg.read_network(load_demand)

    print('\nshortest path (node id) from node 1 to node 2 is '
          +network.find_shortest_path(1, 2))
    print('\nshortest path (link id) from node 1 to node 2 is '
          +network.find_shortest_path(1, 2, 'link'))


def test_find_shortest_path_for_agents():
    network = pg.read_network()

    st = time()
    network.find_path_for_agents()
    print('\nprocessing time of finding shortest paths for all agents:{0: .2f}'
          .format(time()-st)+ 's')

    agent_id = 300
    print('\norigin node id of agent is '
          +str(network.get_agent_orig_node_id(agent_id)))
    print('destination node id of agent is '
          +str(network.get_agent_dest_node_id(agent_id)))
    print('shortest path (node id) of agent is '
          +str(network.get_agent_node_path(agent_id)))
    print('shortest path (link id) of agent is '
          +str(network.get_agent_link_path(agent_id)))

    agent_id = 1000
    print('\norigin node id of agent is '
          +str(network.get_agent_orig_node_id(agent_id)))
    print('destination node id of agent is '
          +str(network.get_agent_dest_node_id(agent_id)))
    print('shortest path (node id) of agent is '
          +str(network.get_agent_node_path(agent_id)))
    print('shortest path (link id) of agent is '
          +str(network.get_agent_link_path(agent_id)))


def test_column_generation_py():
    network = pg.read_network()

    print('\nstart column generation\n')
    st = time()

    iter_num = 20
    column_update_num = 20
    pg.perform_network_assignment(1, iter_num, column_update_num, network)

    print('processing time of column generation:{0: .2f}'.format(time()-st)+'s'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    pg.output_columns(network)
    pg.output_link_performance(network)

    print('\npath finding results can be found in agent.csv')


def test_column_generation_dtalite():
    """ validation using DTALite """
    print('start column generation using DTALite')
    st = time()

    iter_num = 20
    column_update_num = 20
    pg.perform_network_assignment_DTALite(1, iter_num, column_update_num)

    print('processing time of column generation:{0: .2f}'.format(time()-st)+'s'
          f' for {iter_num} assignment iterations and '
          f'{column_update_num} iterations in column generation')

    print('\npath finding results can be found in agent.csv')


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

    demo_mode(1)