from .path import single_source_shortest_path
from .classes import Column, ColumnVec


MIN_OD_VOL = 0.000001
MAX_TIME_PERIODS = 1
MAX_AGNET_TYPES = 1

# is this one duplicate with get_generalized_first_order_gradient_cost_of_second_order_loss_for_agent_type?
def update_generalized_link_cost(link_list, link_genalized_cost_array, tau=0, value_of_time=1):
    for link in link_list:
        link_genalized_cost_array[link.link_seq_no] = link.travel_time_per_period[tau] + link.route_choice_cost + link.toll / value_of_time * 60
	

def update_link_travel_time_and_cost(link_list):
    for link in link_list:
        link.calculate_TD_VDFunction()
        for tau in range(MAX_TIME_PERIODS):
            for at in range(MAX_AGNET_TYPES):
                PCE_agent_type = 1
                link.calculate_marginal_cost_for_agent_type(tau, at, PCE_agent_type)


def reset_and_update_link_vol_based_on_columns(column_pool, link_list, zones, iter_num, is_path_vol_self_reducing):
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
                    pColumnVec = column_pool[orig_zone_id][dest_zone_id]
            
                    if pColumnVec.get_od_volume() <= 0:
                        continue
                    
                    for column in pColumnVec.path_node_seq_map.values():
                        link_volume_contributed_by_path_volume = column.vol
                        for link in column.links:
                            PCE_ratio = 1
                            link_list[link].flow_vol_by_period[tau] += link_volume_contributed_by_path_volume * PCE_ratio
                            link_list[link].vol_by_period_by_at[tau][at] += link_volume_contributed_by_path_volume

                        if not pColumnVec.is_route_fixed() and is_path_vol_self_reducing:
                            column.vol *= iter_num / (iter_num + 1)
                    # end of for column in ...
                # end of for tau in ...
            # end of for dest_zone_id in ...
        # end of for origi_zone_id in ...
    # end of for at in range ...

def update_gradient_cost_and_assigned_flow_in_column_pool(G, A, iter_num, link_size):
    total_gap_count = 0
    
    reset_and_update_link_vol_based_on_columns(A, G.link_list, G.zones, iter_num, False)
    update_link_travel_time_and_cost(G.link_list)

    value_of_time = 1
    for orig_zone_id in G.zones:
        for dest_zone_id in G.zones:
            for at in range(MAX_AGNET_TYPES):
                for tau in range(MAX_TIME_PERIODS):
                    pColumnVec = A.column_pool[orig_zone_id][dest_zone_id]
                    
                    if pColumnVec.get_od_volume() <= 0:
                        continue

                    column_num = pColumnVec.get_column_num()
                    least_gradient_cost = 999999
                    least_gradient_cost_path_seq_no = -1
                    least_gradient_cost_path_node_sum = -1

                    for node_sum, column in pColumnVec.path_node_seq_map:
                        path_toll = 0
                        path_gradient_cost = 0
                        # path_distance = 0
                        path_travel_time = 0
                        for link in column.links:
                            path_toll += G.link_list[link].toll
                            # path_distance += G.link_list[link].length
                            link_travel_time = G.link_list[link].travel_time_by_period
                            path_travel_time += link_travel_time
                            path_gradient_cost += G.link_list[link].get_generalized_first_order_gradient_cost_of_second_order_loss_for_agent_tpye(tau, at, value_of_time)

                        column.toll = path_toll
                        column.travel_time = path_travel_time
                        column.gradient_cost = path_gradient_cost

                        if column_num == 1:
                            total_gap_count += path_gradient_cost * column.vol
                            break

                        if path_gradient_cost < least_gradient_cost:
                            least_gradient_cost = path_gradient_cost
                            least_gradient_cost_path_seq_no = column.seq_no
                            least_gradient_cost_path_node_sum = node_sum

                    if column_num >= 2:
                        total_switched_out_path_volume = 0

                        for node_sum, column in pColumnVec.path_node_seq_map.items():
                            if column.path_no != least_gradient_cost_path_seq_no:
                                column.gradient_cost_abs_diff = column.gradient_cost - least_gradient_cost
                                column.gradient_cost_rel_diff = column.gradient_cost_abs_diff / max(0.00001, least_gradient_cost)

                                total_gap += column.gradient_cost_abs_diff * column.vol
                                total_gap_count += column.gradient_cost * column.vol

                                step_size = 1 / (iter_num + 2) * column.get_od_volume()

                                previous_path_volume = column.vol
                                column.vol = max(0, previous_path_volume - step_size * column.gradient_cost_rel_diff)

                                column.switch_vol = (previous_path_volume - column.vol)
                                total_switched_out_path_volume += column.switch_vol

                    if least_gradient_cost_path_seq_no != -1:
                        column = pColumnVec.path_node_seq_map[least_gradient_cost_path_node_sum]
                        column.vol += total_switched_out_path_volume
                        total_gap_count += column.gradient_cost * column.vol


def optimize_column_pool(A, iter_num, link_size):
    for i in range(iter_num):
        print(f"current iteration number: {i}")
        update_gradient_cost_and_assigned_flow_in_column_pool(A, i, iter_num, link_size)


def backtrace_shortest_path_tree(G, A, iter_num, orig_node_no):
    if not G.node_list[orig_node_no].outgoing_link_list:
        return

    orig_zone_id = G.node_list[orig_node_no].zone_id
    k_path_prob = 1 / (iter_num + 1)

    node_size = G.node_size

    for i in range(node_size):
        if i == orig_node_no:
            continue

        dest_zone_id = G.node_list[i].zone_id
        if dest_zone_id == -1:
            continue
        
        pColumnVec = A.column_pool[orig_zone_id][dest_zone_id]
        if pColumnVec.is_route_fixed():
            continue

        od_vol = pColumnVec.get_od_volume()
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
            
            current_link_seq_no = G.link_predecessor[current_node_seq_no]  
            if current_link_seq_no >= 0:
                link_path.append(current_link_seq_no)
            
            current_node_seq_no = G.node_predecessor[current_node_seq_no]
        
        if node_sum not in pColumnVec.path_node_seq_map.keys():
            path_seq_no = pColumnVec.path_node_seq_map.size()
            column = Column(path_seq_no)
            column.increase_path_toll(G.label_cost[i])
            pColumnVec.path_node_seq_map[node_sum] = column

        pColumnVec.path_node_seq_map[node_sum].increase_path_vol(vol)
            

def do_network_assignment(iter_num, assignment_mode, column_update_iter, G, A):
    if assignment_mode == 0:
        raise Exception("not implemented yet")
    
    node_size = G.node_size
    link_size = G.link_size

    for i in range(iter_num):
        update_link_travel_time_and_cost(G.link_list)
        reset_and_update_link_vol_based_on_columns(A.column_pool, link_size, G.zones, i, True)

        for j in range(node_size):
            UpdateGeneralizedLinkCost(G.link_list, G.link_genalized_cost_array)
            single_source_shortest_path(G, j)
            backtrace_shortest_path_tree(G, A, iter_num, j)

    optimize_column_pool(A, iter_num, link_size)

    reset_and_update_link_vol_based_on_columns(A.column_pool, link_size, G.zones, iter_num, False)
    update_link_travel_time_and_cost(G.link_list)