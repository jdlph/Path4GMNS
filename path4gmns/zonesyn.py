from math import ceil, floor

from .accessibility import _update_min_travel_time
from .classes import AccessNetwork, Zone
from .utils import _convert_str_to_float, InvalidRecord


__all__ = ['network_to_zones']


def _get_grid_id(x, y, res):
    try:
        i = floor(x / res)
        j = floor(y / res)
        return i, j
    except ZeroDivisionError:
        raise Exception('ZERO Resolution. Please check your coordinate info!!')


def _get_boundaries(nodes):
    try:
        L = R = _convert_str_to_float(nodes[0].coord_x)
        U = D = _convert_str_to_float(nodes[0].coord_y)
    except InvalidRecord:
        for i, node in enumerate(nodes):
            try:
                x = _convert_str_to_float(node.coord_x)
            except InvalidRecord:
                continue

            try:
                y = _convert_str_to_float(node.coord_y)
            except InvalidRecord:
                continue

            L = R = x
            U = D = y
            break

        if i == len(nodes) - 1 and (L is None or U is None):
            raise Exception('No Coordinate Info')

    for node in nodes:
        try:
            x = _convert_str_to_float(node.coord_x)
        except InvalidRecord:
            continue

        try:
            y = _convert_str_to_float(node.coord_y)
        except InvalidRecord:
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


def _synthesize_bin_index(max_bin, zones):
    min_ = max_ = next(iter(zones.values())).get_activity_nodes_num()
    for z in zones.values():
        n = z.get_activity_nodes_num()
        min_ = min(min_, n)
        max_ = max(max_, n)

    # just in case max_ and min_ are the same
    # max_ would not be ZERO as guaranteed by _synthesize_grid()
    bin_size = max_
    if min_ != max_:
        bin_size = ceil((max_ - min_) / max_bin)

    for z in zones.values():
        # make sure it starts from 0
        bi = (z.get_activity_nodes_num() - 1) // bin_size
        z.set_bin_index(bi)


def _synthesize_grid(ui, grid_dim, max_bin):
    A = ui._base_assignment
    nodes = A.get_nodes()

    if not nodes:
        raise Exception('No Nodes found in the network')

    network = A.network
    zones = network.zones
    zones.clear()

    sample_rate = 0
    if network.activity_node_num == 0:
        sample_rate = 10
        # in case of reginal model
        if len(nodes) > 1000:
            sample_rate = int(len(nodes) / 100)

    # zone id starts from 1
    k = 1
    num = 0
    grids = {}
    res = _find_resolution(nodes, grid_dim)

    for m, node in enumerate(nodes):
        try:
            x = _convert_str_to_float(node.coord_x)
        except InvalidRecord:
            continue

        try:
            y = _convert_str_to_float(node.coord_y)
        except InvalidRecord:
            continue

        if not node.is_activity_node:
            if not sample_rate:
                continue
            elif m % sample_rate != 0:
                continue

        (i, j) = _get_grid_id(x, y, res)
        if (i, j) not in grids.keys():
            grids[(i, j)] = str(k)
            z = Zone(k)
            # boundaries (roughly)
            L_ = i * res
            D_ = j * res
            R_ = L_ + res
            U_ = D_ + res
            # coordinates of the centroid, which are weighted by the first node
            cx = (2 * x + L_ + R_) / 4
            cy = (2 * y + U_ + D_) / 4
            z.setup_geo(U_, D_, L_, R_, cx, cy)
            zones[str(k)] = z
            k += 1

        zones[grids[(i, j)]].add_activity_node(node.get_node_id())
        # this is needed for _update_min_travel_time()
        zones[grids[(i, j)]].add_node(node.get_node_id())
        num += 1

    network.activity_node_num = num
    _synthesize_bin_index(max_bin, zones)


def _synthesize_demand(ui, total_demand, time_budget, mode):
    A = ui._base_assignment
    network = A.network
    ODMatrix = network.ODMatrix
    zones = network.zones
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
    for z in zones.values():
        z.setup_production(int(z.get_activity_nodes_num() * trip_rate))

    # allocate trips proportionally to each OD pair
    for z, v in zones.items():
        if v.get_production() == 0:
            continue

        total_attr = 0
        for z_, v_ in zones.items():
            if z_ == z:
                continue

            if v_.get_production() == 0:
                continue

            if min_travel_times[(z, z_, at_str)][0] > time_budget:
                continue

            total_attr += v_.get_production()

        if total_attr == 0:
            continue

        prod = v.get_production()

        for z_, v_ in zones.items():
            if z_ == z:
                continue

            if v_.get_production() == 0:
                continue

            prod_ = v_.get_production()
            portion = prod_ / total_attr
            ODMatrix[(z, z_)] = round(prod * portion, 2)


def network_to_zones(ui, grid_dimension=8, max_bin=5, total_demand=10000, time_budget=120, mode='auto'):
    """ synthesize zones and OD demand given a network

    Parameters
    ----------
    ui
        network object generated by pg.read_network().

    grid_dimension
        positive integer. If its value is d, a total of d * d zones will be synthesized.

    max_bin
        positive integer. The maximum number of bin_idex generated for synthesized zones.

    total_demand
        The total demand or the total number of trips to be allocated to the OD
        demand matrix. it should be a positive integer.

        The allocated demand to each zone is proportional to the number of its
        activity nodes. Given an origin zone, its production volume will be proportionally
        allocated to each connected destination zone. Gravity Model is NOT in use.

        note that the summation of demand over each OD pair is roughly the same
        as total_demand due to rounding errors.

    time_budget
        the amount of time to travel in minutes, which is used to cut off the demand
        allocation. If the minimum travel time between an OD pair under a specific mode
        is greater than time_budget, we consider that the two zones are not connected
        and no demand will be allocated between them.

    mode
        target mode with its default value as 'auto'. It can be either agent type
        or its name. For example, 'w' and 'walk' are equivalent inputs.

        It is used along with time_budget to check if the minimum travel time under
        the given mode exceeds the time budget or not.

    Returns
    -------
    None

    Note
    ----
    The following files will be output.

    zone.csv.csv
        synthesized zones including zone id, activity nodes, coordinates of its
        centroid, it boundaries (as a grid or rectangle), production volume, and
        attraction volume.

        zone_id will be an integer starting from one.

    syn_demand.csv
        synthesized demand between each connected OD pair (within a time budget).
    """
    if grid_dimension <= 0 or grid_dimension != int(grid_dimension):
        raise Exception('Invalid grid_dimension: it must be a Positive Integer!')

    if total_demand <= 0:
        raise Exception('Invalid total_demand: it must be a Positive Number')

    if time_budget <= 0:
        raise Exception('Invalid time_budget: it must be a Positive Number')

    _synthesize_grid(ui, grid_dimension, max_bin)
    _synthesize_demand(ui, total_demand, time_budget, mode)