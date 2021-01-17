import csv
from random import choice

from .classes import Node, Link, Network, Agent


def read_nodes(input_dir, node_list, internal_node_seq_no_dict,
               external_node_id_dict, zone_to_nodes_dict):
    """ step 1: read input_node """
    with open(input_dir+'/node.csv', 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        node_seq_no = 0
        for line in reader:
            # set up node_id, which should be an integer
            node_id = line['node_id']
            if not node_id:
                continue
            node_id = int(node_id)
            
            # set up zone_id, which should be an integer
            zone_id = line['zone_id']
            if not zone_id:
                zone_id = -1
            else:
                zone_id = int(zone_id)
            
            # construct node object
            node = Node(node_seq_no, node_id, zone_id)
            node_list.append(node)
            
            # set up mapping between node_seq_no and node_id
            internal_node_seq_no_dict[node_id] = node_seq_no
            external_node_id_dict[node_seq_no] = node_id
            
            # associate node_id to corresponding zone
            if zone_id not in zone_to_nodes_dict.keys():
                zone_to_nodes_dict[zone_id] = []
            zone_to_nodes_dict[zone_id].append(node_id)
            
            node_seq_no += 1
        
        print(f"the number of nodes is {node_seq_no}")
    fp.close()


def read_links(input_dir, link_list, node_list, internal_node_seq_no_dict):
    """ step 2: read input_link """
    with open(input_dir+'/link.csv', 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        link_seq_no = 0
        for line in reader:
            # check the validility 
            from_node_id = line['from_node_id']
            if not from_node_id:
                continue
            to_node_id = line['to_node_id']
            if not to_node_id:
                continue
            length = line['length']
            if not length:
                continue

            # pass validility check
            from_node_id = int(from_node_id)
            to_node_id = int(to_node_id)
            length = float(length)

            # for the following attributes, 
            # if they are not None, convert them to the corresponding types
            # leave None's to the default constructor
            lanes = line['lanes']
            if lanes:
                lanes = int(lanes)
            
            free_speed = line['free_speed']
            if free_speed:
                free_speed = int(free_speed)
            
            capacity = line['capacity']
            if capacity:
                capacity = int(capacity)
            
            link_type = line['link_type']
            if link_type:
                link_type = int(link_type)
            
            VDF_alpha = line['VDF_alpha1']
            if VDF_alpha:
                VDF_alpha = float(VDF_alpha)    
            
            VDF_beta = line['VDF_beta1']
            if VDF_beta:
                VDF_beta = float(VDF_beta)

            try:
                from_node_no = internal_node_seq_no_dict[from_node_id]
                to_node_no = internal_node_seq_no_dict[to_node_id]
            except KeyError:
                print(f"EXCEPTION: Node ID {from_node_no} "
                      f"or/and Node ID {to_node_id} NOT IN THE NETWORK!!")
                continue
            
            # construct link ojbect
            link = Link(link_seq_no, 
                        from_node_no, 
                        to_node_no,
                        from_node_id,
                        to_node_id,
                        length,
                        lanes,
                        link_type,
                        free_speed,
                        capacity,
                        VDF_alpha,
                        VDF_beta)
            
            # set up outgoing links and incoming links
            node_list[from_node_no].outgoing_link_list.append(link)
            node_list[to_node_no].incoming_link_list.append(link)
            link_list.append(link)
            
            link_seq_no += 1
        
        print(f"the number of links is {link_seq_no}")
    fp.close()
    

def read_agents(input_dir,
                agent_list,
                agent_td_list_dict,
                zone_to_nodes_dict):
    """ step 3:read input_agent """
    with open(input_dir+'/demand.csv', 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        agent_id = 1
        agent_type = 'v'
        agent_seq_no = 0
        for line in reader:
            volume = line['volume']
            volume_agent_size = int(float(volume) + 1)
    
            # only test up to 10k
            if agent_id >= 10000 :
                break 
    
            for i in range(volume_agent_size):
                # invalid origin zone id, discard it
                o_zone_id = line['o_zone_id']
                if not o_zone_id:
                    continue
                # invalid destinationzone id, discard it
                d_zone_id = line['d_zone_id']
                if not d_zone_id:
                    continue
                
                o_zone_id = int(o_zone_id)
                # o_zone_id does not exist in node.csv, discard it
                if o_zone_id not in zone_to_nodes_dict.keys():
                    continue
                
                d_zone_id = int(d_zone_id)
                # d_zone_id does not exist in node.csv, discard it
                if d_zone_id not in zone_to_nodes_dict.keys():
                    continue

                # construct agent using valid record
                agent = Agent(agent_id,
                              agent_seq_no,
                              agent_type,
                              o_zone_id, 
                              d_zone_id)

                # step 3.1 generate o_node_id and d_node_id randomly according 
                # to o_zone_id and d_zone_id 
                agent.o_node_id = choice(zone_to_nodes_dict[o_zone_id])
                agent.d_node_id = choice(zone_to_nodes_dict[d_zone_id])
                
                # step 3.2 update agent_id and agent_seq_no
                agent_id += 1
                agent_seq_no += 1 

                # step 3.3: update the g_simulation_start_time_in_min and 
                # g_simulation_end_time_in_min 
                # if agent.departure_time_in_min < g_simulation_start_time_in_min:
                #     g_simulation_start_time_in_min = agent.departure_time_in_min
                # if agent.departure_time_in_min > g_simulation_end_time_in_min:
                #     g_simulation_end_time_in_min = agent.departure_time_in_min

                #step 3.4: add the agent to the time dependent agent list
                departure_time = agent.departure_time_in_simu_interval
                if departure_time not in agent_td_list_dict.keys():
                    agent_td_list_dict[departure_time] = []
                agent_td_list_dict[departure_time].append(agent.agent_seq_no)
                
                agent_list.append(agent)

    print(f"the number of agents is {agent_seq_no}")

    #step 3.6:sort agents by the departure time
    agent_list.sort(key=lambda agent: agent.departure_time_in_min)
    for i, agent in enumerate(agent_list):
        agent.agent_seq_no = i


def read_network(input_dir='./'):
    network = Network()

    read_nodes(input_dir,
               network.node_list,
               network.internal_node_seq_no_dict,
               network.external_node_id_dict,
               network.zone_to_nodes_dict)

    read_links(input_dir, 
               network.link_list,
               network.node_list,
               network.internal_node_seq_no_dict)

    read_agents(input_dir,
                network.agent_list,
                network.agent_td_list_dict,
                network.zone_to_nodes_dict)

    network.update()

    return network