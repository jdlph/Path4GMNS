import path4gmns as pg


if __name__=="__main__":
    network = pg.read_network()
    print('the shortest path from node 1 to node 2 is '
          +str(pg.find_shortest_path(network, 1, 2)))
    
    pg.find_path_for_agents(network)
    agent = network.agent_list[0]
    print('the shortest path (node sequence) of agent 0 is ' 
          + str(agent.path_node_seq_no_list))
    print('the shortest path (link sequence) of agent 0 is ' 
          + str(agent.path_link_seq_no_list))