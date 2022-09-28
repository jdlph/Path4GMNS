from time import time

from .path import single_source_shortest_path
from .classes import Column
from .consts import MAX_LABEL_COST, SMALL_DIVISOR


__all__ = ['perform_column_generation', 'perform_network_assignment']


def _update_generalized_link_cost(spnetworks):
    """ update generalized link costs for each SPNetwork

    warning: there would be duplicate updates for SPNetworks with the same tau
    and vot belonging to different memory blocks. It could be resolved by
    creating a shared network among them??
    """
    for sp in spnetworks:
        tau = sp.get_demand_period().get_id()
        vot = sp.get_agent_type().get_vot()

        for link in sp.get_links():
            if link.length == 0:
                continue

            sp.link_cost_array[link.get_seq_no()] = (
                link.get_generalized_cost(tau, vot)
            )


def _update_link_travel_time_and_cost(links, demand_periods=None, iter_num=None):
    for link in links:
        if link.length == 0:
            continue

        link.calculate_td_vdf(demand_periods, iter_num)


def _reset_and_update_link_vol_based_on_columns(column_pool,
                                                links,
                                                demand_periods,
                                                iter_num,
                                                is_path_vol_self_reducing):
    # the original implementation is iter_num < 0, which does not make sense
    if iter_num == 0:
        return

    for link in links:
        if link.length == 0:
            continue

        for dp in demand_periods:
            tau = dp.get_id()
            link.reset_period_flow_vol(tau)

    for k, cv in column_pool.items():
        # k= (at, tau, oz_id, dz_id)
        tau = k[1]

        for col in cv.get_columns():
            path_vol = col.get_volume()
            for i in col.links:
                # 04/10/22, remove it from now on as it is not in need
                # pce_ratio = 1 and path_vol * pce_ratio
                links[i].increase_period_flow_vol(
                    tau,
                    path_vol
                )

            if is_path_vol_self_reducing and not cv.is_route_fixed():
                col.vol *= iter_num / (iter_num + 1)



def _update_column_gradient_cost_and_flow(column_pool,
                                          links,
                                          agent_types,
                                          demand_periods,
                                          iter_num):

    _reset_and_update_link_vol_based_on_columns(column_pool,
                                                links,
                                                demand_periods,
                                                iter_num,
                                                False)

    _update_link_travel_time_and_cost(links)

    total_gap = 0
    # total_gap_count = 0

    for k, cv in column_pool.items():
        # k= (at, tau, oz_id, dz_id)
        vot = agent_types[k[0]].get_vot()
        tau = k[1]

        column_num = cv.get_column_num()
        least_gradient_cost = MAX_LABEL_COST
        least_gradient_cost_path_id = -1

        for col in cv.get_columns():
            path_gradient_cost = 0
            # i is link sequence no
            path_gradient_cost = sum(
                links[i].get_generalized_cost(tau, vot) for i in col.links
            )

            col.set_gradient_cost(path_gradient_cost)

            if column_num == 1:
                # total_gap_count += (
                #     path_gradient_cost * col.get_volume()
                # )
                break

            if path_gradient_cost < least_gradient_cost:
                least_gradient_cost = path_gradient_cost
                least_gradient_cost_path_id = col.get_id()

        if column_num >= 2:
            total_switched_out_path_vol = 0

            for col in cv.get_columns():
                if col.get_id() == least_gradient_cost_path_id:
                    continue

                col.set_gradient_cost_abs_diff(
                    col.get_gradient_cost() - least_gradient_cost
                )
                col.set_gradient_cost_rel_diff(
                    col.get_gradient_cost_abs_diff()
                    / max(SMALL_DIVISOR, least_gradient_cost)
                )

                total_gap += (
                    col.get_gradient_cost_abs_diff() * col.get_volume()
                )

                # total_gap_count += (
                #     col.get_gradient_cost() * col.get_volume()
                # )

                step_size = 1 / (iter_num + 2) * cv.get_od_volume()

                previous_path_vol = col.get_volume()
                col.vol = max(
                    0,
                    (previous_path_vol
                     - step_size
                     * col.get_gradient_cost_rel_diff())
                )

                total_switched_out_path_vol += (
                    previous_path_vol - col.get_volume()
                )

        if least_gradient_cost_path_id != -1:
            col = cv.get_column(least_gradient_cost_path_id)
            col.increase_volume(total_switched_out_path_vol)
            # total_gap_count += (
            #     col.get_gradient_cost() * col.get_volume()
            # )

    print(f'total gap: {total_gap:.2f}')
    # print(f'total gap count is: {total_gap_count:.2f}')


def _optimize_column_pool(column_pool,
                          links,
                          agent_types,
                          demand_periods,
                          column_update_num):

    for i in range(column_update_num):
        print(f'current iteration number in column update: {i}')
        _update_column_gradient_cost_and_flow(column_pool,
                                              links,
                                              agent_types,
                                              demand_periods,
                                              i)


def _backtrace_shortest_path_tree(centroid,
                                  centroids,
                                  links,
                                  node_preds,
                                  link_preds,
                                  agent_type,
                                  demand_period,
                                  column_pool,
                                  iter_num):

    if not centroid.has_outgoing_links():
        return

    oz_id = centroid.get_zone_id()
    k_path_prob = 1 / (iter_num + 1)

    for c in centroids:
        dz_id = c.get_zone_id()
        if dz_id == oz_id:
            continue

        if (agent_type, demand_period, oz_id, dz_id) not in column_pool.keys():
            continue

        cv = column_pool[(agent_type, demand_period, oz_id, dz_id)]
        if cv.is_route_fixed():
            continue

        od_vol = cv.get_od_volume()
        vol = od_vol * k_path_prob

        node_path = []
        link_path = []

        dist = 0
        curr_node_seq_no = c.get_node_no()
        # retrieve the sequence backwards
        while curr_node_seq_no >= 0:
            node_path.append(curr_node_seq_no)

            curr_link_seq_no = link_preds[curr_node_seq_no]
            if curr_link_seq_no >= 0:
                link_path.append(curr_link_seq_no)
                dist += links[curr_link_seq_no].length

            curr_node_seq_no = node_preds[curr_node_seq_no]

        # make sure this is a valid path
        if not link_path:
            continue

        existing = False
        for col in cv.get_columns():
            if col.get_distance() != dist:
                continue

            # the first and the last are connectors
            if col.get_links() == link_path[1:-1]:
                col.increase_volume(vol)
                existing = True
                break

        if not existing:
            path_id = cv.get_column_num()
            col = Column(path_id)
            col.set_volume(vol)
            col.set_distance(dist)
            # the first and the last are centroids
            col.nodes = [x for x in node_path[1:-1]]
            col.links = [x for x in link_path[1:-1]]
            cv.add_new_column(col)


def _update_column_attributes(column_pool, links):
    """ update toll and travel time for each column """
    for k, cv in column_pool.items():
        # k = (at, dp, oz, dz)
        dp = k[1]

        for col in cv.get_columns():
            travel_time = sum(
                links[j].travel_time_by_period[dp] for j in col.links
            )
            col.set_travel_time(travel_time)

            path_toll = sum(
                links[j].get_toll() for j in col.links
            )
            col.set_toll(path_toll)


def _generate(spn, column_pool, iter_num):
    for c in spn.get_orig_centroids():
        node_id = c.get_node_id()
        single_source_shortest_path(spn, node_id)

        _backtrace_shortest_path_tree(c,
                                      spn.get_centroids(),
                                      spn.get_links(),
                                      spn.get_node_preds(),
                                      spn.get_link_preds(),
                                      spn.get_agent_type().get_id(),
                                      spn.get_demand_period().get_id(),
                                      column_pool,
                                      iter_num)


def _generate_column_pool(spnetworks, column_pool, iter_num):
    # single processing
    # it could be multiprocessing
    for spn in spnetworks:
        _generate(spn, column_pool, iter_num)


def perform_column_generation(column_gen_num, column_update_num, ui):
    """ perform network assignment using the selected assignment mode

    WARNING
    -------
    Only Path/Column-based User Equilibrium (UE) is implemented in Python.
    If you need other assignment modes or dynamic traffic assignment (DTA),
    please use perform_network_assignment_DTALite()

    Parameters
    ----------
    column_gen_num
        number of iterations to be performed on generating column pool
        column pool

    column_update_num
        number of iterations to be performed on optimizing column pool

    ui
        network object generated by pg.read_network()

    Outputs
    -------
    None

        You will need to call output_columns() and output_link_performance() to
        get the assignment results, i.e., paths/columns (in agent.csv) and
        assigned volumes and other link attributes on each link (in l
        ink_performance.csv)
    """
    # make sure iteration numbers are both non-negative
    assert(column_gen_num>=0)
    assert(column_update_num>=0)

    # base assignment
    A = ui._base_assignment
    # set up SPNetwork
    A.setup_spnetwork()

    links = A.get_links()
    ats = A.get_agent_types()
    dps = A.get_demand_periods()
    column_pool = A.get_column_pool()

    st = time()

    for i in range(column_gen_num):
        print(f'current iteration number in column generation: {i}')
        _update_link_travel_time_and_cost(links, dps, i)

        _reset_and_update_link_vol_based_on_columns(column_pool,
                                                    links,
                                                    dps,
                                                    i,
                                                    True)

        # update generalized link cost before assignment
        _update_generalized_link_cost(A.get_spnetworks())

        # loop through all centroids on the base network
        _generate_column_pool(A.get_spnetworks(), column_pool, i)

    print(f'\nprocessing time of generating columns: {time()-st:.2f} s')

    _optimize_column_pool(column_pool, links, ats, dps, column_update_num)

    _reset_and_update_link_vol_based_on_columns(column_pool,
                                                links,
                                                dps,
                                                column_gen_num,
                                                False)

    _update_link_travel_time_and_cost(links)

    _update_column_attributes(column_pool, links)


def update_links_using_columns(network):
    """ a helper function for load_columns() """
    A = network._base_assignment

    column_pool = A.get_column_pool()
    links = A.get_links()
    dps = A.get_demand_periods()

    # do not update column volume
    _reset_and_update_link_vol_based_on_columns(column_pool,
                                                links,
                                                dps,
                                                1,
                                                False)

    _update_link_travel_time_and_cost(links)


def perform_network_assignment(assignment_mode, column_gen_num, column_update_num, ui):
    """DEPRECATED Column Generation API

    Keep it here as legacy support for existing users who already get used to it
    """
    print('This function has been deprecated, and will be removed later!'
          'Please use perform_column_generation() instead.')

    if assignment_mode != 1:
        raise Exception(
            'NOT implemented yet!'
            'Please please use perform_network_assignment_DTALite().'
        )

    perform_column_generation(column_gen_num, column_update_num, ui)