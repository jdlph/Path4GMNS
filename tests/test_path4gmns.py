import path4gmns as pg
from time import time


if __name__=="__main__":
    network = pg.read_network()
    print('\nshortest path (external node sequence) from node 1 to node 2 is '
          +str(pg.find_shortest_path(network, 1, 2)))
    
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

    print('\nstart column generation')
    st = time()
    iter_num = 5
    colum_update_num = 5
    pg.do_network_assignment(1, iter_num, colum_update_num, network)
    print('processing time of column generation:{0: .2f}'
          .format(time()-st)+ 's'
          f' for {iter_num} assignment iterations and '
          f'{colum_update_num} iterations in column generation')