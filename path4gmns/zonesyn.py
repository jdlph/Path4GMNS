from math import floor

from .accessibility import _update_min_travel_time
from .classes import AccessNetwork
from .utils import _convert_str_to_float


__all__ = ['network_to_zones']


def _get_grid_id(x, y, res):
    try:
        i = floor(x / res)
        j = floor(y / res)
        return i, j
    except ZeroDivisionError:
        raise Exception('ZERO Resolution. Please check your coordinate info!!')


def _get_boundaries(nodes):
    L = R = _convert_str_to_float(nodes[0].coord_x)
    U = D = _convert_str_to_float(nodes[0].coord_y)
    if L is None or U is None:
        for i, node in enumerate(nodes):
            x = _convert_str_to_float(node.coord_x)
            if x is None:
                continue

            y = _convert_str_to_float(node.coord_y)
            if y is None:
                continue

            L = R = x
            U = D = y
            break

        if i == len(nodes) - 1 and (L is None or U is None):
            raise Exception('No Coordinate Info')

    for node in nodes:
        x = _convert_str_to_float(node.coord_x)
        if x is None:
            continue

        y = _convert_str_to_float(node.coord_y)
        if y is None:
            continue

        L = min(L, x)
        R = max(R, x)
        D = min(D, y)
        U = max(U, y)

    return (U, D, L, R)


def _find_resolution(nodes, grid_dim):
    # adopt from NeXTA
    resolutions = [0.00005, 0.0001, 0.0002, 0.00025, 0.0005, 0.00075,
                   0.001, 0.002, 0.0025, 0.005, 0.0075, 0.01, 0.02,
                   0.025, 0.05, 0.075, 0.1, 0.2, 0.25, 0.5, 0.75,
                   1, 2, 2.5, 5, 7.5, 10, 20, 25, 50, 75]

    # if grid_dim is d, we will create a total of d * d grids
    (U, D, L, R) = _get_boundaries(nodes)
    res = ((R - L + U - D) / grid_dim) / 2
    for r in resolutions:
        if res < r:
            res = r
            break

    return res


def _synthesize_grid(ui, grid_dim):
    A = ui._base_assignment
    nodes = A.get_nodes()
    network = A.network

    sample_rate = 0
    if not A.activity_nodes():
        sample_rate = 10
        # in case of reginal model
        if len(nodes) > 1000:
            sample_rate = int(len(nodes) / 100)

    k = 0
    num = 0
    grids = {}
    zone_info = {}
    activity_nodes = {}
    activity_nodeids = {}
    res = _find_resolution(nodes, grid_dim)

    for m, node in enumerate(nodes):
        x = _convert_str_to_float(node.coord_x)
        if x is None:
            continue

        y = _convert_str_to_float(node.coord_y)
        if y is None:
            continue

        if not node.is_activity_node:
            if not sample_rate:
                continue
            elif m % sample_rate != 0:
                continue

        (i, j) = _get_grid_id(x, y, res)
        if (i, j) not in grids.keys():
            grids[(i, j)] = k
            activity_nodes[k] = []
            activity_nodeids[k] = []
            # boundaries (roughly)
            L_ = i * res
            D_ = j * res
            R_ = L_ + res
            U_ = D_ + res
            # coordinates of the centroid, which are weighted by the first node
            cx = (2 * x + L_ + R_) / 4
            cy = (2 * y + U_ + D_) / 4
            # the last one is reserved for production/attraction
            zone_info[k] = [U_, D_, L_, R_, cx, cy, 0]
            k += 1

        activity_nodes[grids[(i, j)]].append(node.get_node_no())
        activity_nodeids[grids[(i, j)]].append(node.get_node_id())
        num += 1

    network.activity_nodes = activity_nodes
    network.zone_to_nodes = activity_nodeids
    network.zones = sorted(activity_nodes.keys())
    network.zone_info = zone_info
    network.activity_node_num = num


def _synthesize_demand(ui, total_demand, time_budget, mode):
    A = ui._base_assignment
    network = A.network
    ODMatrix = network.ODMatrix
    zone_info = network.zone_info
    activity_nodes = network.activity_nodes
    num = network.activity_node_num

    # calculate accessibility
    an = AccessNetwork(network)
    at_name, at_str = A._convert_mode(mode)
    an.set_target_mode(at_name)
    at = A.get_agent_type(at_str)

    min_travel_times = {}
    _update_min_travel_time(an, at, min_travel_times, False, 0)

    # allocate trips proportionally to each zone
    trip_rate = total_demand / num
    for k, v in zone_info.items():
        v[6] = int(len(activity_nodes[k]) * trip_rate)

    # allocate trips proportionally to each OD pair
    for z, v in zone_info.items():
        if v[6] == 0:
            continue

        total_attr = 0
        for z_, v_ in zone_info.items():
            if z_ == z:
                continue

            if v_[6] == 0:
                continue

            if min_travel_times[(z, z_, at_str)][0] > time_budget:
                continue

            total_attr += v_[6]

        if total_attr == 0:
            continue

        for z_, v_ in zone_info.items():
            if z_ == z:
                continue

            if v_[6] == 0:
                continue

            portion = v_[6] / total_attr
            ODMatrix[(z, z_)] = round(v[6] * portion, 2)


def network_to_zones(ui, grid_dimension=8, total_demand=5000, time_budget=120, mode='p'):
    if grid_dimension <= 0 or grid_dimension != int(grid_dimension):
        raise Exception('Invalid grid_dimension: it must be a Positive Integer!')

    if total_demand <= 0:
        raise Exception('Invalid total_demand: it must be a Positive Number')

    if time_budget <= 0:
        raise Exception('Invalid time_budget: it must be a Positive Number')
    
    _synthesize_grid(ui, grid_dimension)
    _synthesize_demand(ui, total_demand, time_budget, mode)