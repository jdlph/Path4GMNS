import csv

from .classes import ColumnVec
from .colgen import _assignment


__all__ = ['evaluate_accessiblity']


def _get_interval_id(t):
    """ return interval id in predefined time budget intervals

    [0, min_time_budget],
    (min_time_budget + (i-1)*time_intvl, min_time_budget + i*time_intvl]
        where, i is integer and i>=1
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
        vot = sp.get_agent_type().get_vot()
        ffs = sp.get_agent_type().get_free_flow_speed()

        if sp.get_agent_type().get_type().startswith('p'):
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


def _update_min_travel_time(column_pool):
    max_min = 0

    for cv in column_pool.values():
        # try:
        #     min_travel_time = cv.get_columns()[0].get_toll()
        # except IndexError:
        #     # cv does not have any columns/paths
        #     continue
        min_travel_time = -1
        
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


def evaluate_accessiblity(ui, output_dir='.'):
    """ evaluate and output accessiblity matrices """
    print('this operation will reset link volume and travel times!!!')
    
    A = ui._base_assignment
    zones = A.get_zones()
    ats = A.get_agent_types()
    
    # set up column pool for all OD pairs where O != D
    column_pool = {}
    dp = 0
    for oz in zones:
        if oz == -1:
            continue

        for dz in zones:
            if dz == -1:
                continue

            for atype in ats:
                at = atype.get_id()
                column_pool[(at, dp, oz, dz)] = ColumnVec()
                
                if oz == dz:
                    continue
                
                column_pool[(at, dp, oz, dz)].od_vol = 1
    
    # update generalized link cost with free flow speed
    _update_generalized_link_cost_a(A.get_spnetworks())
    # run assignment for one iteration to generate column pool
    _assignment(A.get_spnetworks(), column_pool, 0)
    # update minimum travel time between O and D for each agent type
    max_min = _update_min_travel_time(column_pool)

    # calculate and output accessiblity for each OD pair (i.e., travel time)
    with open(output_dir+'/accessibility.csv', 'w',  newline='') as f:
        interval_num = _get_interval_id(max_min) + 1
        time_bugets = ['TT_'+str(10+5*i) for i in range(interval_num)]

        headers = ['o_zone_id', 'o_zone_name', 
                   'd_zone_id', 'd_zone_name',
                   'accessibility', 'geometry']

        writer = csv.writer(f)
        writer.writerow(headers)

        at = A.get_agent_type_id('p')

        dp = 0
        for oz in zones:
            for dz in zones:
                # for multimodal case, find the minimum travel time 
                # under mode 'p' (i.e., auto)
                min_min = -1
            
                if (at, dp, oz, dz) not in column_pool.keys():
                    min_min = 0
                    continue
                
                cv = column_pool[(at, dp, oz, dz)]
                if cv.get_min_travel_time() == -1:
                    min_min = 0
                    continue

                tt = cv.get_min_travel_time()

                if tt < min_min or min_min == -1:
                    min_min = tt
     
                # output assessiblity
                line = [oz, '', dz, '', min_min, '']
                writer.writerow(line)

    # calculate and output aggregated accessiblity matrix for each agent type
    with open(output_dir+'/accessibility_aggregated.csv', 'w',  newline='') as f:
        interval_num = _get_interval_id(max_min) + 1
        time_bugets = ['TT_'+str(10+5*i) for i in range(interval_num)]

        headers = ['zone_id', 'geometry', 'mode']
        headers.extend(time_bugets)

        writer = csv.writer(f)
        writer.writerow(headers)

        # calculate accessiblity
        dp = 0
        for oz in zones:
            if oz == -1:
                continue

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
                line = [oz, '', atype.get_type()]
                line.extend(counts)
                writer.writerow(line)