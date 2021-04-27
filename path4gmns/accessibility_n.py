from path4gmns.path import single_source_shortest_path
from path4gmns.classes import AccessNetwork


def _update_generalized_link_cost_a(G, at):
    """ update generalized link costs to calculate accessibility """
    vot = at.get_vot()
    ffs = at.get_free_flow_speed()

    if at.get_type().startswith('p'):
        for link in G.get_links():
            G.link_cost_array[link.get_seq_no()] = (
            link.get_free_flow_travel_time()
            + link.get_route_choice_cost()
            + link.get_toll() / min(0.001, vot) * 60
        )
    else:
        for link in G.get_links():
            G.link_cost_array[link.get_seq_no()] = (
            (link.get_length() / max(0.001, ffs) * 60)
            + link.get_route_choice_cost()
            + link.get_toll() / min(0.001, vot) * 60
        )


def evaluate_accessibility(ui, multimodal=True, output_dir='.'):
    base = ui._base_assignment

    an = AccessNetwork(base.network)

    min_travel_times = {}
    if multimodal:
        for at in base.get_agent_types():
            at_type_str = at.get_type()
            # update generalized link costs
            _update_generalized_link_cost_a(an, at)
            
            for c in an.get_centroids():
                node_id = c.get_node_id()
                node_no = c.get_node_no()
                zone_id = c.get_zone_id()
                single_source_shortest_path(an, node_id)
                for c_ in an.get_centroids():
                    if c_ == c:
                        continue

                    to_zone_id = c_.get_zone_id()
                    min_travel_times[(zone_id, to_zone_id, at_type_str)] = an.get_node_label_costs(node_no)

    else:
        at = base.get_agent_type('p')
        at_type_str = at.get_type()
        # update generalized link costs
        _update_generalized_link_cost_a(an, at)
        
        for c in an.get_centroids():
            node_id = c.get_node_id()
            node_no = c.get_node_no()
            zone_id = c.get_zone_id()
            single_source_shortest_path(an, node_id)
            for c_ in an.get_centroids():
                if c_ == c:
                    continue

                to_zone_id = c_.get_zone_id()
                min_travel_times[(zone_id, to_zone_id, at_type_str)] = an.get_node_label_costs(node_no)