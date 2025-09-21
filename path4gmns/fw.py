from .colgen import _update_link_cost_array
from .consts import EPSILON
from .path import single_source_shortest_path


__all__ = ['find_ue_fw']


_total_sys_travel_time = dict()
_total_min_sys_travel_time = dict()


def _backtrace_shortest_path_tree(centroid,
                                  centroids,
                                  links,
                                  node_preds,
                                  link_preds,
                                  node_costs,
                                  at_id,
                                  dp_id,
                                  column_pool):

    oz_id = centroid.get_zone_id()
    for c in centroids:
        dz_id = c.get_zone_id()
        if dz_id == oz_id:
            continue

        if (at_id, dp_id, oz_id, dz_id) not in column_pool:
            continue

        cv = column_pool[(at_id, dp_id, oz_id, dz_id)]

        link_path = []

        curr_node_no = c.get_node_no()
        cost = node_costs[curr_node_no]

        # retrieve the sequence backwards
        while curr_node_no >= 0:
            curr_link_no = link_preds[curr_node_no]
            if curr_link_no >= 0:
                link_path.append(curr_link_no)

            curr_node_no = node_preds[curr_node_no]

        # make sure this is a valid path
        if not link_path:
            continue

        vol = cv.get_od_volume()
        _total_min_sys_travel_time[dp_id] += vol * cost

        [links[i].update_aux_flows(dp_id, vol) for i in link_path[1:-1]]


def _update_link_travel_time(links):
    for link in links:
        if not link.length:
            break

        link.calculate_td_vdf()


def _get_derivative(links, tau, alpha):
    d = 0
    for link in links:
        if not link.length:
            break

        d += link.get_derivative(tau, alpha)

    return d


def _update_link_flows(spnetworks, iter_no):
    for sp in spnetworks:
        tau = sp.get_demand_period().get_id()
        if not iter_no:
            alpha = 1
        else:
            alpha = _line_search(sp.get_links(), tau)

        for link in sp.get_links():
            if not link.length:
                break

            link.update_period_flows(tau, alpha)
            link.calculate_td_vdf()


def _update_auxiliary_flows(A, links, column_pool):
    # reset auxiliary flows for all links (except connectors)
    for link in links:
        if not link.length:
            break

        link.reset_period_aux_flows()

    _init_sys_tt(A.get_spnetworks())
    # find the new shortest paths
    for spn in A.get_spnetworks():
        for c in spn.get_orig_centroids():
            single_source_shortest_path(spn, c.get_node_id())
            _backtrace_shortest_path_tree(c,
                                          spn.get_centroids(),
                                          spn.get_links(),
                                          spn.get_node_preds(),
                                          spn.get_link_preds(),
                                          spn.get_node_label_costs(),
                                          spn.get_agent_type().get_id(),
                                          spn.get_demand_period().get_id(),
                                          column_pool)


def _line_search(links, tau, tolerance=1e-06):
    # line search, which shall be demand period specific
    lb = 0
    ub = 1

    j = 0
    while j < 20:
        alpha = (lb + ub) / 2

        derivative = _get_derivative(links, tau, alpha)
        if abs(derivative) < 0.0001:
            break

        if derivative < 0:
            lb = alpha
        else:
            ub = alpha

        if abs(ub - lb) < tolerance:
            break

        j = j + 1

    print(f'derivative is {derivative}')
    print(f'step size is {alpha}')

    return alpha


def _compute_relative_gap(A, iter_no):
    """ compute the relative gap """
    for sp in A.get_spnetworks():
        tau = sp.get_demand_period().get_id()
        vot = sp.get_agent_type().get_vot()

        for link in sp.get_links():
            if not link.length:
                break

            # this can be optimized by replacing link.get_generalized_cost(tau, vot)
            # with sp.link_cost_array[link.get_seq_no()]
            _total_sys_travel_time[tau] += (
                link.get_generalized_cost(tau, vot) * link.get_period_flow_vol(tau)
            )

        total_gap = _total_sys_travel_time[tau] - _total_min_sys_travel_time[tau]
        rel_gap = total_gap / max(_total_sys_travel_time[tau], EPSILON)
        print(f'current iteration number in Frank-Wolfe: {iter_no}\n'
              f'total gap: {total_gap:.4e}; relative gap: {rel_gap:.4%}\n')


def _init_sys_tt(spnetworks):
    for sp in spnetworks:
        tau = sp.get_demand_period().get_id()

        _total_sys_travel_time[tau] = 0
        _total_min_sys_travel_time[tau] = 0


def find_ue_fw(ui, max_iter_num = 40, rel_gap_tolerance=0.0001):
    # base assignment
    A = ui._base_assignment
    # set up SPNetwork
    A.setup_spnetwork(True)

    column_pool = A.get_column_pool()
    links = A.get_links()

    i = 0
    _update_link_travel_time(links)
    _update_link_cost_array(A.get_spnetworks())

    while i < max_iter_num:
        _update_auxiliary_flows(A, links, column_pool)
        # a little bit ugly to place it here
        _compute_relative_gap(A, i)

        _update_link_flows(A.get_spnetworks(), iter_no=i)
        _update_link_travel_time(links)
        _update_link_cost_array(A.get_spnetworks())

        i = i + 1
