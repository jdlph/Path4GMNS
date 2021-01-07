import csv
import operator
from random import choice

from .classes import Node, Link, Network, Agent


def read_nodes(input_dir, node_list, internal_node_seq_no_dict,
               external_node_id_dict, zone_to_nodes_dict):
    """ step 1: read input_node """
    with open(input_dir+'/node.csv', 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        node_seq_no = 0
        for line in reader:
            node = Node(node_seq_no, line['node_id'], line['zone_id'])
            node_list.append(node)
            internal_node_seq_no_dict[node.external_node_id] = node_seq_no
            external_node_id_dict[node_seq_no] = node.external_node_id
            if node.zone_id not in zone_to_nodes_dict.keys():
                zone_to_nodes_dict[int(node.zone_id)] = list()
                zone_to_nodes_dict[int(node.zone_id)].append(
                    node.external_node_id
                )
            else:
                zone_to_nodes_dict[int(node.zone_id)].append(
                    node.external_node_id
                )
            node_seq_no += 1
        print('the number of nodes is', node_seq_no)
    fp.close()


def read_links(input_dir, link_list, node_list, internal_node_seq_no_dict):
    """ step 2: read input_link """
    with open(input_dir+'/link.csv', 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        link_seq_no = 0
        for line in reader:
            from_node_no = internal_node_seq_no_dict[int(line['from_node_id'])]
            to_node_no = internal_node_seq_no_dict[int(line['to_node_id'])]
            link = Link(link_seq_no, 
                        from_node_no, 
                        to_node_no,
                        int(line['from_node_id']),
                        int(line['to_node_id']),
                        line['length'],
                        line['lanes'],
                        line['free_speed'],
                        line['capacity'],
                        line['link_type'],
                        line['VDF_alpha1'],
                        line['VDF_beta1'])
            node_list[link.from_node_seq_no].outgoing_link_list.append(link)
            node_list[link.to_node_seq_no].incoming_link_list.append(link)
            link_list.append(link)
            link_seq_no += 1
        print('the number of links is', link_seq_no)
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
                agent = Agent(agent_id,
                              agent_seq_no,
                              agent_type,
                              line['o_zone_id'], 
                              line['d_zone_id'])

                # step 3.1 generate o_node_id and d_node_id randomly according 
                # to o_zone_id and d_zone_id 
                if zone_to_nodes_dict.get(agent.o_zone_id, -1) == -1 : 
                     continue
                if zone_to_nodes_dict.get(agent.d_zone_id, -1) == -1 : 
                     continue 
                
                agent.o_node_id = choice(zone_to_nodes_dict[agent.o_zone_id])
                agent.d_node_id = choice(zone_to_nodes_dict[agent.d_zone_id])
                
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
                if agent.departure_time_in_simu_interval not in agent_td_list_dict.keys():
                    agent_td_list_dict[agent.departure_time_in_simu_interval] = list()
                    agent_td_list_dict[agent.departure_time_in_simu_interval].append(agent.agent_seq_no)
                else:
                    agent_td_list_dict[agent.departure_time_in_simu_interval].append(agent.agent_seq_no)
                agent_list.append(agent)

    print('the number of agents is', len(agent_list))

    #step 3.6:sort agents by the departure time
    sort_fun = operator.attrgetter("departure_time_in_min")
    agent_list.sort(key=sort_fun)
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