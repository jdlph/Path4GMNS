import csv

from .classes import Node, Link, Network


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

    network.update()

    return network