from .utils import _convert_str_to_float


__all__ = ['synthesize_zones']


_resolutions = [0.00005, 0.0001, 0.0002, 
                0.00025, 0.0005, 0.00075, 
                0.001, 0.002, 0.0025,
                0.005, 0.0075, 0.01,
                0.02, 0.025, 0.05,
                0.075, 0.1, 0.2,
                0.25, 0.5, 0.75,
                1, 2, 2.5,
                5, 7.5, 10,
                20, 25, 50, 75]


def _get_grid_id(x, y, res):
    assert(res > 0)
    i = int(x / res)
    j = int(y / res)

    return i, j


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

        if i == len(nodes) - 1 and L is None or U is None:
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

    return (L, R, D, U)


def _setup_grid(ui):
    A = ui._base_assignment
    nodes = A.get_nodes()

    (L, R, D, U) = _get_boundaries(nodes)
    grid_dim = 8
    if len(nodes) > 3000:
        grid_dim = 10

    res = ((R - L + U - D) / grid_dim) / 2
    for r in _resolutions:
        if res < r:
            res = r
            break
    
    no_activity_node = False
    if not A.activity_nodes():
        no_activity_node = True
        sample_rate = 10
        if len(nodes) > 1000:
            sample_rate = len(nodes) / 100

    k = 0
    grids = {}
    zone_to_nodes = {}
    for m, node in enumerate(nodes):
        x = _convert_str_to_float(node.coord_x)
        if x is None:
            continue
        
        y = _convert_str_to_float(node.coord_y)
        if y is None:
            continue

        if not no_activity_node and not node.is_activity_node:
            continue

        if no_activity_node and m % sample_rate != 0:
            continue

        (i, j) = _get_grid_id(x, y, res)
        if (i, j) not in grids.keys():
            grids[(i, j)] = k
            zone_to_nodes[k] = []
            k += 1
        zone_to_nodes[grids[(i, j)]].append(node.get_node_no())
    
    print(k)
    print(grids.keys())

    A.zone_to_nodes_dict = zone_to_nodes


def synthesize_zones(ui):
    _setup_grid(ui)