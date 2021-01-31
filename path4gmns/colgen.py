from .path import single_source_shortest_path
from .classes import Column, ColumnVec, MAX_TIME_PERIODS, MAX_AGNET_TYPES, \
                     MIN_OD_VOL


__all__ = ['do_network_assignment']


# is this one duplicate with 
# get_generalized_first_order_gradient_cost_of_second_order_loss_for_agent_type
def _update_generalized_link_cost(links, link_genalized_costs, 
                                  tau=0, value_of_time=1):
    for link in links:
        link_genalized_costs[link.get_seq_no()] = (
            link.get_period_travel_time(tau)
            + link.get_route_choice_cost() 
            + link.get_toll() / value_of_time * 60
        )
	

def _update_link_travel_time_and_cost(links):
    for link in links:
        link.calculate_td_vdfunction()
        for tau in range(MAX_TIME_PERIODS):
            for at in range(MAX_AGNET_TYPES):
                link.calculate_agent_marginal_cost(tau, at)


def _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                links,
                                                zones,
                                                iter_num,
                                                is_path_vol_self_reducing):
    # the original implementation is iter_num < 0, which does not make sense
    if iter_num <= 0:
        return
    
    for link in links:
        for tau in range(MAX_TIME_PERIODS):
            link.reset_period_flow_vol(tau)
            # link.queue_length_by_slot[tau] = 0
            for at in range(MAX_AGNET_TYPES):
                link.reset_period_agent_vol(tau, at)

    for at in range(MAX_AGNET_TYPES):
        for orig_zone_id in zones:
            for dest_zone_id in zones:
                for tau in range(MAX_TIME_PERIODS):
                    if (orig_zone_id, dest_zone_id) not in column_pool.keys():
                        continue

                    cv = column_pool[(orig_zone_id, dest_zone_id)]
            
                    if cv.get_od_volume() <= 0:
                        continue
                    
                    for col in cv.get_columns().values():
                        link_vol_contributed_by_path_vol = col.get_volume()
                        for i in col.links:
                            pce_ratio = 1
                            links[i].increase_period_flow_vol(
                                tau,
                                link_vol_contributed_by_path_vol * pce_ratio
                            )
                            links[i].increase_period_agent_vol(
                                tau,
                                at,
                                link_vol_contributed_by_path_vol
                            )

                        if not cv.is_route_fixed() \
                           and is_path_vol_self_reducing:
                            col.vol *= iter_num / (iter_num + 1)
                    # end of for column in ...
                # end of for tau in ...
            # end of for dest_zone_id in ...
        # end of for origi_zone_id in ...
    # end of for at in range ...


def _update_column_gradient_cost_and_flow(column_pool, links, zones, iter_num):
    total_gap_count = 0
    
    _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                links,
                                                zones,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(links)

    for orig_zone_id in zones:
        for dest_zone_id in zones:
            for at in range(MAX_AGNET_TYPES):
                for tau in range(MAX_TIME_PERIODS):
                    if (orig_zone_id, dest_zone_id) not in column_pool.keys():
                        continue
                    
                    cv = column_pool[(orig_zone_id, dest_zone_id)]
                    
                    if cv.get_od_volume() <= 0:
                        continue

                    column_num = cv.get_column_num()
                    least_gradient_cost = 999999
                    least_gradient_cost_path_seq_no = -1
                    least_gradient_cost_path_node_sum = -1

                    for node_sum, col in cv.get_columns().items():
                        path_toll = 0
                        path_gradient_cost = 0
                        path_travel_time = 0
                        for i in col.get_links():
                            path_toll += links[i].get_toll()
                            link_travel_time = (
                                links[i].travel_time_by_period[tau]
                            )
                            path_travel_time += link_travel_time
                            path_gradient_cost += (
                                links[i].get_generalized_cost(tau, at)
                            )

                        col.set_toll(path_toll)
                        col.set_travel_time(path_travel_time)
                        col.set_gradient_cost(path_gradient_cost)

                        if column_num == 1:
                            total_gap_count += (
                                path_gradient_cost * col.get_volume()
                            )
                            break

                        if path_gradient_cost < least_gradient_cost:
                            least_gradient_cost = path_gradient_cost
                            least_gradient_cost_path_seq_no = col.get_seq_no()
                            least_gradient_cost_path_node_sum = node_sum

                    if column_num >= 2:
                        total_switched_out_path_vol = 0

                        for node_sum, col in cv.get_columns().items():
                            if col.path_no != least_gradient_cost_path_seq_no:
                                col.set_gradient_cost_abs_diff(
                                    col.get_gradient_cost() 
                                    - least_gradient_cost
                                )
                                col.set_gradient_cost_rel_diff(
                                    col.get_gradient_cost_abs_diff() 
                                    / max(0.00001, least_gradient_cost)
                                )

                                total_gap += (
                                    col.get_gradient_cost_abs_diff() 
                                    * col.get_volume()
                                )
                                total_gap_count += (
                                    col.get_gradient_cost() * col.get_volume()
                                )

                                step_size = (
                                    1 / (iter_num + 2) * cv.get_od_volume()
                                )

                                previous_path_vol = col.get_volume()
                                col.vol = max(
                                    0, 
                                    (previous_path_vol 
                                     - step_size 
                                     * col.get_gradient_cost_rel_diff())
                                )

                                col.set_switch_volume(
                                    previous_path_vol - col.get_volume()
                                )
                                total_switched_out_path_vol += (
                                    col.get_switch_volume()
                                )

                    if least_gradient_cost_path_seq_no != -1:
                        col = cv.get_column(
                            least_gradient_cost_path_node_sum
                        )
                        col.increase_volume(total_switched_out_path_vol)
                        total_gap_count += (
                            col.get_gradient_cost() * col.get_volume()
                        )                    


def _optimize_column_pool(column_pool, links, zones, iter_num):
    for i in range(iter_num):
        print(f"current iteration number: {i}")
        _update_column_gradient_cost_and_flow(column_pool, links, zones, i)


def _backtrace_shortest_path_tree(orig_node_id,
                                  id_to_no_dict,
                                  nodes,
                                  node_preds,
                                  link_preds,
                                  node_label_costs,
                                  column_pool,
                                  iter_num):
    
    orig_node_no = id_to_no_dict[orig_node_id]
    
    if not nodes[orig_node_no].has_outgoing_links():
        return

    orig_zone_id = nodes[orig_node_no].get_zone_id()
    k_path_prob = 1 / (iter_num + 1)

    node_size = len(nodes)

    for i in range(node_size):
        if i == orig_node_no:
            continue

        dest_zone_id = nodes[i].get_zone_id()
        if dest_zone_id == -1:
            continue
        
        if (orig_zone_id, dest_zone_id) not in column_pool.keys():
            continue

        cv = column_pool[(orig_zone_id, dest_zone_id)]
        if cv.is_route_fixed():
            continue

        od_vol = cv.get_od_volume()
        if od_vol <= MIN_OD_VOL:
            continue
        
        vol = od_vol * k_path_prob

        node_path = []
        link_path = []

        node_sum = 0
        current_node_seq_no = i
        # retrieve the sequence backwards
        while current_node_seq_no >= 0:
            node_path.append(current_node_seq_no)
            node_sum += current_node_seq_no
            
            current_link_seq_no = link_preds[current_node_seq_no]  
            if current_link_seq_no >= 0:
                link_path.append(current_link_seq_no)
            
            current_node_seq_no = node_preds[current_node_seq_no]
        
        if node_sum not in cv.path_node_seq_map.keys():
            path_seq_no = cv.get_column_num()
            col = Column(path_seq_no)
            col.increase_toll(node_label_costs[i])
            col.nodes = [x for x in node_path]
            col.links = [x for x in link_path]
            cv.get_column(node_sum).set_volume(vol)

        cv.get_column(node_sum).increase_vol(vol)
            

def do_network_assignment(iter_num, assignment_mode, column_update_iter, G):
    if assignment_mode == 0:
        raise Exception("not implemented yet")

    for i in range(iter_num):
        _update_link_travel_time_and_cost(G.link_list)
        _reset_and_update_link_vol_based_on_columns(G.column_pool, 
                                                    G.link_list,
                                                    G.zones,
                                                    i,
                                                    True)

        for node in G.node_list:
            _update_generalized_link_cost(G.link_list, 
                                          G.link_genalized_cost_array)
            # single_source_shortest_path(G, 
            #                             node.external_node_id,
            #                             engine_type='python',
            #                             sp_algm='dijkstra')
            single_source_shortest_path(G, node.external_node_id)
                        
            _backtrace_shortest_path_tree(node.external_node_id,
                                          G.internal_node_seq_no_dict,
                                          G.node_list,
                                          G.node_predecessor,
                                          G.link_predecessor,
                                          G.node_label_cost,
                                          G.column_pool,
                                          iter_num)

    _optimize_column_pool(G.column_pool, G.link_list,
                          G.zones, column_update_iter)

    _reset_and_update_link_vol_based_on_columns(G.column_pool, 
                                                G.link_list,
                                                G.zones,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(G.link_list)