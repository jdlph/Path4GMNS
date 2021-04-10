import csv

from .classes import ColumnVec
from .colgen import _assignment


__all__ = ['evaluate_accessiblity']


def _get_interval_id(t):
    """ return interval id in predefined time budget intervals

    [min_time_budget, min_time_budget+time_intvl],

    (min_time_budget+time_intvl, min_time_budget+i*time_intvl], where i>=1 and
    i is integer
    """
    min_time_budget = 10
    time_intvl = 5

    if t < min_time_budget:
        return 0

    if (t % (min_time_budget+time_intvl)) == 0:
        return (t/(min_time_budget+time_intvl))

    return int(t/(min_time_budget+time_intvl)) + 1


def _update_generalized_link_cost_a(spnetworks):
    """ update generalized link costs to calcualte accessibility   """
    for sp in spnetworks:
        tau = sp.get_demand_period().get_id()
        vot = sp.get_agent_type().get_vot()
        ffs = sp.get_agent_type().get_free_flow_speed()

        if sp.get_agent_type() == 'p':
            for link in sp.get_links():
                sp.link_cost_array[link.get_seq_no()] = (
                link.get_free_flow_travel_time()
                + link.get_route_choice_cost()
                + link.get_toll() / min(0.001, vot) * 60
            )
        else:
            for link in sp.get_links():
                sp.link_cost_array[link.get_seq_no()] = (
                (link.get_length() / max(0.001, ffs) * 60)
                + link.get_route_choice_cost()
                + link.get_toll() / min(0.001, vot) * 60
            )


def _update_min_travel_time(column_pool, 
                            links,
                            zones,
                            agent_types):
    max_min = 0
    dp = 0

    for oz in zones:
        for dz in zones:
            for atype in agent_types:
                at = atype.get_id()

                min_travel_time = -1
                
                if (at, dp, oz, dz) not in column_pool.keys():
                    continue

                cv = column_pool[(at, dp, oz, dz)]

                for col in cv.get_columns().values():
                    travel_time = col.get_toll()
                    # col.set_travel_time(travel_time)

                    # get minmum travel time
                    if travel_time < min_travel_time or min_travel_time == -1:
                        min_travel_time = travel_time
                    
                cv.update_min_travel_time(min_travel_time)

                if min_travel_time > max_min:
                    max_min = min_travel_time

    return max_min


def evaluate_accessiblity(ui, use_free_flow_travel_time=True):
    """ what if there is no demand between O and D?? """
    print('this operation will reset link volume and travel times!!!')
    
    A = ui._base_assignment

    links = A.get_links()
    zones = A.get_zones()
    ats = A.get_agent_types()
    dps = A.get_demand_periods()
    
    # set up column pool for all OD pairs where O != D
    column_pool = {}
    dp = 0
    for oz in zones:
        for dz in zones:
            for atype in ats:
                at = atype.get_id()
                column_pool[(at, dp, oz, dz)] = ColumnVec()
                column_pool[(at, dp, oz, dz)].od_vol = 1
    
    if use_free_flow_travel_time:
        # update generalized link cost with free flow speed
        _update_generalized_link_cost_a(A.get_spnetworks())
        # run assignment for one iteration to generate column pool
        _assignment(A.get_spnetworks(), column_pool, 0)

    # update minimum travel time between O and D for each agent type
    max_min = _update_min_travel_time(column_pool, links, zones, ats)

    # calculate minimum travel time between O and D for each agent type
    min_travel_times = {}

    with open('./accessibility.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        interval_num = _get_interval_id(max_min) + 1
        time_bugets = ['TT_'+str(10+5*i) for i in range(interval_num)]

        headers = ['zone_id', 'geometry', 'mode']
        headers.extend(time_bugets)

        writer.writerow(headers)

        # calculate accessiblity
        dp = 0
        for oz in zones:
            for atype in ats:
                at = atype.get_id()
                # number of accessible zones from oz for each agent type
                counts = [0] * interval_num
                for dz in zones:
                    if (at, dp, oz, dz) not in column_pool.keys():
                        continue
                    
                    cv = column_pool[(at, dp, oz, dz)]
                    if cv.get_min_travel_time() == -1:
                        continue

                    id = _get_interval_id(cv.get_min_travel_time())
                    while id < interval_num:
                        counts[id] += 1
                        id += 1       
                # output assessiblity
                line = [oz, '', at]
                line.extend(counts)
                writer.writerow(line)