from .colgen import _update_link_cost_array
from .path import single_source_shortest_path


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
        dist = 0

        curr_node_no = c.get_node_no()
        cost = node_costs[curr_node_no]

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

        vol = cv.get_od_volume()
        total_min_sys_tt += vol * cost
        
        [links[i].update_directions[dp_id, vol] for i in link_path[1:-1]]


def _update_link_travel_time(links, alpha):
    for link in links:
        if not link.length:
            break

        link.calculate_td_vdf(alpha)


def _get_derivative(links, tau, alpha):
    d = 0
    for link in links:
        if not link.length:
            break

        d += link.get_derivative(tau, alpha)

    return d


def _update_link_flows(links, alpha=1):
    for link in links:
        if not link.length:
            break

        link.update_period_flows(alpha)


def _update_auxiliary_flows(spnetworks, column_pool):
    # find the new shortest paths
    for spn in spnetworks:
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


def find_ue(ui, max_iter_num = 40, rel_gap_tolerance=0.0001):
    # base assignment
    A = ui._base_assignment
    # set up SPNetwork
    A.setup_spnetwork(True)

    ats = A.get_agent_types()
    column_pool = A.get_column_pool()
    links = A.get_links()

    i = 0
    _update_link_travel_time(links, 0)
    _update_link_cost_array(A.get_spnetworks())
    _update_auxiliary_flows(A.get_spnetworks(), column_pool)
    _update_auxiliary_flows(links)

    alpha = 0.5
    lb = 0
    ub = 1
    while i < max_iter_num:
        _update_link_travel_time(links, 0)
        _update_link_cost_array(A.get_spnetworks())
        _update_auxiliary_flows(A.get_spnetworks(), column_pool)
        
        tau = 1
        # line search, which shall be demand period specific
        j = 0
        while j < 20:
            d = _get_derivative(tau, alpha)
            if abs(d) < 0.0001:
                break

            if d < 0:
                lb = alpha
            elif d > 0:
                ub = alpha

            alpha = (lb + ub) / 2

        _update_link_flows(alpha)
        # compute the relative gap
        _update_link_travel_time(links, alpha)

        tstt = 0
        for link in links:
            if not link.length:
                break

        tstt += link.get_derivative(tau, alpha)
        gap = tstt - total_min_sys_tt
        rel_gap = gap /tstt
        