import os
import csv
import threading

from .classes import AccessNetwork
from .path import single_source_shortest_path
from .consts import MAX_LABEL_COST, MIN_TIME_BUDGET, \
                    BUDGET_TIME_INTVL, MAX_TIME_BUDGET


__all__ = ['evaluate_accessibility']


def _get_interval_id(t):
    """ return interval id in predefined time budget intervals

    [0, MIN_TIME_BUDGET],

    (MIN_TIME_BUDGET + (i-1)*BUDGET_TIME_INTVL, MIN_TIME_BUDGET + i*BUDGET_TIME_INTVL]
        where, i is integer and i>=1
    """
    if t < MIN_TIME_BUDGET:
        return 0

    if (t % (MIN_TIME_BUDGET+BUDGET_TIME_INTVL)) == 0:
        return int(t/(MIN_TIME_BUDGET+BUDGET_TIME_INTVL))

    return int(t/(MIN_TIME_BUDGET+BUDGET_TIME_INTVL)) + 1


def _update_min_travel_time(an, at, min_travel_times, time_dependent, demand_period_id):
    an.update_generalized_link_cost(at, time_dependent, demand_period_id)

    at_str = at.get_type_str()
    max_min = 0
    for c in an.get_centroids():
        node_id = c.get_node_id()
        zone_id = c.get_zone_id()
        single_source_shortest_path(an, node_id)
        for c_ in an.get_centroids():
            if c_ == c:
                continue

            node_no = c_.get_node_no()
            to_zone_id = c_.get_zone_id()
            min_tt = an.get_node_label_cost(node_no)
            # this function will dramatically slow down the whole process
            min_dist = an.get_sp_distance(node_no)
            min_travel_times[(zone_id, to_zone_id, at_str)] = min_tt, min_dist

            if min_tt < MAX_LABEL_COST and max_min < min_tt:
                max_min = min_tt

    return max_min


def _output_accessibility(min_travel_times, zones, mode='p', output_dir='.'):
    """ output accessibility for each OD pair (i.e., travel time) """
    with open(output_dir+'/accessibility.csv', 'w',  newline='') as f:
        headers = ['o_zone_id', 'o_zone_name',
                   'd_zone_id', 'd_zone_name',
                   'accessibility', 'distance',
                   'geometry']

        writer = csv.writer(f)
        writer.writerow(headers)

        # for multimodal case, find the minimum travel time
        # under mode 'p' (i.e., auto)
        for k, v in min_travel_times.items():
            # k = (from_zone_id, to_zone_id, at_type_str)
            if k[2] != mode:
                continue

            # output assessiblity
            # no exception handlings here as min_travel_times is constructed 
            # directly using an.get_centroids()
            coord_oz = zones[k[0]]
            coord_dz = zones[k[1]]
            geo = 'LINESTRING (' + coord_oz + ', ' + coord_dz + ')'

            line = [k[0], '', k[1], '', v[0], v[1], geo]
            writer.writerow(line)

        if output_dir == '.':
            print('\ncheck accessibility.csv in '
                  +os.getcwd()+' for accessibility matrix')
        else:
            print('\ncheck accessibility.csv in '
                  +os.path.join(os.getcwd(), output_dir)
                  +' for accessibility matrix')


def _output_accessibility_aggregated(min_travel_times, interval_num,
                                     zones, ats, output_dir='.'):
    """ output aggregated accessibility matrix for each agent type """

    with open(output_dir+'/accessibility_aggregated.csv', 'w',  newline='') as f:
        time_bugets = [
            'TT_'+str(MIN_TIME_BUDGET+BUDGET_TIME_INTVL*i) for i in range(interval_num)
        ]

        headers = ['zone_id', 'geometry', 'mode']
        headers.extend(time_bugets)

        writer = csv.writer(f)
        writer.writerow(headers)

        # calculate accessibility
        for oz, coord in zones.items():
            if oz == -1:
                continue

            for atype in ats:
                at_str = atype.get_type_str()
                # number of accessible zones from oz for each agent type
                counts = [0] * interval_num
                for dz in zones.keys():
                    if (oz, dz, at_str) not in min_travel_times.keys():
                        continue

                    min_tt = min_travel_times[(oz, dz, at_str)][0]
                    if min_tt >= MAX_LABEL_COST:
                        continue

                    id = _get_interval_id(min_tt)
                    while id < interval_num:
                        counts[id] += 1
                        id += 1
                # output assessiblity
                geo = 'LINESTRING (' + coord + ')'
                line = [oz, geo, atype.get_type_str()]
                line.extend(counts)
                writer.writerow(line)

        if output_dir == '.':
            print('\ncheck accessibility_aggregated.csv in '
                  +os.getcwd()+' for aggregated accessibility matrix')
        else:
            print('\ncheck accessibility_aggregated.csv in '
                  +os.path.join(os.getcwd(), output_dir)
                  +' for aggregated accessibility matrix')


def evaluate_accessibility(ui, multimodal=True, mode='p', time_dependent=False, demand_period_id=0, output_dir='.'):
    base = ui._base_assignment
    an = AccessNetwork(base.network)
    ats = None

    # map zone id to zone centroid coordinate 
    zones = {}
    for c in an.get_centroids():
        zones[c.get_zone_id()] = c.get_coordinate()

    max_min = 0
    min_travel_times = {}
    if multimodal:
        ats = base.get_agent_types()
        for at in ats:
            an.set_target_mode(at.get_name())
            max_min_ = _update_min_travel_time(an, at, min_travel_times, time_dependent, demand_period_id)
            if max_min_ > max_min:
                max_min = max_min_
    else:
        at_name, at_str = base._convert_mode(mode)
        an.set_target_mode(at_name)
        at = base.get_agent_type(at_str)
        max_min = _update_min_travel_time(an, at, min_travel_times, time_dependent, demand_period_id)
        ats = [at]

    interval_num = _get_interval_id(min(max_min, MAX_TIME_BUDGET)) + 1

    t = threading.Thread(
        target=_output_accessibility,
        args=(min_travel_times, zones, mode, output_dir))
    t.start()

    t = threading.Thread(
        target=_output_accessibility_aggregated,
        args=(min_travel_times, interval_num, zones, ats, output_dir)
    )
    t.start()