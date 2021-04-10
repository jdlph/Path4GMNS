from .classes import Link

def setup_network(ui):
    # get number of zones
    G = ui._base_assignment.get_network()
    zone_num = len(G.get_zones())

    connectors = []
    i = 0
    for j, z in enumerate(G.get_zones()):
        for node in G.get_nodes_from_zone(z):
            c_out = Link(i, i, j, node.get_node_no(), i, node.get_node_id(), 0, 1, 3)
            c_in = Link(i+1, i+1, node.get_node_no(), j, node.get_node_id(), i, 0, 1, 3)
            connectors.append(c_out)
            connectors.append(c_in)
            i += 1