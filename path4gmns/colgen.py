import ctypes
# import ray
# import multiprocessing as mp
# import threading
# import pathos.multiprocessing as mp
# import dill
# import dispy
from time import time

from .path import single_source_shortest_path
from .classes import Column, ColumnVec, MIN_OD_VOL, SPNetwork


__all__ = ['perform_network_assignment']


def _update_generalized_link_cost(links, link_cost_array, 
                                  tau=0, value_of_time=10):
    for link in links:
        link_cost_array[link.get_seq_no()] = (
            link.get_period_travel_time(tau)
            + link.get_route_choice_cost() 
            + link.get_toll() / value_of_time * 60
        )


def _update_link_travel_time_and_cost(links, demand_period_count, 
                                      agent_type_count):

    for link in links:
        link.calculate_td_vdfunction()
        for tau in range(demand_period_count):
            for at in range(agent_type_count):
                link.calculate_agent_marginal_cost(tau, at)


def _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                links,
                                                zones,
                                                demand_period_count, 
                                                agent_type_count,
                                                iter_num,
                                                is_path_vol_self_reducing):

    # the original implementation is iter_num < 0, which does not make sense
    if iter_num <= 0:
        return
    
    for link in links:
        for tau in range(demand_period_count):
            link.reset_period_flow_vol(tau)
            # link.queue_length_by_slot[tau] = 0
            for at in range(agent_type_count):
                link.reset_period_agent_vol(tau, at)

    for at in range(agent_type_count):
        for oz_id in zones:
            for dz_id in zones:
                for tau in range(demand_period_count):
                    if (at, tau, oz_id, dz_id) not in column_pool.keys():
                        continue

                    cv = column_pool[(at, tau, oz_id, dz_id)]
            
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


def _update_column_gradient_cost_and_flow(column_pool, links, 
                                          zones, demand_period_count, 
                                          agent_type_count, iter_num):
    total_gap = 0
    # total_gap_count = 0
    
    _reset_and_update_link_vol_based_on_columns(column_pool, 
                                                links,
                                                zones,
                                                demand_period_count, 
                                                agent_type_count,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(links, 
                                      demand_period_count, 
                                      agent_type_count)

    for orig_zone_id in zones:
        for dest_zone_id in zones:
            for at in range(agent_type_count):
                for tau in range(demand_period_count):
                    if (at, tau, orig_zone_id, dest_zone_id) not in column_pool.keys():
                        continue
                    
                    cv = column_pool[(at, tau, orig_zone_id, dest_zone_id)]
                    
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
                            path_travel_time += (
                                links[i].travel_time_by_period[tau]
                            )
                            path_gradient_cost += (
                                links[i].get_generalized_cost(tau, at)
                            )

                        col.set_toll(path_toll)
                        col.set_travel_time(path_travel_time)
                        col.set_gradient_cost(path_gradient_cost)

                        if column_num == 1:
                            # total_gap_count += (
                            #     path_gradient_cost * col.get_volume()
                            # )
                            break

                        if path_gradient_cost < least_gradient_cost:
                            least_gradient_cost = path_gradient_cost
                            least_gradient_cost_path_seq_no = col.get_seq_no()
                            least_gradient_cost_path_node_sum = node_sum

                    if column_num >= 2:
                        total_switched_out_path_vol = 0

                        for node_sum, col in cv.get_columns().items():
                            if col.get_seq_no() != least_gradient_cost_path_seq_no:
                                col.set_gradient_cost_abs_diff(
                                    col.get_gradient_cost() 
                                    - least_gradient_cost
                                )
                                col.set_gradient_cost_rel_diff(
                                    col.get_gradient_cost_abs_diff() 
                                    / max(0.0001, least_gradient_cost)
                                )

                                total_gap += (
                                    col.get_gradient_cost_abs_diff() 
                                    * col.get_volume()
                                )

                                # total_gap_count += (
                                #     col.get_gradient_cost() * col.get_volume()
                                # )

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

    print(f'total gap: {total_gap:.2f}')
    # print(f'total gap count is: {total_gap_count:.2f}')


def _optimize_column_pool(column_pool, links, 
                          zones, demand_period_count, 
                          agent_type_count,colum_update_num):

    for i in range(colum_update_num):
        print(f"current iteration number in column generation: {i}")
        _update_column_gradient_cost_and_flow(column_pool, links, 
                                              zones, demand_period_count, 
                                              agent_type_count, i)


def _backtrace_shortest_path_tree(orig_node_no,
                                  nodes,
                                  links,
                                  node_preds,
                                  link_preds,
                                  node_label_costs,
                                  column_pool,
                                  demand_period, 
                                  agent_type,
                                  iter_num):
    
    if not nodes[orig_node_no].has_outgoing_links():
        return

    oz_id = nodes[orig_node_no].get_zone_id()
    k_path_prob = 1 / (iter_num + 1)

    node_size = len(nodes)

    for i in range(node_size):
        if i == orig_node_no:
            continue

        dz_id = nodes[i].get_zone_id()
        if dz_id == -1:
            continue
        
        if (agent_type, demand_period, oz_id, dz_id) not in column_pool.keys():
            continue

        cv = column_pool[( agent_type, demand_period,oz_id, dz_id)]
        if cv.is_route_fixed():
            continue

        od_vol = cv.get_od_volume()
        if od_vol <= MIN_OD_VOL:
            continue
        
        vol = od_vol * k_path_prob

        node_path = []
        link_path = []

        dist = 0
        node_sum = 0
        current_node_seq_no = i
        # retrieve the sequence backwards
        while current_node_seq_no >= 0:
            node_path.append(current_node_seq_no)
            node_sum += current_node_seq_no
            
            current_link_seq_no = link_preds[current_node_seq_no]  
            if current_link_seq_no >= 0:
                link_path.append(current_link_seq_no)
                dist += links[current_link_seq_no].length
            
            current_node_seq_no = node_preds[current_node_seq_no]

        # make sure this is a valid path
        if not link_path:
            continue

        if node_sum not in cv.path_node_seq_map.keys():
            path_seq_no = cv.get_column_num()
            col = Column(path_seq_no)
            col.set_toll(node_label_costs[i])
            col.nodes = [x for x in node_path]
            col.links = [x for x in link_path]
            col.dist = dist
            cv.add_new_column(node_sum, col)

        cv.get_column(node_sum).increase_volume(vol)


def _update_column_travel_time(links, zones, column_pool, 
                               demand_period_count, agent_type_count):
    
    for oz in zones:
        for dz in zones:
            for at in range(agent_type_count):
                for tau in range(demand_period_count):
                    if (at, tau, oz, dz) not in column_pool.keys():
                        continue
                    
                    cv = column_pool[(at, tau, oz, dz)]

                    for col in cv.get_columns().values():
                        travel_time = sum(
                            links[j].travel_time_by_period[tau] for j in col.links
                        )
                        col.set_travel_time(travel_time)
            
# @ray.remote
def _assginment_core(spn, node_list, link_list, column_pool, vot, demand_period, agent_type, iter_num):

    for node_id in spn.orig_nodes:

        _update_generalized_link_cost(link_list, spn.link_cost_array, demand_period, vot)

        single_source_shortest_path(spn, node_id)
                    
        _backtrace_shortest_path_tree(spn.get_node_no(node_id),
                                      node_list,
                                      link_list,
                                      spn.node_predecessor,
                                      spn.link_predecessor,
                                      spn.node_label_cost,
                                      column_pool,
                                      demand_period, 
                                      agent_type,
                                      iter_num)


def _assignment(spnetworks, node_list, link_list, column_pool, agent_types, iter_num):
    # multiprocessing

    # pool = mp.Pool(mp.cpu_count())
    # pool.starmap(_assginment_core, [(spn, A.column_pool, iter_num) for spn in A.spnetworks])
    # [pool.apply(_assginment_core, args=(spn, A.column_pool, iter_num)) for spn in A.spnetworks]
    # pool.close()
    # q = mp.Queue()
    # processes = [mp.Process(target=_assginment_core, args=(spn, A.column_pool, iter_num, q)) for spn in A.spnetworks]
    
    # for p in processes:
    #     p.start()
    
    # for p in processes:
    #     p.join()

    # multi-threading
    # threads = []
    # for spn in spnetworks:
    #     t = threading.Thread(target=_assginment_core, args=(spn, node_list, link_list, column_pool, 10, 0, 0, iter_num,))
    #     threads.append(t)
    #     t.start()
    
    # for t in threads:
    #     t.join()

    # [_assginment_core.remote(spn, column_pool, 10, 0, 0, iter_num) for spn in spnetworks]

    # p = mp.Pool(4)
    # p.map(dill.dumps(_assginment_core), [(dill.dumps(spn), column_pool, 10, 0, 0, iter_num) for spn in spnetworks])

    # using dispy
    # cluster = dispy.JobCluster(_assginment_core, depends=[SPNetwork, _update_generalized_link_cost, single_source_shortest_path, _backtrace_shortest_path_tree])
    # jobs = []
    # for spn in spnetworks:
    #     vot = agent_types[spn.get_agent_type()].get_vot()
    #     at = spn.get_agent_type()
    #     dp = spn.get_demand_period()
    #     job = cluster.submit(spn, node_list, link_list, column_pool, vot, dp, at, iter_num)
    #     jobs.append(job)
    
    # for job in jobs:
    #     job()

    # cluster.print_status()

    flag = False
 
    # single processing
    for spn in spnetworks:
        vot = agent_types[spn.get_agent_type()].get_vot()
        at = spn.get_agent_type()
        dp = spn.get_demand_period()
        # if not flag:
        #     _update_generalized_link_cost(link_list, spn.link_cost_array, dp, vot)
        #     flag = True

        _assginment_core(spn, node_list, link_list, column_pool, vot, dp, at, iter_num)


def perform_network_assignment(assignment_mode, iter_num, column_update_num, A):
    """ perform network assignemnt using the selected assignment mode
    
    WARNING
    -------
        Only Path/Column-based User Equilibrium (UE) is implemented in Python.
        If you need other assignment modes or dynamic traffic assignment (DTA),
        please use perform_network_assignment_DTALite()
    
    Parameters
    ----------
    assignment_mode
        0: Link-based UE
        1: Path-based UE 
        2: UE + dynamic traffic assignment and simulation
        3: ODME
    iter_num
        number of assignment iterations to be performed before optimizing
        column pool
    column_update_iter
        number of iterations to be performed on optimizing column pool

    Outputs
    -------
        None

        You will need to call output_columns() and output_link_performance() to
        get the assignment results, i.e., paths/columns (in agent.csv) and 
        assigned volumes and other link attributes on each link (in l
        ink_performance.csv)
    """
    if assignment_mode != 1:
        raise Exception("not implemented yet")

    # ray.init()

    G = A.get_network()

    # this is important. 
    # otherwise, at iteration 0, _update_generalized_link_cost() is useless
    # link_cost_array may not be correctly set up
    # if not G.has_capi_allocated:
    #     G.allocate_for_CAPI()

    st = time()

    for i in range(iter_num):
        print(f"current iteration number in assignment: {i}")
        _update_link_travel_time_and_cost(G.link_list, 
                                          A.get_demand_period_count(),
                                          A.get_agent_type_count())
        
        _reset_and_update_link_vol_based_on_columns(A.column_pool, 
                                                    G.link_list,
                                                    G.zones,
                                                    A.get_demand_period_count(), 
                                                    A.get_agent_type_count(),
                                                    i,
                                                    True)

        # for node in G.node_list:
        _assignment(A.spnetworks, G.node_list, G.link_list, A.column_pool, A.agent_types, i)

    print('\nprocessing time of assignment:{0: .2f}'.format(time()-st)+ 's')

    _optimize_column_pool(A.column_pool,
                          G.link_list,
                          G.zones,
                          A.get_demand_period_count(), 
                          A.get_agent_type_count(),
                          column_update_num)

    _reset_and_update_link_vol_based_on_columns(A.column_pool, 
                                                G.link_list,
                                                G.zones,
                                                A.get_demand_period_count(), 
                                                A.get_agent_type_count(),
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(G.link_list, 
                                      A.get_demand_period_count(),
                                      A.get_agent_type_count())

    _update_column_travel_time(G.link_list, G.zones, A.column_pool,
                               A.get_demand_period_count(), 
                               A.get_agent_type_count())