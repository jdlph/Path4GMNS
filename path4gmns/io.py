import csv
import os
import warnings

from .classes import Node, Link, Zone, Network, Column, ColumnVec, VDFPeriod, \
                     AgentType, DemandPeriod, Demand, SpecialEvent, Assignment, UI

from .colgen import update_links_using_columns
from .consts import EPSILON, MILE_TO_METER, MPH_TO_KPH
from .utils import InvalidRecord, _are_od_connected, _convert_boundaries, \
                   _convert_str_to_float, _convert_str_to_int, _get_time_stamp, \
                   _update_dest_zone, _update_orig_zone
from .zonesyn import network_to_zones


__all__ = [
    'read_network',
    'read_demand',
    'read_measurements',
    'load_demand',
    'load_columns',
    'output_columns',
    'output_link_performance',
    'output_agent_paths',
    'output_agent_trajectory',
    'output_synthetic_zones',
    'output_synthetic_demand'
]


def read_nodes(input_dir,
               nodes,
               map_id_to_no,
               map_no_to_id,
               zones,
               load_demand):

    """ step 1: read input_node """
    with open(input_dir+'/node.csv', 'r') as fp:
        print('read node.csv')

        reader = csv.DictReader(fp)
        node_no = 0
        for line in reader:
            # set up node_id
            node_id = line['node_id']
            # node_id should be unique
            if node_id in map_id_to_no:
                print(f'Duplicate node id found {node_id}. Record discarded!')
                continue

            # set up zone_id
            try:
                zone_id = line['zone_id']
            except KeyError:
                zone_id = ''

            # treat them as string
            coord_x = line['x_coord']
            coord_y = line['y_coord']

            # activity node
            is_activity_node = False
            try:
                b = _convert_str_to_int(line['boundary'])
                if b:
                    is_activity_node = True
            except (KeyError, InvalidRecord):
                pass

            # construct node object
            node = Node(node_no, node_id, zone_id, coord_x, coord_y, is_activity_node)
            nodes.append(node)

            # set up mapping between node_no and node_id
            map_id_to_no[node_id] = node_no
            map_no_to_id[node_no] = node_id

            # bin_index for equity evaluation
            try:
                bin_index = _convert_str_to_int(line['bin_index'])
            except (KeyError, InvalidRecord):
                bin_index = 0

            # associate node_id with corresponding zone
            if zone_id not in zones:
                # only take the value of bin_index from the first node
                # associated with each zone
                z = Zone(zone_id, bin_index)
                zones[zone_id] = z

            zones[zone_id].add_node(node_id)
            if is_activity_node:
                zones[zone_id].add_activity_node(node_id)

            node_no += 1

        print(f'the number of nodes is {node_no:,d}')

        if load_demand:
            zone_size = len(zones)
            if '' in zones:
                zone_size -= 1

            if zone_size == 0:
                raise Exception('there are NO VALID zones from node.csv')

            print(f'the number of zones is {zone_size:,d}\n')


def read_links(input_dir,
               links,
               nodes,
               map_id_to_no,
               link_ids,
               demand_period_size,
               length_unit,
               speed_unit,
               load_demand):
    """ step 2: read input_link """
    with open(input_dir+'/link.csv', 'r') as fp:
        print('read link.csv')

        reader = csv.DictReader(fp)
        link_no = 0
        # a temporary container (set) to validate the uniqueness of a link id
        link_ids_ = set()
        for line in reader:
            # link id shall be unique
            link_id = line['link_id']
            # binary search shall be fast enough
            if link_id in link_ids_:
                print(f'Duplicate link id found {link_id}. Record discarded!')
                continue

            # validity check
            from_node_id = line['from_node_id']
            to_node_id = line['to_node_id']

            try:
                from_node_no = map_id_to_no[from_node_id]
            except KeyError:
                print(
                    f'Exception: Node ID {from_node_id}'
                    ' NOT in the network!!'
                )
                continue

            try:
                to_node_no = map_id_to_no[to_node_id]
            except KeyError:
                print(
                    f'Exception: Node ID {to_node_id}'
                    ' NOT in the network!!'
                )
                continue

            try:
                length = _convert_str_to_float(line['length'])
            except InvalidRecord:
                continue

            # pass validity check

            # for the following attributes,
            # if they are not None, convert them to the corresponding types
            # if they are None's, set them using the default values
            try:
                lanes = _convert_str_to_int(line['lanes'])
            except InvalidRecord:
                lanes = 1

            try:
                link_type = _convert_str_to_int(line['link_type'])
            except (KeyError, InvalidRecord):
                link_type = 1

            try:
                free_speed = _convert_str_to_float(line['free_speed'])
            except InvalidRecord:
                free_speed = 60

            # issue: int??
            try:
                capacity = _convert_str_to_int(line['capacity'])
            except (KeyError, InvalidRecord):
                capacity = 1999

            try:
                toll = _convert_str_to_float(line['toll'])
            except (KeyError, InvalidRecord):
                toll = 0

            # if link.csv does not have no column 'allowed_uses',
            # set allowed_uses to 'all'
            # developer's note:
            # we may need to change this implementation as we cannot deal with
            # cases a link which is not open to any modes
            try:
                allowed_uses = line['allowed_uses']
                if not allowed_uses:
                    raise InvalidRecord
            except (KeyError, InvalidRecord):
                allowed_uses = 'all'

            # if link.csv does not have no column 'geometry',
            # set geometry to ''
            try:
                geometry = line['geometry']
            except KeyError:
                geometry = ''

            link_ids[link_id] = link_no

            # unit conversion
            if length_unit.startswith('meter') or length_unit == 'm':
                length = length / MILE_TO_METER
            elif length_unit.startswith('kilometer') or length_unit.startswith('km'):
                length = length / MPH_TO_KPH

            if speed_unit.startswith('kmh') or speed_unit.startswith('kph'):
                free_speed = free_speed / MPH_TO_KPH

            # construct link object
            link = Link(link_id,
                        link_no,
                        from_node_no,
                        to_node_no,
                        from_node_id,
                        to_node_id,
                        length,
                        lanes,
                        link_type,
                        free_speed,
                        capacity,
                        toll,
                        allowed_uses,
                        geometry,
                        demand_period_size)

            # VDF Attributes
            for i in range(demand_period_size):
                dp_id_str = str(i+1)
                header_vdf_alpha = 'VDF_alpha' + dp_id_str
                header_vdf_beta = 'VDF_beta' + dp_id_str
                header_vdf_mu = 'VDF_mu' + dp_id_str
                header_vdf_fftt = 'VDF_fftt' + dp_id_str
                header_vdf_cap = 'VDF_cap' + dp_id_str
                header_vdf_phf = 'VDF_phf' + dp_id_str

                # case i: link.csv does not VDF attributes at all
                # case ii: link.csv only has partial VDF attributes
                # under case i, we will set up only one VDFPeriod object using
                # default values
                # under case ii, we will set up some VDFPeriod objects up to
                # the number of complete set of VDF_alpha, VDF_beta, and VDF_mu
                try:
                    VDF_alpha = _convert_str_to_float(line[header_vdf_alpha])
                except (KeyError, InvalidRecord):
                    if i == 0:
                        # default value will be applied in the constructor
                        VDF_alpha = 0.15
                    else:
                        break

                try:
                    VDF_beta = _convert_str_to_float(line[header_vdf_beta])
                except (KeyError, InvalidRecord):
                    if i == 0:
                        # default value will be applied in the constructor
                        VDF_beta = 4
                    else:
                        break

                try:
                    VDF_mu = _convert_str_to_float(line[header_vdf_mu])
                except (KeyError, InvalidRecord):
                    if i == 0:
                        # default value will be applied in the constructor
                        VDF_mu = 1000
                    else:
                        break

                try:
                    VDF_fftt = _convert_str_to_float(line[header_vdf_fftt])
                except (KeyError, InvalidRecord):
                    # set it up using length and free_speed from link
                    VDF_fftt = length / max(EPSILON, free_speed) * 60

                try:
                    VDF_cap = _convert_str_to_float(line[header_vdf_cap])
                except (KeyError, InvalidRecord):
                    # set it up using capacity from link
                    VDF_cap = capacity * lanes

                # not a mandatory column
                try:
                    VDF_phf = _convert_str_to_float(line[header_vdf_phf])
                except (KeyError, InvalidRecord):
                    # default value will be applied in the constructor
                    VDF_phf = -1

                # construct VDFPeriod object
                vdf = VDFPeriod(i, VDF_alpha, VDF_beta, VDF_mu,
                                VDF_fftt, VDF_cap, VDF_phf)

                link.vdfperiods.append(vdf)

            # set up outgoing links and incoming links
            from_node = nodes[from_node_no]
            to_node = nodes[to_node_no]
            from_node.add_outgoing_link(link)
            to_node.add_incoming_link(link)
            links.append(link)

            # set up zone degrees
            if load_demand:
                oz_id = from_node.get_zone_id()
                dz_id = to_node.get_zone_id()
                _update_orig_zone(oz_id)
                _update_dest_zone(dz_id)

            link_no += 1
            link_ids_.add(link_id)

        print(f'the number of links is {link_no:,d}\n')


def _read_demand(input_dir,
                 file,
                 agent_type_id,
                 demand_period_id,
                 zones,
                 column_pool,
                 check_connectivity=False):
    """ step 3:read input_agent """
    with open(input_dir+'/'+file, 'r') as fp:
        print('read '+file)

        at = agent_type_id
        dp = demand_period_id

        reader = csv.DictReader(fp)
        valid_vol = 0
        invalid_vol = 0
        invalid_od_num = 0
        for line in reader:
            oz_id = line['o_zone_id']
            # o_zone_id does not exist in node.csv, discard it
            if oz_id not in zones:
                continue

            dz_id = line['d_zone_id']
            # d_zone_id does not exist in node.csv, discard it
            if dz_id not in zones:
                continue

            try:
                vol = _convert_str_to_float(line['volume'])
            except InvalidRecord:
                continue

            # discard invalid OD pair, case I: invalid volume
            if vol <= 0:
                invalid_od_num += 1
                continue

            # discard invalid OD pair, case II: O and D are the same
            if oz_id == dz_id:
                invalid_od_num += 1
                invalid_vol += vol
                continue

            # precheck on connectivity of each OD pair
            if check_connectivity and not (_are_od_connected(oz_id, dz_id)):
                continue

            # set up volume for ColumnVec
            if (at, dp, oz_id, dz_id) not in column_pool:
                column_pool[(at, dp, oz_id, dz_id)] = ColumnVec()
            column_pool[(at, dp, oz_id, dz_id)].increase_volume(vol)

            valid_vol += vol

        print(
            f'the total valid demand is {valid_vol:,.3f}\n'
            f'{invalid_od_num:,d} invalid OD pairs are found. '
            f'Total discarded volume: {invalid_vol:,.2f}\n'
        )

        if valid_vol == 0:
            # there are four cases.
            # Case I:   zones is empty
            #           This shall be caught by read_node().
            # Case II:  zones is not empty and invalid_od_num == 0
            #           Every zone_id present in demand.csv is not found in
            #           node.csv. This implies data inconsistency between these
            #           two files on zone_id). Another possibility is that volume
            #           is not numerical.
            # Case III: zones is not empty, invalid_od_num > 0, and invalid_vol == 0
            #           All OD pairs in demand.csv have invalid volume (i.e.,
            #           volume is zero or less).
            # Case IV:  zones is not empty, invalid_od_num > 0, and invalid_vol > 0
            #           This implies either O and D are the same for every OD
            #           pair or no OD pair is not connected.
            if invalid_od_num == 0:
                message = 'volume is not encoded as numerical or Every zone id ' \
                          'present in demand.csv is not found in node.csv.\n\n' \
                          'For the latter one, different zone id representations ' \
                          'could be the reason. For example, zone id is encoded ' \
                          'as integer in demand.csv but decimal in node.csv. ' \
                          'Note that zone_id CANNOT be decimal per GMNS specification!\n'\
                          'Hint: Use an advanced text editor (not Excel) to verify. '
            elif invalid_od_num > 0 and invalid_vol == 0:
                message = 'At lease one OD pair shall have positive volume!\n'
            else:
                message = 'No connected OD pairs are found (i.e., no valid paths ' \
                          'between O and D for each OD pair) or Every OD pair ' \
                          'have the same O and D!\n'

            raise Exception(message)


def load_demand(ui,
                agent_type_str='a',
                demand_period_str='AM',
                input_dir='.',
                filename='demand.csv'):
    """
    load demand for an agent type and a demand period

    this is an user interface while _read_demand() is intended for internal use.
    """
    A = ui._base_assignment

    at = A.get_agent_type_id(agent_type_str)
    dp = A.get_demand_period_id(demand_period_str)
    # do not check connectivity of OD pairs
    _read_demand(input_dir, filename, at, dp, A.network.zones, A.column_pool, False)


def _read_zones(ui, input_dir='.', filename='syn_zone.csv'):
    """ read syn_zone.csv to set up (synthetic) zones """
    with open(input_dir+'/'+filename, 'r') as fp:
        print('read syn_zone.csv')

        A = ui._base_assignment
        zones = A.network.zones
        zones.clear()

        node_objs = A.get_nodes()

        reader = csv.DictReader(fp)
        for line in reader:
            zone_id = line['zone_id']
            if not zone_id:
                continue

            nodes = line['activity_nodes']
            if not nodes:
                continue

            # just in case that there is empty space in between ';'
            node_ids = [x.strip() for x in nodes.split(';') if x.strip()]
            if not node_ids:
                continue

            try:
                bin_index = _convert_str_to_int(line['bin_index'])
            except (KeyError, InvalidRecord):
                bin_index = 0

            try:
                x = _convert_str_to_float(line['x_coord'])
                y = _convert_str_to_float(line['y_coord'])
            except (KeyError, InvalidRecord):
                x = 91
                y = 181

            try:
                U, D, L, R = _convert_boundaries(line['geometry'])
            except (KeyError, InvalidRecord):
                U = D = L = R = ''

            try:
                prod = _convert_str_to_int(line['production'])
            except (KeyError, InvalidRecord):
                prod = 0

            if zone_id not in zones:
                z = Zone(zone_id, bin_index)
                z.activity_nodes = [x for x in node_ids]
                z.nodes = [x for x in node_ids]
                z.set_coord(x, y)
                z.set_geo(U, D, L, R)
                z.set_production(prod)
                zones[zone_id] = z
                # update zone info for each node
                for id in node_ids:
                    try:
                        no = A.get_node_no(id)
                        node_objs[no].zone_id = zone_id
                    except (IndexError, KeyError):
                        continue
            else:
                raise Exception(f'DUPLICATE zone id: {zone_id}')

        print(f'the number of zones is {len(zones):,d}')


def read_demand_matrix(input_dir, agent_type_id, demand_period_id,
                       zone_to_node_dict, column_pool):
    """ read demand matrix from input_matrix

    not in use
    """
    with open(input_dir+'/input_matrix.csv', 'r') as fp:
        print('read input_matrix.csv')

        at = agent_type_id
        dp = demand_period_id

        total_vol = 0
        reader = csv.DictReader(fp)
        for line in reader:
            oz_id = line['od']
            # o_zone_id does not exist in node.csv, discard it
            if oz_id not in zone_to_node_dict:
                continue

            for dz_str, vol_str in line:
                dz_id = _convert_str_to_int(dz_str)
                if dz_id == oz_id:
                    continue

                # d_zone_id does not exist in node.csv, discard it
                if dz_id not in zone_to_node_dict:
                    continue

                try:
                    vol = _convert_str_to_float(vol_str)
                except InvalidRecord:
                    continue

                if vol == 0:
                    continue

                if not _are_od_connected(oz_id, dz_id):
                    continue

                if (at, dp, oz_id, dz_id) not in column_pool:
                    column_pool[(at, dp, oz_id, dz_id)] = ColumnVec()
                    column_pool[(at, dp, oz_id, dz_id)].set_volume(vol)
                else:
                    raise Exception(
                        f'DUPLICATE OD pair found between {oz_id} and {dz_id}'
                    )

                total_vol += vol

            print(f'the number of agents is {total_vol}')

            if total_vol == 0:
                raise Exception(
                    'NO VALID OD VOLUME!! DOUBLE CHECK YOUR input_matrix.csv'
                )


def _auto_setup(assignment):
    """ automatically set up one demand period and one agent type

    The two objects will be set up using the default constructors using the
    default values. See class DemandPeriod and class AgentType for details
    """
    at = AgentType()
    dp = DemandPeriod()
    d = Demand()

    assignment.update_agent_types(at)
    assignment.update_demand_periods(dp)
    assignment.update_demands(d)


def read_settings(input_dir, assignment):
    try:
        import yaml as ym

        with open(input_dir+'/settings.yml') as file:
            print('read settings.yml\n')

            settings = ym.full_load(file)

            # agent types
            agents = settings['agents']
            for i, a in enumerate(agents):
                agent_type = a['type']
                agent_name = a['name']
                # possible duplication check
                if agent_type in assignment.map_atstr_id:
                    warnings.warn(f'duplicate agent type found: {agent_type}')
                    continue

                agent_vot = a['vot']
                agent_flow_type = a['flow_type']
                agent_pce = a['pce']
                agent_ffs = a['free_speed']

                try:
                    agent_use_link_ffs = a['use_link_ffs']
                except KeyError:
                    agent_use_link_ffs = True

                at = AgentType(i,
                               agent_type,
                               agent_name,
                               agent_vot,
                               agent_flow_type,
                               agent_pce,
                               agent_ffs,
                               agent_use_link_ffs)

                assignment.update_agent_types(at)

            # add the default mode if it does not exist
            if AgentType.get_default_type_str() not in assignment.map_atstr_id:
                assignment.update_agent_types(AgentType())

            # demand periods
            demand_periods = settings['demand_periods']
            for i, d in enumerate(demand_periods):
                period = d['period']
                time_period = d['time_period']

                dp = DemandPeriod(i, period, time_period)
                # special event
                try:
                    s = d['special_event']
                    enable = s['enable']
                    # no need to set up a special event if it is off
                    if not enable:
                        raise KeyError

                    name = s['name']
                    se = SpecialEvent(name)

                    links = s['affected_links']
                    for link in links:
                        link_id = str(link['link_id'])
                        ratio = link['capacity_ratio']
                        se.affected_links[link_id] = ratio

                    dp.special_event = se
                except KeyError:
                    pass

                assignment.update_demand_periods(dp)

            # demand files
            demands = settings['demand_files']
            for i, d in enumerate(demands):
                demand_file = d['file_name']
                demand_period = d['period']
                demand_type = d['agent_type']

                if demand_type not in assignment.map_atstr_id:
                    raise Exception(
                        f'{demand_type} is not found as an entry of agents in settings.yml'
                    )

                demand = Demand(i, demand_period, demand_type, demand_file)
                assignment.update_demands(demand)

            # simulation setup
            try:
                simulation = settings['simulation']
                # simulation resolution
                res = simulation['resolution']
                assert(int(res)>1)
                assignment.set_simu_resolution(int(res))
                # simulation timings
                dp_str = simulation['period']
                dp = assignment.get_demand_period(dp_str)
                st = dp.get_start_time()
                dur = dp.get_duration()
                assignment.set_simu_start_time(st)
                assignment.set_simu_duration(dur)
            except KeyError:
                pass

    except ImportError:
        # just in case user does not have pyyaml installed
        # warnings.warn(
        #     'Please install pyyaml next time!\n'
        #     'Engine will set up one demand period and one agent type using '
        #     'default values for you, which might NOT reflect your case!'
        # )
        _auto_setup(assignment)
    except FileNotFoundError:
        # just in case user does not provide settings.yml
        # warnings.warn(
        #     'Please provide settings.yml next time!\n'
        #     'Engine will set up one demand period and one agent type using '
        #     'default values for you, which might NOT reflect your case!'
        # )
        _auto_setup(assignment)
    except Exception as e:
        raise e


def read_network(length_unit='mile', speed_unit='mph', input_dir='.'):
    len_units = ['kilometer', 'km', 'meter', 'm', 'mile', 'mi']
    spd_units = ['kmh', 'kph', 'mph']

    # length and speed units check
    # linear search is OK for such small lists
    if length_unit not in len_units:
        units = ', '.join(len_units)
        raise Exception(
            f'Invalid length unit: {length_unit} !'
            f' Please choose one available unit from {units}'
        )

    if speed_unit not in spd_units:
        units = ', '.join(spd_units)
        raise Exception(
            f'Invalid speed unit: {speed_unit} !'
            f' Please choose one available unit from {units}'
        )

    assignm = Assignment()
    network = Network()

    read_settings(input_dir, assignm)

    read_nodes(input_dir,
               network.nodes,
               network.map_id_to_no,
               network.map_no_to_id,
               network.zones,
               load_demand)

    read_links(input_dir,
               network.links,
               network.nodes,
               network.map_id_to_no,
               network.link_ids,
               assignm.get_demand_period_count(),
               length_unit,
               speed_unit,
               load_demand)

    network.update()
    assignm.network = network

    return UI(assignm)


def load_columns(ui, input_dir='.'):
    with open(input_dir+'/route_assignment.csv', 'r') as f:
        print('read route_assignment.csv')

        A = ui._base_assignment
        cp = A.get_column_pool()

        # just in case agent_id was not output
        last_agent_id = 0
        reader = csv.DictReader(f)
        for line in reader:
            # critical info
            oz_id = line['o_zone_id']
            dz_id = line['d_zone_id']

            try:
                vol = _convert_str_to_float(line['volume'])
            except InvalidRecord:
                continue

            # skip zero-volume column
            if not vol:
                continue

            node_seq = line['node_sequence']
            if not node_seq:
                continue

            link_seq = line['link_sequence']
            if not link_seq:
                continue

            # non-critical info
            try:
                agent_id = _convert_str_to_int(line['agent_id'])
            except InvalidRecord:
                agent_id = last_agent_id + 1

            last_agent_id = agent_id

            # it could be empty
            # path_id = line['path_id']

            at = line['agent_type']
            if not at:
                continue
            else:
                # back-compatible on 'p' and 'passenger'
                try:
                    at = A.get_agent_type_id(at)
                except Exception:
                    # replace 'p' with 'a'
                    if at.startswith(AgentType.get_legacy_type_str()):
                        at = A.get_agent_type_id(AgentType.get_default_type_str())
                    else:
                        warnings.warn(
                            f'agent_type {at} is not existing in settings.yml.'
                            'this record is discarded'
                        )
                        continue

            dp = line['demand_period']
            if not dp:
                continue
            else:
                dp = A.get_demand_period_id(dp)

            try:
                toll = _convert_str_to_float(line['toll'])
            except InvalidRecord:
                toll = 0

            try:
                tt = _convert_str_to_float(line['travel_time'])
            except InvalidRecord:
                tt = 0

            try:
                dist = _convert_str_to_float(line['distance'])
            except InvalidRecord:
                dist = 0

            # it could be empty
            geo = line['geometry']

            if (at, dp, oz_id, dz_id) not in cp:
                cp[(at, dp, oz_id, dz_id)] = ColumnVec()

            cv = A.get_column_vec(at, dp, oz_id, dz_id)
            path_id = cv.get_column_num()
            col = Column(path_id)

            try:
                col.nodes = [A.get_node_no(x) for x in reversed(node_seq.split(';')) if x]
            except KeyError:
                raise Exception(
                    'Invalid node found on column!!'
                    'Did you use route_assignment.csv from a different network?'
                )

            try:
                # if x is only needed for columns generated from DTALite,
                # which have the trailing ';' and leads to '' after split
                col.links = [
                    A.get_link_no(x) for x in reversed(link_seq.split(';')) if x
                ]
            except KeyError:
                raise Exception(
                    'INVALID link found on column!!'
                    'Did you use route_assignment.csv from a different network?'
                )
            except ValueError:
                raise Exception(
                    f'INVALID LINK PATH found for agent id: {agent_id}'
                )

            # the following four are non-critical info
            col.set_volume(vol)
            col.set_toll(toll)
            col.set_travel_time(tt)
            col.set_geometry(geo)

            # deprecate node_sum and adopt the same implementation in colgen.py
            existing = False

            if dist == 0:
                sum(A.get_link(x).get_length() for x in col.links)

            for col_ in cv.get_columns():
                if col_.get_distance() != dist:
                    continue

                if col_.get_links() == col.links:
                    col_.increase_volume(vol)
                    existing = True
                    break

            if not existing:
                col.set_distance(dist)
                cv.add_new_column(col)
                cv.increase_volume(vol)

        update_links_using_columns(ui)


def output_columns(ui, output_geometry=True, output_dir='.'):
    with open(output_dir+'/route_assignment.csv', 'w',  newline='') as fp:
        base = ui._base_assignment

        nodes = base.get_nodes()
        links = base.get_links()
        column_pool = base.get_column_pool()

        writer = csv.writer(fp)

        line = ['agent_id',
                'o_zone_id',
                'd_zone_id',
                'path_id',
                'agent_type',
                'demand_period',
                'volume',
                'toll',
                'travel_time',
                'distance',
                'node_sequence',
                'link_sequence',
                'geometry']

        writer.writerow(line)

        path_sep = ';'
        i = 0
        for k, cv in column_pool.items():
            # k = (at_id, dp_id, oz_id, dz_id)
            at_id = k[0]
            dp_id = k[1]
            oz_id = k[2]
            dz_id = k[3]

            at_str = base.get_agent_type_str(at_id)
            dp_str = base.get_demand_period_str(dp_id)

            for col in cv.get_columns():
                # skip zero-volume column
                if not col.get_volume():
                    continue

                i += 1
                node_seq = path_sep.join(
                    nodes[x].get_node_id() for x in reversed(col.nodes)
                )
                link_seq = path_sep.join(
                    links[x].get_link_id() for x in reversed(col.links)
                )

                geometry = ''
                if output_geometry:
                    geometry = ', '.join(
                        nodes[x].get_coordinate() for x in reversed(col.nodes)
                    )
                    geometry = 'LINESTRING (' + geometry + ')'

                line = [i,
                        oz_id,
                        dz_id,
                        col.get_id(),
                        at_str,
                        dp_str,
                        '{:.4f}'.format(col.get_volume()),
                        col.get_toll(),
                        col.get_travel_time(),
                        col.get_distance(),
                        node_seq,
                        link_seq,
                        geometry]

                writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck route_assignment.csv in {os.getcwd()} for path finding results')
        else:
            print(
                f'\ncheck route_assignment.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for path finding results'
            )


def output_link_performance(ui, mode='ue', output_dir='.'):
    with open(output_dir+'/link_performance.csv', 'w',  newline='') as fp:
        writer = csv.writer(fp)

        line = ['link_id',
                'from_node_id',
                'to_node_id',
                'time_period',
                'volume',
                'travel_time',
                'speed',
                'VOC',
                'geometry']

        if mode.lower().startswith('odme'):
            line.append('obs_count')
            line.append('deviation')

        writer.writerow(line)

        base = ui._base_assignment
        links = base.get_links()

        if not mode.lower().startswith('odme'):
            # UE or UE + Simulation
            for link in links:
                # connector
                if not link.length:
                    continue

                for dp in base.get_demand_periods():
                    avg_tt = link.get_period_avg_travel_time(dp.get_id())
                    speed = link.get_length() / (max(EPSILON, avg_tt) / 60)

                    line = [link.get_link_id(),
                            link.get_from_node_id(),
                            link.get_to_node_id(),
                            dp.get_period(),
                            link.get_period_flow_vol(dp.get_id()),
                            avg_tt,
                            speed,
                            link.get_period_voc(dp.get_id()),
                            link.get_geometry()]

                    writer.writerow(line)
        else:
            # ODME
            for link in links:
                # connector
                if not link.length:
                    continue

                for dp in base.get_demand_periods():
                    avg_tt = link.get_period_avg_travel_time(dp.get_id())
                    speed = link.get_length() / (max(EPSILON, avg_tt) / 60)

                    obs_count = ''
                    dev = ''
                    if dp.get_id() == 0:
                        obs_count = link.obs
                        dev = link.est_dev

                    line = [link.get_link_id(),
                            link.get_from_node_id(),
                            link.get_to_node_id(),
                            dp.get_period(),
                            link.get_period_flow_vol(dp.get_id()),
                            avg_tt,
                            speed,
                            link.get_period_voc(dp.get_id()),
                            link.get_geometry(),
                            obs_count,
                            dev]

                    writer.writerow(line)

        if output_dir == '.':
            print(f'check link_performance.csv in {os.getcwd()} for link performance')
        else:
            print(
                f'check link_performance.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for link performance'
            )


def output_agent_paths(ui, output_geometry=True, output_dir='.'):
    """ output unique agent path

    use it with find_path_for_agents() (which has been DEPRECATED)
    """
    with open(output_dir+'/agent_paths.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        line = ['agent_id',
                'o_zone_id',
                'd_zone_id',
                'origin node',
                'destination node',
                'path_id',
                'agent_type',
                'demand_period',
                'OD volume',
                'distance',
                'node_sequence',
                'link_sequence',
                'geometry']

        writer.writerow(line)

        base = ui._base_assignment
        nodes = base.get_nodes()
        agents = base.get_agents()
        agents.sort(key=lambda agent: agent.get_orig_node_id())

        at_str = ''
        dp_str = ''
        for a in agents:
            if not a.get_node_path():
               continue

            at_str = base.get_agent_type_str(a.get_at_id())
            dp_str = base.get_demand_period_str(a.get_dp_id())
            break

        pre_dest_node_id = -1
        for a in agents:
            if not a.get_node_path():
               continue

            if a.get_dest_node_id() == pre_dest_node_id:
                continue

            pre_dest_node_id = a.get_dest_node_id()
            id = a.get_id()

            at = a.get_at_id()
            dp = a.get_dp_id()
            oz = a.get_orig_zone_id()
            dz = a.get_dest_zone_id()

            vol = base.column_pool[(at, dp, oz, dz)].get_od_volume()

            geometry = ''
            if output_geometry:
                geometry = ', '.join(
                    nodes[x].get_coordinate() for x in reversed(a.get_node_path())
                )
                geometry = 'LINESTRING (' + geometry + ')'

            line = [id,
                    oz,
                    dz,
                    a.get_orig_node_id(),
                    a.get_dest_node_id(),
                    0,
                    at_str,
                    dp_str,
                    vol,
                    a.get_path_cost(),
                    base.get_agent_node_path(id, True),
                    base.get_agent_link_path(id, True),
                    geometry]

            writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck agent_paths.csv in {os.getcwd()} for unique agent paths')
        else:
            print(
                f'\ncheck agent_paths.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for unique agent paths'
            )


def output_synthetic_zones(ui, output_dir='.'):
    with open(output_dir+'/syn_zone.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        line = ['zone_id',
                'bin_index',
                'activity_nodes',
                'x_coord',
                'y_coord',
                'geometry',
                'production',
                'attraction']

        writer.writerow(line)

        base = ui._base_assignment
        network = base.network
        zones = network.zones

        for k, v in zones.items():
            bi = v.get_bin_index()
            nodes = '; '.join(str(x) for x in v.get_activity_nodes())
            # [U, D, L, R] = v.get_boundaries()
            x, y = v.get_coordinate()
            prod = v.get_production()
            geo = v.get_geo()

            line = [k, bi, nodes, x, y, geo, prod, prod]
            writer.writerow(line)

        if output_dir == '.':
            print(f'check zone.csv in {os.getcwd()} for synthetic zones')
        else:
            print(
                f'check zone.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for synthetic zones'
            )


def output_synthetic_demand(ui, output_dir='.'):
    with open(output_dir+'/syn_demand.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        line = ['o_zone_id', 'd_zone_id', 'volume']
        writer.writerow(line)

        column_pool = ui.get_column_pool()
        for k, v in column_pool.items():
            # k = (at_id, dp_id, oz_id, dz_id)
            line = [k[2], k[3], v.get_od_volume()]
            writer.writerow(line)

        if output_dir == '.':
            print(f'check demand.csv in {os.getcwd()} for synthetic demand\n')
        else:
            print(
                f'check demand.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for synthetic demand\n'
            )


def output_agent_trajectory(ui, output_dir='.'):
    with open(output_dir+'/trajectory.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        line = ['agent_id',
                'o_zone_id',
                'd_zone_id',
                'departure_time_in_min',
                'arrival_time_in_min',
                'complete_trip',
                'travel_time_in_min',
                'PCE',
                'distance',
                'node_sequence',
                'geometry',
                'time_sequence',
                'time_sequence_hhmmss']

        writer.writerow(line)

        A = ui._base_assignment
        nodes = A.get_nodes()
        agents = A.get_agents()
        st = A.get_simu_start_time()

        pre_dt = -1
        pre_od = -1, -1
        for a in agents:
            if a.get_node_path() is None:
                continue

            # do not output agents of the same OD pair with the same departure time
            if a.get_dep_time() == pre_dt and a.get_od() == pre_od:
                continue

            pre_dt = a.get_dep_time()
            pre_od = a.get_od()

            at = A.cast_interval_to_minute_float(a.link_arr_interval[-1]) + st
            dt = A.cast_interval_to_minute_float(a.link_dep_interval[-1]) + st
            time_seq1 = [at, dt]
            time_seq2 = [_get_time_stamp(at), _get_time_stamp(dt)]

            num = len(a.link_arr_interval) - 2
            # if num < 0, the following loop will be skipped
            for i in range(num, -1, -1):
                k = a.link_dep_interval[i]
                if k < 0:
                    break

                dt_ = A.cast_interval_to_minute_float(k) + st
                time_seq1.append(dt_)
                time_seq2.append(_get_time_stamp(dt_))

            time_seq1_str = ';'.join(str(t) for t in time_seq1)
            time_seq2_str = ';'.join(time_seq2)

            complete_trip = 'c'
            if a.link_dep_interval[0] < 0:
                complete_trip = 'n'

            # arrival time to the last node or departure time from the last link
            at_ = time_seq1[-1]
            # the original implementation using arrival time to the last link
            # to calculate trip time does not make sense
            tt = at_ - a.get_dep_time()

            node_path_str = A.get_agent_node_path(a.get_id(), True)
            geometry = ', '.join(
                nodes[x].get_coordinate() for x in reversed(a.get_node_path())
            )
            geometry = 'LINESTRING (' + geometry + ')'

            line = [a.get_id(),
                    a.get_orig_zone_id(),
                    a.get_dest_zone_id(),
                    a.get_dep_time(),
                    at_,
                    complete_trip,
                    tt,
                    a.PCE_factor,
                    a.get_path_cost(),
                    node_path_str,
                    geometry,
                    time_seq1_str,
                    time_seq2_str]

            writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck trajectory.csv in {os.getcwd()} for trajectories')
        else:
            print(
                f'\ncheck trajectory.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for trajectories'
            )


def read_measurements(ui, input_dir='.'):
    """ load traffic observations specified in measurement.csv """
    with open(input_dir+'/measurement.csv') as fp:
        print('read measurement.csv')

        base = ui._base_assignment
        map_id_to_no = base.network.map_id_to_no
        zones = base.network.zones

        links = base.get_links()
        # a temporary lookup table to retrieve a link using its head and tail
        link_lookup = {
            (link.from_node_no, link.to_node_no) : link for link in links
        }

        reader = csv.DictReader(fp)
        record_no = 0
        for line in reader:
            # get measurement type, which could be link, production, and attraction
            meas_type = line['measurement_type']
            if not meas_type:
                continue

            try:
                count = _convert_str_to_float(line['count'])
            except KeyError:
                count = _convert_str_to_float(line['count1'])
            except InvalidRecord:
                continue

            try:
                ub = line['upper_bound_flag']
            except KeyError:
                ub = 'false'

            is_upper_bounded = False
            ub_lowercase = ub.lower()
            if ub_lowercase.startswith('true') or ub_lowercase.startswith('1'):
                is_upper_bounded = True
                # all the other strings will be taken as False

            if meas_type.startswith('link'):
                from_node_id = line['from_node_id']
                to_node_id = line['to_node_id']

                try:
                    from_node_no = map_id_to_no[from_node_id]
                except KeyError:
                    print(
                        f'Exception: Node ID {from_node_id}'
                        ' NOT in the network!!'
                    )
                    continue

                try:
                    to_node_no = map_id_to_no[to_node_id]
                except KeyError:
                    print(
                        f'Exception: Node ID {to_node_id}'
                        ' NOT in the network!!'
                    )
                    continue

                # need to retrieve the link using from node and to node
                link_key = (from_node_no, to_node_no)
                if link_key not in link_lookup:
                    continue

                link = link_lookup[link_key]
                link.obs = count
                link.is_obs_upper_bounded = is_upper_bounded
            elif meas_type.startswith('production'):
                try:
                    zone_id = line['o_zone_id']
                except KeyError:
                    continue

                if not zone_id or zone_id not in zones:
                    continue

                zone = zones[zone_id]
                zone.prod_obs = count
                zone.is_prod_obs_upper_bounded = is_upper_bounded
            elif meas_type.startswith('attraction'):
                try:
                    zone_id = line['d_zone_id']
                except KeyError:
                    continue

                if not zone_id or zone_id not in zones:
                    continue

                zone = zones[zone_id]
                zone.attr_obs = count
                zone.is_attr_obs_upper_bounded = is_upper_bounded
            else:
                continue

            record_no += 1

        print(f'the number of valid measurements is {record_no}\n')


def read_demand(ui, use_synthetic_data = False, save_synthetic_data=True, input_dir='.'):
    """ a dedicated API to read demand and zone information """
    A = ui._base_assignment

    if not use_synthetic_data:
        # set up capacity ratio of affected links from special event
        for dp in A.demand_periods:
            se = dp.special_event
            if se is None:
                continue

            # k is link id and v is capacity ratio
            for k, v in se.get_affected_links():
                A.set_capacity_ratio(dp.get_id(), k, v)

        print('load demand')
        print('Step 1: try to load the default demand file: demand.csv')
        demand_loaded = False
        for d in A.get_demands():
            try:
                at = A.get_agent_type_id(d.get_agent_type_str())
                dp = A.get_demand_period_id(d.get_period())
                _read_demand(input_dir,
                             d.get_file_name(),
                             at,
                             dp,
                             A.network.zones,
                             A.column_pool)

                if not demand_loaded:
                    demand_loaded = True
            except FileNotFoundError:
                continue

        if demand_loaded:
            return

        print('the default demand files are NOT found!\n')

    # try to load the synthetic demand
    filename = 'syn_demand.csv'
    if use_synthetic_data:
        print(f'attempt to load the synthetic data: {filename} and syn_zone.csv')
    else:
        print(f'Step 2: attempt to load the synthetic data: {filename} and syn_zone.csv')

    for d in A.get_demands():
        try:
            at = A.get_agent_type_id(d.get_agent_type_str())
            dp = A.get_demand_period_id(d.get_period())
            _read_zones(ui)
            _read_demand(
                input_dir, filename, at, dp, A.network.zones, A.column_pool
            )
            # early termination to load only one synthetic demand file
            return
        except FileNotFoundError:
            break

    print('the synthetic data is missing or incomplete!\n')
    if use_synthetic_data:
        print('start to synthesize zones and demand!')
    else:
        print('Step 3: start to synthesize zones and demand!')

    # synthesize zones and demand
    network_to_zones(ui)
    print('data synthesis is complete!')

    if save_synthetic_data:
        output_synthetic_zones(ui, input_dir)
        output_synthetic_demand(ui, input_dir)