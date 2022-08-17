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


def _setup_grid(ui):
    A = ui._base_assignment
    nodes = A.get_nodes()

    left = right = float(nodes[0].coord_x)
    top = bot = float(nodes[0].coord_y)

    for node in nodes:
        x = node.coord_x
        if not x:
            continue
        
        y = node.coord_y
        if not y:
            continue

        x = float(x)
        y = float(y)

        left = min(left, x)
        right = max(right, x)
        bot = min(bot, y)
        top = max(top, y)

    grid_num = 8
    if len(nodes) > 3000:
        grid_num = 10

    res = ((right - left + top - bot) / grid_num) / 2
    for r in _resolutions:
        if res < r:
            res = r
            break

    k = 0
    grids = {}
    zone_to_nodes = {}
    for node in nodes:
        x = node.coord_x
        if not x:
            continue
        
        y = node.coord_y
        if not y:
            continue

        x = float(x)
        y = float(y)

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