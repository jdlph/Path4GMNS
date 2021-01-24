from .path import single_source_shortest_path
from .classes import Column, ColumnVec, MAX_TIME_PERIODS, MAX_AGNET_TYPES, \
                     MIN_OD_VOL


__all__ = ['do_network_assignment']


# is this one duplicate with 
# get_generalized_first_order_gradient_cost_of_second_order_loss_for_agent_type
def _update_generalized_link_cost(link_list, 
                                  link_genalized_cost_arr, 
                                  tau=0,
                                  value_of_time=1):
    for link in link_list:
        link_genalized_cost_arr[link.link_seq_no] = (
            link.travel_time_by_period[tau] 
            + link.route_choice_cost 
            + link.toll / value_of_time * 60
        )
	

def _update_link_travel_time_and_cost(link_list):
    for link in link_list:
        link.calculate_TD_VDFunction()
        for tau in range(MAX_TIME_PERIODS):
            for at in range(MAX_AGNET_TYPES):
                PCE_agent_type = 1
                link.calculate_marginal_cost_for_agent_type(tau, 
                                                            at,
                                                            PCE_agent_type)


def _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                link_list,
                                                zones,
                                                iter_num,
                                                is_path_vol_self_reducing):
    # the original implementation is iter_num < 0, which does not make sense
    if iter_num <= 0:
        return
    
    for link in link_list:
        for tau in range(MAX_TIME_PERIODS):
            link.flow_vol_by_period[tau] = 0
            # link.queue_length_by_slot[tau] = 0
            for at in range(MAX_AGNET_TYPES):
                link.vol_by_period_by_at[tau][at] = 0

    for at in range(MAX_AGNET_TYPES):
        for orig_zone_id in zones:
            for dest_zone_id in zones:
                for tau in range(MAX_TIME_PERIODS):
                    if (orig_zone_id, dest_zone_id) not in column_pool.keys():
                        continue

                    cv = column_pool[(orig_zone_id, dest_zone_id)]
            
                    if cv.get_od_volume() <= 0:
                        continue
                    
                    for col in cv.path_node_seq_map.values():
                        link_vol_contributed_by_path_vol = col.vol
                        for i in col.links:
                            PCE_ratio = 1
                            link_list[i].flow_vol_by_period[tau] += (
                                link_vol_contributed_by_path_vol * PCE_ratio
                            )
                            link_list[i].vol_by_period_by_at[tau][at] += (
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


def _update_gradient_cost_and_assigned_flow_in_column_pool(column_pool,
                                                           link_list,
                                                           zones,
                                                           iter_num):
    total_gap_count = 0
    
    _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                link_list,
                                                zones,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(link_list)

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

                    for node_sum, col in cv.path_node_seq_map.items():
                        path_toll = 0
                        path_gradient_cost = 0
                        path_travel_time = 0
                        for i in col.links:
                            path_toll += link_list[i].toll
                            link_travel_time = (
                                link_list[i].travel_time_by_period[tau]
                            )
                            path_travel_time += link_travel_time
                            path_gradient_cost += (
                                link_list[i].get_generalized_link_cost(tau, at)
                            )

                        col.toll = path_toll
                        col.travel_time = path_travel_time
                        col.gradient_cost = path_gradient_cost

                        if column_num == 1:
                            total_gap_count += path_gradient_cost * col.vol
                            break

                        if path_gradient_cost < least_gradient_cost:
                            least_gradient_cost = path_gradient_cost
                            least_gradient_cost_path_seq_no = col.seq_no
                            least_gradient_cost_path_node_sum = node_sum

                    if column_num >= 2:
                        total_switched_out_path_vol = 0

                        for node_sum, col in cv.path_node_seq_map.items():
                            if col.path_no != least_gradient_cost_path_seq_no:
                                col.gradient_cost_abs_diff = (
                                    col.gradient_cost - least_gradient_cost
                                )
                                col.gradient_cost_rel_diff = (
                                    col.gradient_cost_abs_diff 
                                    / max(0.00001, least_gradient_cost)
                                )

                                total_gap += (
                                    col.gradient_cost_abs_diff * col.vol
                                )
                                total_gap_count += col.gradient_cost * col.vol

                                step_size = (
                                    1 / (iter_num + 2) * col.get_od_volume()
                                )

                                previous_path_vol = col.vol
                                col.vol = max(
                                    0, 
                                    previous_path_vol 
                                    - step_size * col.gradient_cost_rel_diff)

                                col.switch_vol = previous_path_vol - col.vol
                                total_switched_out_path_vol += col.switch_vol

                    if least_gradient_cost_path_seq_no != -1:
                        col = cv.path_node_seq_map[
                            least_gradient_cost_path_node_sum
                        ]
                        col.vol += total_switched_out_path_vol
                        total_gap_count += col.gradient_cost * col.vol


def _optimize_column_pool(column_pool, link_list, zones, iter_num):
    for i in range(iter_num):
        print(f"current iteration number: {i}")
        _update_gradient_cost_and_assigned_flow_in_column_pool(column_pool,
                                                               link_list,
                                                               zones,
                                                               i)


def _backtrace_shortest_path_tree(origin_node_id,
                                  internal_node_seq_no_dict,
                                  node_list,
                                  node_predecessor,
                                  link_predecessor,
                                  node_label_cost,
                                  column_pool,
                                  iter_num):
    orig_node_no = internal_node_seq_no_dict[origin_node_id]
    
    if not node_list[orig_node_no].outgoing_link_list:
        return

    orig_zone_id = node_list[orig_node_no].zone_id
    k_path_prob = 1 / (iter_num + 1)

    node_size = len(node_list)

    for i in range(node_size):
        if i == orig_node_no:
            continue

        dest_zone_id = node_list[i].zone_id
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
            
            current_link_seq_no = link_predecessor[current_node_seq_no]  
            if current_link_seq_no >= 0:
                link_path.append(current_link_seq_no)
            
            current_node_seq_no = node_predecessor[current_node_seq_no]
        
        if node_sum not in cv.path_node_seq_map.keys():
            path_seq_no = cv.get_column_num()
            col = Column(path_seq_no)
            col.increase_path_toll(node_label_cost[i])
            col.nodes = [x for x in node_path]
            col.links = [x for x in link_path]
            cv.path_node_seq_map[node_sum] = col

        cv.path_node_seq_map[node_sum].increase_path_vol(vol)
            

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

    _optimize_column_pool(G.column_pool,
                          G.link_list,
                          G.zones,
                          column_update_iter)

    _reset_and_update_link_vol_based_on_columns(G.column_pool, 
                                                G.link_list,
                                                G.zones,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(G.link_list)