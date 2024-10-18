from time import time

from .path import single_source_shortest_path
from .classes import Column
from .consts import EPSILON, MAX_LABEL_COST, MIN_COL_VOL


__all__ = ['find_ue', 'perform_column_generation', 'perform_network_assignment']


def _update_link_cost_array(spnetworks):
    """ update generalized link costs for each SPNetwork """
    for sp in spnetworks:
        tau = sp.get_demand_period().get_id()
        vot = sp.get_agent_type().get_vot()

        for link in sp.get_links():
            if not link.length:
                break

            sp.link_cost_array[link.get_seq_no()] = (
                link.get_generalized_cost(tau, vot)
            )


def _update_link_travel_time(links):
    for link in links:
        if not link.length:
            break

        link.calculate_td_vdf()


def _update_link_and_column_volume(column_pool, links, iter_num, reduce_path_vol = True):
    if not iter_num:
        return

    for link in links:
        if not link.length:
            break

        link.reset_period_flow_vol()

    for k, cv in column_pool.items():
        # k= (at, tau, oz_id, dz_id)
        tau = k[1]

        for col in cv.get_columns():
            path_vol = col.get_volume()
            for i in col.links:
                # 04/10/22, remove it from now on as it is not in need
                # pce_ratio = 1 and path_vol * pce_ratio
                links[i].increase_period_flow_vol(tau, path_vol)

            # 06/11/24: if we check cv.is_route_fixed() here,
            # 1. shall we check it anywhere else??
            # 2. is it really necessary?
            if reduce_path_vol and not cv.is_route_fixed():
                col.vol *= iter_num / (iter_num + 1)


def _update_column_gradient_cost_and_flow(column_pool, links, agent_types, iter_num):
    total_gap = 0
    total_sys_travel_time = 0

    for k, cv in column_pool.items():
        # k = (at, tau, oz_id, dz_id)
        vot = agent_types[k[0]].get_vot()
        tau = k[1]

        least_gradient_cost = MAX_LABEL_COST
        least_gradient_cost_path_id = -1

        for col in cv.get_columns():
            # i is link sequence no
            path_gradient_cost = sum(
                links[i].get_generalized_cost(tau, vot) for i in col.links
            )
            col.set_gradient_cost(path_gradient_cost)

            # col.get_volume() >= EPSILON is the key to eliminate ultra-low-volume
            # columns. along with the blow new_vol reset if new_vol < MIN_COL_VOL,
            # it enables shifting volume from the shortest path to a non-shortest path.
            if path_gradient_cost < least_gradient_cost and col.get_volume() >= EPSILON:
                least_gradient_cost = path_gradient_cost
                least_gradient_cost_path_id = col.get_id()

        total_switched_out_path_vol = 0
        if cv.get_column_num() >= 2:
            for col in cv.get_columns():
                if col.get_id() == least_gradient_cost_path_id:
                    continue

                if not col.get_volume():
                    continue

                col.update_gradient_cost_diffs(least_gradient_cost)

                # with the forgoing col.get_volume() >= EPSILON,
                # col.get_cap() could be negative
                total_gap += col.get_gap()
                total_sys_travel_time += col.get_sys_travel_time()

                step_size = 1 / (iter_num + 2) * cv.get_od_volume()
                cur_vol = col.get_volume()

                new_vol = cur_vol - step_size * col.get_gradient_cost_rel_diff()
                if new_vol < MIN_COL_VOL:
                    new_vol = 0

                col.set_volume(new_vol)
                total_switched_out_path_vol += cur_vol - new_vol

        if least_gradient_cost_path_id != -1:
            col = cv.get_column(least_gradient_cost_path_id)
            total_sys_travel_time += col.get_sys_travel_time()
            col.increase_volume(total_switched_out_path_vol)

    rel_gap = total_gap / max(total_sys_travel_time, EPSILON)

    print(f'current iteration number in column update: {iter_num}\n'
          f'total gap: {total_gap:.4e}; relative gap: {rel_gap:.4%}')


def _backtrace_shortest_path_tree(centroid,
                                  centroids,
                                  links,
                                  node_preds,
                                  link_preds,
                                  at_id,
                                  dp_id,
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

        if (at_id, dp_id, oz_id, dz_id) not in column_pool:
            continue

        cv = column_pool[(at_id, dp_id, oz_id, dz_id)]
        if cv.is_route_fixed():
            continue

        link_path = []
        dist = 0

        curr_node_no = c.get_node_no()
        # retrieve the sequence backwards
        while curr_node_no >= 0:
            curr_link_no = link_preds[curr_node_no]
            if curr_link_no >= 0:
                link_path.append(curr_link_no)
                dist += links[curr_link_no].length

            curr_node_no = node_preds[curr_node_no]

        # make sure this is a valid path
        if not link_path:
            continue

        vol = k_path_prob * cv.get_od_volume()

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
            col.links = [x for x in link_path[1:-1]]
            cv.add_new_column(col)


def _update_column_attributes(column_pool, links, agent_types):
    """ update toll and travel time for each column, and compute final UE convergency """
    total_gap = 0
    total_sys_travel_time = 0

    for k, cv in column_pool.items():
        # k = (at, dp, oz, dz)
        dp = k[1]
        vot = agent_types[k[0]].get_vot()
        least_gradient_cost = MAX_LABEL_COST

        i = 0
        for col in cv.get_columns():
            if not col.get_volume():
                col.reset()
                continue

            # reset column id
            col.set_id(i)
            i += 1

            nodes = []
            path_toll = 0
            travel_time = 0

            path_gradient_cost = 0
            for j in col.links:
                link = links[j]
                nodes.append(link.to_node_no)
                travel_time += link.travel_time_by_period[dp]
                path_toll += link.get_toll()
                path_gradient_cost += link.get_generalized_cost(dp, vot)

            # last node
            nodes.append(links[col.links[-1]].from_node_no)

            col.set_gradient_cost(path_gradient_cost)
            col.set_travel_time(travel_time)
            col.set_toll(path_toll)
            col.nodes = [x for x in nodes]

            if path_gradient_cost < least_gradient_cost:
                least_gradient_cost = path_gradient_cost

        for col in cv.get_columns():
            if not col.get_volume():
                continue

            col.update_gradient_cost_diffs(least_gradient_cost)
            total_sys_travel_time += col.get_sys_travel_time()
            total_gap += col.get_gap()

    rel_gap = total_gap / max(total_sys_travel_time, EPSILON)
    print('current iteration number in column update: postprocessing\n'
          f'total gap: {total_gap:.4e}; relative gap: {rel_gap:.4%}\n')


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
    DEPRECATED due to its confusing name. Use find_ue() instead!

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

    Returns
    -------
    None

    Note
    ----
    You will need to call output_columns() and output_link_performance() to
    get the assignment results, i.e., paths/columns (in route_assignment.csv) and
    assigned volumes and other link attributes on each link (in link_performance.csv)
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
    column_pool = A.get_column_pool()

    print('find user equilibrium (UE)')
    st = time()

    for i in range(column_gen_num):
        print(f'current iteration number in column generation: {i}')

        _update_link_and_column_volume(column_pool, links, i)
        _update_link_travel_time(links)
        # update generalized link cost before assignment
        _update_link_cost_array(A.get_spnetworks())
        # loop through all centroids on the base network
        _generate_column_pool(A.get_spnetworks(), column_pool, i)

    print(f'\nprocessing time of generating columns: {time()-st:.2f} s\n')

    for i in range(column_update_num):
        _update_link_and_column_volume(column_pool, links, i, False)
        _update_link_travel_time(links)
        _update_column_gradient_cost_and_flow(column_pool, links, ats, i)

    # postprocessing
    _update_link_and_column_volume(column_pool, links, column_gen_num, False)
    _update_link_travel_time(links)
    _update_column_attributes(column_pool, links, ats)


def update_links_using_columns(network):
    """ a helper function for load_columns() """
    A = network._base_assignment

    column_pool = A.get_column_pool()
    links = A.get_links()

    # do not update column volume
    _update_link_and_column_volume(column_pool, links, 1, False)
    _update_link_travel_time(links)


def perform_network_assignment(assignment_mode, column_gen_num, column_update_num, ui):
    """DEPRECATED Column Generation API. Use find_ue() instead!

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


def find_ue(ui, column_gen_num, column_update_num):
    """ find user equilibrium (UE)

    WARNING
    -------
    Only Path/Column-based User Equilibrium (UE) is implemented in Python.
    If you need other assignment modes or dynamic traffic assignment (DTA),
    please use perform_network_assignment_DTALite()

    Parameters
    ----------
    ui
        network object generated by pg.read_network()

    column_gen_num
        number of iterations to be performed on generating column pool
        column pool

    column_update_num
        number of iterations to be performed on optimizing column pool

    Returns
    -------
    None

    Note
    ----
    You will need to call output_columns() and output_link_performance() to
    get the assignment results, i.e., paths/columns (in route_assignment.csv) and
    volumes and other link attributes on each link (in link_performance.csv)
    """
    perform_column_generation(column_gen_num, column_update_num, ui)