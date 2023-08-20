import os
import csv
import threading
import warnings
from datetime import timedelta

from .classes import Node, Link, Zone, Network, Column, ColumnVec, VDFPeriod, \
                     AgentType, DemandPeriod, Demand, SpecialEvent, Assignment, UI

from .colgen import update_links_using_columns
from .consts import MILE_TO_METER, MPH_TO_KPH, SMALL_DIVISOR


__all__ = [
    'read_network',
    'read_zones',
    'load_demand',
    'load_columns',
    'output_columns',
    'output_link_performance',
    'download_sample_data_sets',
    'download_sample_setting_file',
    'output_agent_paths',
    'output_zones',
    'output_synthesized_demand',
    'output_agent_trajectory'
]


class InvalidRecord(Exception):
    """a custom exception for invalid input from parsing a csv file"""
    pass


# for precheck on connectivity of each OD pair
# 0: isolated, has neither outgoing links nor incoming links
# 1: has at least one outgoing link
# 2: has at least one incoming link
# 3: has both outgoing and incoming links
_zone_degrees = {}


def _update_orig_zone(oz_id):
    if oz_id not in _zone_degrees:
        _zone_degrees[oz_id] = 1
    elif _zone_degrees[oz_id] == 2:
        _zone_degrees[oz_id] = 3


def _update_dest_zone(dz_id):
    if dz_id not in _zone_degrees:
        _zone_degrees[dz_id] = 2
    elif _zone_degrees[dz_id] == 1:
        _zone_degrees[dz_id] = 3


def _are_od_connected(oz_id, dz_id):
    connected = True

    # at least one node in O must have outgoing links
    if oz_id not in _zone_degrees or _zone_degrees[oz_id] == 2:
        connected = False
        print(f'WARNING! {oz_id} has no outgoing links to route volume '
              f'between OD: {oz_id} --> {dz_id}')

    # at least one node in D must have incoming links
    if dz_id not in _zone_degrees or _zone_degrees[dz_id] == 1:
        if connected:
            connected = False
        print(f'WARNING! {dz_id} has no incoming links to route volume '
              f'between OD: {oz_id} --> {dz_id}')

    return connected


# a little bit ugly
def _convert_str_to_int(s):
    if not s:
        raise InvalidRecord

    try:
        return int(s)
    except ValueError:
        # if s is not numeric, a ValueError will be then caught
        try:
            return int(float(s))
        except ValueError:
            raise InvalidRecord
    except TypeError:
        raise InvalidRecord


def _convert_str_to_float(s):
    if not s:
        raise InvalidRecord

    try:
        return float(s)
    except (TypeError, ValueError):
        raise InvalidRecord


def _convert_boundaries(bs):
    """a helper function to facilitate read_zones()"""
    if not bs:
        raise InvalidRecord

    prefix = 'LINESTRING ('
    postfix = ')'

    try:
        b = bs.index(prefix) + len(prefix)
        e = bs.index(postfix)
    except ValueError:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    bs_ = bs[b:e]
    vs = [x for x in bs_.split(',')]

    # validation
    if len(vs) != 5:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    if vs[0] != vs[-1]:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    L, U = vs[0].split(' ')
    R, U_ = vs[1].split(' ')
    if U != U_:
        raise Exception(
            f'Invalid Zone Boundaries: inconsistent upper boundary {U}; {U_}'
        )

    R_, D = vs[2].split(' ')
    if R != R_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent right boundary {R}; {R_}'
        )

    L_, D_ = vs[3].split(' ')
    if L != L_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent left boundary {L}; {L_}'
        )

    if D != D_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent lower boundary {D}; {D_}'
        )

    U = _convert_str_to_float(U)
    D = _convert_str_to_float(D)
    L = _convert_str_to_float(L)
    R = _convert_str_to_float(R)

    return U, D, L, R


def _get_time_stamp(minute):
    """ covert minute into HH:MM:SS as string """
    s = minute * 60
    return str(timedelta(seconds=s))


def _download_url(url, filename, loc_dir):
    try:
        import requests
    except ImportError:
        print('please print requests to proceed downloading!!')

    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(loc_dir+filename, 'wb') as f:
            f.write(r.content)
    except requests.HTTPError:
        print(f'file not existing: {url}')
    except requests.ConnectionError:
        raise Exception('check your connection!!!')
    except Exception as e:
        raise e


def download_sample_data_sets():
    """ download sample data sets from the Github repo

    the following data sets will be downloaded: ASU, Braess Paradox, Chicago Sketch,
    Lima Network, Sioux Falls, and Two Corridors.
    """
    url = 'https://raw.githubusercontent.com/jdlph/Path4GMNS/dev/data/'

    data_sets = [
        "ASU",
        "Braess_Paradox",
        "Chicago_Sketch",
        "Lima_Network",
        "Sioux_Falls",
        "Two_Corridor"
    ]

    files = [
        "node.csv",
        "link.csv",
        "demand.csv",
        "settings.csv",
        "settings.yml"
    ]

    print('downloading starts')

    # data folder under cdw
    loc_data_dir = 'data'
    if not os.path.isdir(loc_data_dir):
        os.mkdir(loc_data_dir)

    for ds in data_sets:
        web_dir = url + ds + '/'
        loc_sub_dir = os.path.join(loc_data_dir, ds) + '/'

        if not os.path.isdir(loc_sub_dir):
            os.mkdir(loc_sub_dir)

        # multi-threading
        threads = []
        for x in files:
            t = threading.Thread(
                target=_download_url,
                args=(web_dir+x, x, loc_sub_dir)
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    print('downloading completes')
    print(f'check {os.path.join(os.getcwd(), loc_data_dir)} for downloaded data sets')


def download_sample_setting_file():
    """ download the sample settings.yml from the Github repo """
    url = 'https://raw.githubusercontent.com/jdlph/Path4GMNS/dev/tests/settings.yml'
    filename = 'settings.yml'
    loc_dir = './'

    _download_url(url, filename, loc_dir)

    print('downloading completes')
    print(f'check {os.getcwd()} for downloaded settings.yml')


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
            if node_id in map_id_to_no.keys():
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
                b = _convert_str_to_int(line['is_boundary'])
                if b > 0:
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
            if zone_id not in zones.keys():
                # only take the value of bin_index from the first node
                # associated with each zone
                z = Zone(zone_id, bin_index)
                zones[zone_id] = z

            zones[zone_id].add_node(node_id)
            if is_activity_node:
                zones[zone_id].add_activity_node(node_id)

            node_no += 1

        print(f'the number of nodes is {node_no}')

        if load_demand:
            zone_size = len(zones)
            if '' in zones.keys():
                zone_size -= 1

            if zone_size == 0:
                raise Exception('there are NO VALID zones from node.csv')

            print(f'the number of zones is {zone_size}')


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
        for line in reader:
            # it can be an empty string
            link_id = line['link_id']

            # validity check
            from_node_id = line['from_node_id']
            to_node_id = line['to_node_id']

            try:
                from_node_no = map_id_to_no[from_node_id]
                to_node_no = map_id_to_no[to_node_id]
            except KeyError:
                print(
                    f'EXCEPTION: Node ID {from_node_id} '
                    f'or/and Node ID {to_node_id} NOT IN THE NETWORK!!'
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
            except InvalidRecord:
                capacity = 1999

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
                    VDF_fftt = length / max(SMALL_DIVISOR, free_speed) * 60

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

        print(f'the number of links is {link_no}')


def read_demand(input_dir,
                file,
                agent_type_id,
                demand_period_id,
                zones,
                column_pool,
                check_connectivity=True):
    """ step 3:read input_agent """
    with open(input_dir+'/'+file, 'r') as fp:
        print('read '+file)

        at = agent_type_id
        dp = demand_period_id
        column_pool.clear()

        reader = csv.DictReader(fp)
        total_vol = 0
        for line in reader:
            oz_id = line['o_zone_id']
            # o_zone_id does not exist in node.csv, discard it
            if oz_id not in zones.keys():
                continue

            dz_id = line['d_zone_id']
            # d_zone_id does not exist in node.csv, discard it
            if dz_id not in zones.keys():
                continue

            try:
                volume = _convert_str_to_float(line['volume'])
            except InvalidRecord:
                continue

            if volume == 0:
                continue

            # precheck on connectivity of each OD pair
            if check_connectivity and not _are_od_connected(oz_id, dz_id):
                continue

            # set up volume for ColumnVec
            if (at, dp, oz_id, dz_id) not in column_pool.keys():
                column_pool[(at, dp, oz_id, dz_id)] = ColumnVec()
            column_pool[(at, dp, oz_id, dz_id)].increase_volume(volume)

            total_vol += volume

        print(f'the total demand is {total_vol:.2f}')

        if total_vol == 0:
            raise Exception(
                'NO VALID OD VOLUME!! Double check your demand.csv and '
                'make sure there is zone info in node.csv'
            )


def load_demand(ui,
                agent_type_str='a',
                demand_period_str='AM',
                input_dir='.',
                filename='demand.csv'):
    """
    load demand for an agent type and a demand period

    this is an user interface while read_demand() is intended for internal use.
    """
    A = ui._base_assignment

    at = A.get_agent_type_id(agent_type_str)
    dp = A.get_demand_period_id(demand_period_str)
    # do not check connectivity of OD pairs
    read_demand(input_dir, filename, at, dp, A.network.zones, A.column_pool, False)


def read_zones(ui, input_dir='.', filename='zone.csv'):
    """ read zone.csv to set up zones """
    with open(input_dir+'/'+filename, 'r') as fp:
        print('read zone.csv')

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

            try:
                node_ids = [int(x) for x in nodes.split(';') if x]
            except ValueError:
                raise Exception(
                    f'INVALID ACCESS NODES for zone id: {zone_id}'
                )

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

            if zone_id not in zones.keys():
                z = Zone(zone_id, bin_index)
                z.activity_nodes = [int(x) for x in node_ids]
                z.nodes = [x for x in z.activity_nodes]
                z.setup_geo(U, D, L, R, x, y)
                z.setup_production(prod)
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

        print(f'the number of zones is {len(zones)}')


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
            if oz_id not in zone_to_node_dict.keys():
                continue

            for dz_str, vol_str in line:
                dz_id = _convert_str_to_int(dz_str)
                if dz_id == oz_id:
                    continue

                # d_zone_id does not exist in node.csv, discard it
                if dz_id not in zone_to_node_dict.keys():
                    continue

                try:
                    vol = _convert_str_to_float(vol_str)
                except InvalidRecord:
                    continue

                if vol == 0:
                    continue

                if not _are_od_connected(oz_id, dz_id):
                    continue

                if (at, dp, oz_id, dz_id) not in column_pool.keys():
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
            print('read settings.yml')

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
                    agent_use_link_ffs= True

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
        warnings.warn('Please install pyyaml next time!')
        warnings.warn(
            'Engine will set up one demand period and one agent type using '
            'default values for you, which might NOT reflect your case!\n'
        )
        _auto_setup(assignment)
    except FileNotFoundError:
        # just in case user does not provide settings.yml
        warnings.warn('Please provide settings.yml next time!')
        warnings.warn(
            'Engine will set up one demand period and one agent type using '
            'default values for you, which might NOT reflect your case!\n'
        )
        _auto_setup(assignment)
    except Exception as e:
        raise e


def read_network(length_unit='mile', speed_unit='mph', load_demand=False, input_dir='.'):
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

    if load_demand:
        for d in assignm.get_demands():
            at = assignm.get_agent_type_id(d.get_agent_type_str())
            dp = assignm.get_demand_period_id(d.get_period())
            read_demand(input_dir,
                        d.get_file_name(),
                        at,
                        dp,
                        network.zones,
                        assignm.column_pool)

    network.update()
    assignm.network = network

    if load_demand:
        # set up capacity ratio of affected links from special event
        for dp in assignm.demand_periods:
            se = dp.special_event
            if se is None:
                continue

            # k is link id and v is capacity ratio
            for k, v in se.get_affected_links():
                assignm.set_capacity_ratio(dp.get_id(), k, v)

    ui = UI(assignm)

    return ui


def load_columns(ui, input_dir='.'):
    """ developer note: do we use agent.csv to set up network? """
    with open(input_dir+'/agent.csv', 'r') as f:
        print('read agent.csv')

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

            if (at, dp, oz_id, dz_id) not in cp.keys():
                cp[(at, dp, oz_id, dz_id)] = ColumnVec()

            cv = A.get_column_vec(at, dp, oz_id, dz_id)
            path_id = cv.get_column_num()
            col = Column(path_id)

            try:
                col.nodes = [A.get_node_no(x) for x in reversed(node_seq.split(';')) if x]
            except KeyError:
                raise Exception(
                    'Invalid node found on column!!'
                    'Did you use agent.csv from a different network?'
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
                    'Did you use agent.csv from a different network?'
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
    with open(output_dir+'/agent.csv', 'w',  newline='') as fp:
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
            if cv.get_od_volume() <= 0:
                continue

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
                        col.get_volume(),
                        col.get_toll(),
                        col.get_travel_time(),
                        col.get_distance(),
                        node_seq,
                        link_seq,
                        geometry]

                writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck agent.csv in {os.getcwd()} for path finding results')
        else:
            print(
                f'\ncheck agent.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for path finding results'
            )


def output_link_performance(ui, output_dir='.'):
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

        writer.writerow(line)

        base = ui._base_assignment
        links = base.get_links()
        for link in links:
            # connector
            if not link.length:
                continue

            for dp in base.get_demand_periods():
                avg_travel_time = link.get_period_avg_travel_time(dp.get_id())
                speed = link.get_length() / (max(SMALL_DIVISOR, avg_travel_time) / 60)

                line = [link.get_link_id(),
                        link.get_from_node_id(),
                        link.get_to_node_id(),
                        dp.get_period(),
                        link.get_period_flow_vol(dp.get_id()),
                        avg_travel_time,
                        speed,
                        link.get_period_voc(dp.get_id()),
                        link.get_geometry()]

                writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck link_performance.csv in {os.getcwd()} for link performance')
        else:
            print(
                f'\ncheck link_performance.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for link performance'
            )


def output_agent_paths(ui, output_geometry=True, output_dir='.'):
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


def output_zones(ui, output_dir='.'):
    with open(output_dir+'/zone.csv', 'w',  newline='') as f:
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
            print(f'\ncheck zone.csv in {os.getcwd()} for synthesized zones')
        else:
            print(
                f'\ncheck zone.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for synthesized zones'
            )


def output_synthesized_demand(ui, output_dir='.'):
    with open(output_dir+'/demand.csv', 'w',  newline='') as f:
        writer = csv.writer(f)

        line = ['o_zone_id', 'd_zone_id', 'volume']
        writer.writerow(line)

        ODMatrix = ui.get_ODMatrix()
        for k, v in ODMatrix.items():
            line = [k[0], k[1], v]
            writer.writerow(line)

        if output_dir == '.':
            print(f'\ncheck demand.csv in {os.getcwd()} for synthesized demand')
        else:
            print(
                f'\ncheck demand.csv in {os.path.join(os.getcwd(), output_dir)}'
                ' for synthesized demand'
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