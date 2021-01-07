import path4gmns as pg


if __name__=="__main__":
    network = pg.read_network()
    print('shortest path (external node sequence) from node 1 to node 2 is '
          +str(pg.find_shortest_path(network, 1, 2)))
    
    pg.find_path_for_agents(network)
    agent = network.agent_list[300]
    print('origin node id of agent is '+str(agent.o_node_id))
    print('destination node id of agent is '+str(agent.d_node_id))
    print('shortest path (internal node sequence) of agent is ' 
          + str(agent.path_node_seq_no_list))
    print('shortest path (internal link sequence) of agent is ' 
          + str(agent.path_link_seq_no_list))