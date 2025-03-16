import ctypes
from collections import deque
from copy import deepcopy
from datetime import datetime
from math import ceil, floor
from random import choice, randint

from .consts import EPSILON, MAX_LABEL_COST, SECONDS_IN_MINUTE, SECONDS_IN_HOUR
from .path import benchmark_apsp, find_path_for_agents, find_shortest_path, \
                  get_shortest_path_tree, single_source_shortest_path


__all__ = ['UI']


class Node:

    def __init__(self, node_no, node_id, zone_id, x='', y='', is_activity_node=False):
        """ the attributes of node  """
        # node_no: internal node index used for calculation
        self.node_no = node_no
        # node_id: user defined node id from input
        self.node_id = node_id
        # link objects
        self.outgoing_links = []
        self.incoming_links = []
        self.zone_id = zone_id
        self.coord_x = x
        self.coord_y = y
        self.is_activity_node = is_activity_node

    def has_outgoing_links(self):
        return len(self.outgoing_links) > 0

    def has_incoming_links(self):
        return len(self.incoming_links) > 0

    def get_zone_id(self):
        return self.zone_id

    def get_node_id(self):
        return self.node_id

    def get_node_no(self):
        return self.node_no

    def get_coordinate(self):
        return self.coord_x + ' ' + self.coord_y

    def add_outgoing_link(self, link):
        self.outgoing_links.append(link)

    def add_incoming_link(self, link):
        self.incoming_links.append(link)

    def update_coordinate(self, args):
        self.coord_x = args[0]
        self.coord_y = args[1]

    def get_incoming_link_num(self):
        return len(self.incoming_links)


class Link:

    def __init__(self,
                 id,
                 link_no,
                 from_node_no,
                 to_node_no,
                 from_node_id,
                 to_node_id,
                 length,
                 lanes=1,
                 link_type=1,
                 free_speed=60,
                 capacity=1999,
                 toll = 0,
                 allowed_uses='all',
                 geometry='',
                 demand_period_size=1):
        """ the attributes of link """
        self.id = id
        self.link_no = link_no
        self.from_node_no = from_node_no
        self.to_node_no = to_node_no
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        # length is mile or km
        self.length = length
        self.lanes = lanes
        # 1: one direction, 2: two way
        self.type = link_type
        # free flow travel time in minutes, free_speed is either mile/h or km/h
        self.fftt = (
            length / max(EPSILON, free_speed) * 60
        )
        # capacity is lane capacity per hour
        self.link_capacity = capacity * lanes
        self.allowed_uses = allowed_uses
        self.geometry = geometry
        # add for CG
        self.demand_period_size = demand_period_size
        self.toll = toll
        self.route_choice_cost = 0
        self.travel_time_by_period = [0] * demand_period_size
        self.flow_vol_by_period = [0] * demand_period_size
        self.vdfperiods = []
        # for simulation
        self.cum_arr = None
        self.cum_dep = None
        self.outflow_cap = None
        self.waiting_time = None
        self.entr_queue = deque()
        self.exit_queue = deque()
        # for ODME
        self.obs = 0
        self.est_dev = 0
        self.is_obs_upper_bounded = False

    def get_link_id(self):
        return self.id

    def get_seq_no(self):
        return self.link_no

    def get_from_node_id(self):
        return self.from_node_id

    def get_to_node_id(self):
        return self.to_node_id

    def get_length(self):
        return self.length

    def get_geometry(self):
        return self.geometry

    def get_toll(self):
        return self.toll

    def get_free_flow_travel_time(self):
        return self.fftt

    def get_route_choice_cost(self):
        return self.route_choice_cost

    def get_period_travel_time(self, tau):
        return self.travel_time_by_period[tau]

    def get_period_flow_vol(self, tau):
        return self.flow_vol_by_period[tau]

    def get_period_voc(self, tau):
        return self.vdfperiods[tau].get_voc()

    def get_period_fftt(self, tau):
        try:
            return self.vdfperiods[tau].get_fftt()
        except IndexError:
            raise Exception(f'NO such demand period id: {tau}!'
                            ' Check your input demand_period_id')

    def get_period_avg_travel_time(self, tau):
        return self.vdfperiods[tau].get_avg_travel_time()

    def get_generalized_cost(self, tau, value_of_time):
        return (
            self.travel_time_by_period[tau]
            + self.route_choice_cost
            + self.toll / max(EPSILON, value_of_time) * 60
        )

    def reset_period_flow_vol(self):
        for tau in range(self.demand_period_size):
            self.flow_vol_by_period[tau] = 0

    def increase_period_flow_vol(self, tau, fv):
        self.flow_vol_by_period[tau] += fv

    def calculate_td_vdf(self):
        for tau in range(self.demand_period_size):
            self.travel_time_by_period[tau] = (
                self.vdfperiods[tau].run_bpr(self.flow_vol_by_period[tau])
            )

    def update_waiting_time(self, minute, wt):
        try:
            self.waiting_time[minute] += wt
        except IndexError:
            pass

    def set_capacity_ratio(self, tau, rr):
        self.vdfperiods[tau].capacity_ratio = rr


class Agent:
    """ individual agent derived from aggregated demand between an OD pair

    id: integer starts from 1
    seq_no: internal agent index starting from 0 used for calculation
    """
    def __init__(self, agent_id, agent_no, agent_type_id, demand_period_id,
                 o_zone_id, d_zone_id):
        """ the attribute of agent """
        self.id = agent_id
        self.seq_no = agent_no
        # vehicle
        self.at_id = agent_type_id
        self.dp_id = demand_period_id
        self.o_zone_id = o_zone_id
        self.d_zone_id = d_zone_id
        self.o_node_id = 0
        self.d_node_id = 0
        self.node_path = None
        self.link_path = None
        # Passenger Car Equivalent (PCE) of the agent
        self.PCE_factor = 1
        self.path_cost = 0
        # for simulation
        self.dep_time = 0
        # corresponding to each link along the link path
        self.link_dep_interval = None
        self.link_arr_interval = None
        self.curr_link_pos = 0

    def get_orig_node_id(self):
        return self.o_node_id

    def get_dest_node_id(self):
        return self.d_node_id

    def get_seq_no(self):
        return self.seq_no

    def get_id(self):
        return self.id

    def get_orig_zone_id(self):
        return self.o_zone_id

    def get_dest_zone_id(self):
        return self.d_zone_id

    def get_path_cost(self):
        return self.path_cost

    def get_node_path(self):
        return self.node_path

    def get_at_id(self):
        return self.at_id

    def get_dp_id(self):
        return self.dp_id

    def get_od(self):
        return self.o_zone_id, self.d_zone_id

    def update_dep_interval(self, intvl):
        self.link_dep_interval[self.curr_link_pos] = (
            self.link_arr_interval[self.curr_link_pos] + intvl
        )

    def get_curr_dep_interval(self):
        return self.link_dep_interval[self.curr_link_pos]

    def reached_last_link(self):
        return self.curr_link_pos == 0

    def get_next_link_no(self):
        pos = self.curr_link_pos - 1
        return self.link_path[pos]

    def set_dep_interval(self, i):
        self.link_dep_interval[self.curr_link_pos] = i

    def set_arr_interval(self, i, increment=0):
        self.link_arr_interval[self.curr_link_pos-increment] = i

    def get_arr_interval(self):
        return self.link_arr_interval[self.curr_link_pos]

    def increment_link_pos(self):
        if self.curr_link_pos > 0:
            self.curr_link_pos -= 1

    def get_dep_time(self):
        return self.dep_time

    def get_origin_dep_interval(self):
        return self.link_arr_interval[-1]


class Zone:

    def __init__(self, zone_id, bin_index=0):
        self.no = -1
        self.id = str(zone_id)
        self.bin_id = bin_index
        self.production = 0
        self.centroid = None
        self.boundaries = []
        self.coord_x = 91
        self.coord_y = 181
        self.nodes = []
        self.activity_nodes = []
        # for ODME
        self.prod_obs = 0
        self.attr_obs = 0
        self.attr_est = 0
        self.prod_est = 0
        self.prod_est_dev = 0
        self.attr_est_dev = 0
        self.is_prod_obs_upper_bounded = False
        self.is_attr_obs_upper_bounded = False

    def get_activity_nodes(self):
        return self.activity_nodes

    def get_activity_nodes_num(self):
        return len(self.activity_nodes)

    def get_bin_index(self):
        return self.bin_id

    def get_boundaries(self):
        return self.boundaries

    def get_centroid(self):
        return self.centroid

    def get_coordinate(self):
        return self.coord_x, self.coord_y

    def get_coordinate_str(self):
        if self.coord_x == 91 or self.coord_y == 181:
            return ''

        return str(self.coord_x) + ' ' + str(self.coord_y)

    def get_geo(self):
        """ output the four vertices as boundary """
        try:
            [U, D, L, R] = self.get_boundaries()
            geo = (
                'LINESTRING ('
                + str(L) + ' ' + str(U) + ','
                + str(R) + ' ' + str(U) + ','
                + str(R) + ' ' + str(D) + ','
                + str(L) + ' ' + str(D) + ','
                + str(L) + ' ' + str(U) + ')'
            )
        except ValueError:
            geo = 'LINESTRING ()'

        return geo

    def get_nodes(self):
        return self.nodes

    def get_production(self):
        return self.production

    def add_activity_node(self, node_id):
        self.activity_nodes.append(node_id)

    def add_node(self, node_id):
        self.nodes.append(node_id)

    def set_bin_index(self, bi):
        self.bin_id = bi

    def set_coord(self, cx, cy):
        self.coord_x = cx
        self.coord_y = cy

    def set_geo(self, U, D, L, R):
        self.boundaries = [U, D, L, R]

    def set_production(self, p):
        self.production = p


class Network:

    def __init__(self):
        self.nodes = []
        self.links = []
        self.agents = []
        # key: node id, value: node seq no
        self.map_id_to_no = {}
        # key: node seq no, value: node id
        self.map_no_to_id = {}
        # map link id to link seq no
        self.link_ids = {}
        self.node_label_cost = None
        self.node_preds = None
        self.link_preds = None
        self.capi_allocated = False
        self.agent_type_name = 'all'
        # key: zone id, value: zone object
        self.zones = {}
        self.activity_node_num = 0
        self.last_thru_node = 0
        self.centroids_added = False
        # key: simulation interval, value: agent id
        self.td_agents = {}
        self.len_unit_cf = 1
        self.len_unit = 'mi'

    def update(self):
        self.last_thru_node = self.get_node_size()
        self.activity_node_num = sum(
            z.get_activity_nodes_num() for z in self.zones.values()
        )

    def allocate_for_CAPI(self):
        # execute only on the first call
        if self.capi_allocated:
            return

        node_size = self.get_node_size()
        link_size = self.get_link_size()

        # initialization for predecessors and label costs
        node_preds = [-1] * node_size
        link_preds = [-1] * node_size
        node_label_cost = [MAX_LABEL_COST] * node_size

        # initialize from_node_no_array, to_node_no_array, and link_cost_array
        from_node_no_array = [link.from_node_no for link in self.links]
        to_node_no_array = [link.to_node_no for link in self.links]
        link_cost_array = [link.fftt for link in self.links]

        # initialize others
        queue_next = [0] * node_size
        first_link_from = [-1] * node_size
        last_link_from = [-1] * node_size
        sorted_link_no_array = [-1] * link_size

        # internal link index used for shortest path calculation only
        j = 0
        for i, node in enumerate(self.nodes):
            if not node.outgoing_links:
                continue
            first_link_from[i] = j
            for link in node.outgoing_links:
                # set up the mapping from j to the true link seq no
                sorted_link_no_array[j] = link.link_no
                j += 1
            last_link_from[i] = j

        # setup allowed uses
        allowed_uses = [link.allowed_uses for link in self.links]

        # set up arrays using ctypes
        int_arr_node = ctypes.c_int * node_size
        int_arr_link = ctypes.c_int * link_size
        double_arr_node = ctypes.c_double * node_size
        double_arr_link = ctypes.c_double * link_size
        # for allowed_uses
        char_arr_link = ctypes.c_wchar_p * link_size

        self.from_node_no_array = int_arr_link(*from_node_no_array)
        self.to_node_no_array = int_arr_link(*to_node_no_array)
        self.first_link_from = int_arr_node(*first_link_from)
        self.last_link_from = int_arr_node(*last_link_from)
        self.sorted_link_no_array = int_arr_link(*sorted_link_no_array)
        self.link_cost_array = double_arr_link(*link_cost_array)
        self.node_label_cost = double_arr_node(*node_label_cost)
        self.node_preds = int_arr_node(*node_preds)
        self.link_preds = int_arr_node(*link_preds)
        self.queue_next = int_arr_node(*queue_next)
        self.allowed_uses = char_arr_link(*allowed_uses)

        self.capi_allocated = True

    def init_link_costs(self, cost_type='time'):
        if cost_type == 'time':
            link_costs = [link.fftt for link in self.links]
        else:
            link_costs = [link.length for link in self.links]

        double_arr_link = ctypes.c_double * self.get_link_size()
        self.link_cost_array = double_arr_link(*link_costs)

    def add_centroids_connectors(self):
        if self.centroids_added:
            return

        node_no = self.get_node_size()
        link_no = self.get_link_size()
        # get zones
        for z in self.get_zones():
            if not z:
                continue

            # create a centroid
            node_id = 'c_' + z
            centroid = Node(node_no, node_id, z)
            # try coordinate of the centroid from each zone first. if the values
            # are invalid, then use that of the first node from each zone.
            coord_x, coord_y = self.zones[z].get_coordinate()
            if coord_x == 91 or coord_y == 181:
                node_id_ = self.get_nodes_from_zone(z)[0]
                node_no_ = self.get_node_no(node_id_)
                node = self.get_nodes()[node_no_]
                coord_x = node.coord_x
                coord_y = node.coord_y
                self.zones[z].set_coord(float(coord_x), float(coord_y))
            else:
                coord_x = str(coord_x)
                coord_y = str(coord_y)

            centroid.update_coordinate((coord_x, coord_y))
            self.zones[z].centroid = centroid

            self.nodes.append(centroid)
            self.map_id_to_no[node_id] = node_no
            self.map_no_to_id[node_no] = node_id

            # build connectors
            for i in self.get_nodes_from_zone(z):
                link_id_f = 'conn_' + str(link_no)
                from_node_no = node_no
                to_node_id = i

                try:
                    to_node_no = self.map_id_to_no[i]
                except KeyError:
                    continue

                # connector from centroid to activity nodes in this zone
                c_forward = Link(link_id_f,
                                 link_no,
                                 from_node_no,
                                 to_node_no,
                                 node_id,
                                 to_node_id,
                                 0)

                # connector from activity nodes in this zone to centroid
                link_id_b = 'conn_' + str(link_no+1)
                c_backward = Link(link_id_b,
                                  link_no+1,
                                  to_node_no,
                                  from_node_no,
                                  to_node_id,
                                  node_id,
                                  0)

                self.nodes[from_node_no].add_outgoing_link(c_forward)
                self.nodes[to_node_no].add_outgoing_link(c_backward)

                self.links.append(c_forward)
                self.links.append(c_backward)

                link_no += 2

            node_no += 1

        self.centroids_added = True

    def setup_agents(self, column_pool):
        agent_id = 1
        agent_no = 0

        for k, cv in column_pool.items():
            if cv.get_od_volume() <= 0:
                continue

            # k= (at, dp, orig, dest)
            at = k[0]
            dp = k[1]
            oz = k[2]
            dz = k[3]

            vol = int(cv.get_od_volume()+1)
            for _ in range(vol):
                # construct agent using valid record
                agent = Agent(agent_id,
                              agent_no,
                              at,
                              dp,
                              oz,
                              dz)

                # step 1 generate o_node_id and d_node_id randomly
                # according to o_zone_id and d_zone_id
                agent.o_node_id = choice(
                    self.zones[oz].get_nodes()
                )
                agent.d_node_id = choice(
                    self.zones[dz].get_nodes()
                )

                # step 2 update agent_id and agent_seq_no
                agent_id += 1
                agent_no += 1

                self.agents.append(agent)

        print(f'the number of agents is {len(self.agents)}')

    def _get_agent(self, agent_no):
        """ retrieve agent using agent_no """
        try:
            return self.agents[agent_no]
        except IndexError:
            agent_id = agent_no + 1
            print(f'Please provide a valid agent id. agent_id: {agent_id} does NOT EXIST!')

    def get_agent_node_path(self, agent_id, cost_type, path_only):
        """ return the sequence of node IDs along the agent path

        developer's note: consider changing its name to
        get_agent_node_path_str()
        """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        path_cost = agent.get_path_cost()
        if path_cost >= MAX_LABEL_COST:
            return f'path {cost_type}: infinity | path: '

        path = ''
        if agent.node_path:
            path = ';'.join(
                self.map_no_to_id[x] for x in reversed(agent.node_path)
            )

        if path_only:
            return path
        else:
            unit = 'minutes'
            if cost_type.startswith('dis'):
                unit = self.get_length_unit() + 's'

            return f'path {cost_type}: {path_cost:.4f} {unit} | node path: {path}'

    def get_agent_link_path(self, agent_id, cost_type, path_only):
        """ return the sequence of link IDs along the agent path

        developer's note: consider changing its name to
        get_agent_link_path_str()
        """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        path_cost = agent.get_path_cost()
        if path_cost >= MAX_LABEL_COST:
            return f'path {cost_type}: infinity | path: '

        path = ''
        if agent.link_path:
            path = ';'.join(
                self.links[x].get_link_id() for x in reversed(agent.link_path)
            )

        if path_only:
            return path
        else:
            unit = 'minutes'
            if cost_type.startswith('dis'):
                unit = self.get_length_unit() + 's'

            return f'path {cost_type}: {path_cost:.4f} {unit} | link path: {path}'

    def get_agent_orig_node_id(self, agent_id):
        """ return the origin node id of agent """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        return agent.get_orig_node_id()

    def get_agent_dest_node_id(self, agent_id):
        """ return the origin node id of agent """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        return agent.get_dest_node_id()

    def get_agent_count(self):
        return len(self.agents)

    def get_nodes_from_zone(self, zone_id):
        return self.zones[zone_id].get_nodes()

    def get_node_no(self, node_id):
        return self.map_id_to_no[node_id]

    def get_node_size(self):
        return len(self.nodes)

    def get_link_size(self):
        return len(self.links)

    def get_nodes(self):
        return self.nodes

    def get_links(self):
        return self.links

    def get_zones(self):
        # sorting is needed for setup_spnetwork()
        return sorted(self.zones.keys())

    def get_zone_size(self):
        return len(self.zone_)

    def get_from_node_no_arr(self):
        return self.from_node_no_array

    def get_to_node_no_arr(self):
        return self.to_node_no_array

    def get_first_links(self):
        return self.first_link_from

    def get_last_links(self):
        return self.last_link_from

    def get_sorted_link_no_arr(self):
        return self.sorted_link_no_array

    def get_node_preds(self):
        return self.node_preds

    def get_link_preds(self):
        return self.link_preds

    def get_node_label_costs(self):
        return self.node_label_cost

    def get_node_label_cost(self, node_no):
        return self.node_label_cost[node_no]

    def get_link_costs(self):
        return self.link_cost_array

    def get_queue_next(self):
        return self.queue_next

    def get_allowed_uses(self):
        return self.allowed_uses

    def get_link(self, seq_no):
        return self.links[seq_no]

    def get_node(self, node_id):
        return self.nodes[self.get_node_no(node_id)]

    def get_agent_type_name(self):
        """ for allowed uses in single_source_shortest_path() """
        return self.agent_type_name

    def get_link_no(self, id):
        return self.link_ids[id]

    def get_agents(self):
        return self.agents

    def get_last_thru_node(self):
        """ node no of the first potential centroid """
        return self.last_thru_node

    def set_agent_type_name(self, at_name):
        self.agent_type_name = at_name

    def get_centroids(self):
        for k, v in self.zones.items():
            if not k:
                continue

            yield v.get_centroid()

    def get_length_unit(self):
        return self.len_unit

    def get_path_cost(self, to_node_id, cost_type='time'):
        to_node_no = self.map_id_to_no[to_node_id]
        if cost_type == 'time':
            return self.node_label_cost[to_node_no]

        return self.node_label_cost[to_node_no] * self.len_unit_cf

    def have_dep_agents(self, i):
        return i in self.td_agents

    def get_td_agents(self, i):
        return self.td_agents[i]


class Column:
    """ column is path """
    def __init__(self, id=-1):
        self.id = id
        self.vol = 0
        self.dist = 0
        self.toll = 0
        self.travel_time = 0
        self.gradient_cost = 0
        self.gradient_cost_abs_diff = 0
        self.gradient_cost_rel_diff = 0
        self.nodes = None
        self.links = None
        self.geo = ''

    def get_link_num(self):
        return len(self.links)

    def get_node_num(self):
        return len(self.nodes)

    def get_id(self):
        return self.id

    def get_distance(self):
        return self.dist

    def get_volume(self):
        return self.vol

    def get_toll(self):
        return self.toll

    def get_travel_time(self):
        return self.travel_time

    def get_gradient_cost(self):
        return self.gradient_cost

    def get_gradient_cost_abs_diff(self):
        return self.gradient_cost_abs_diff

    def get_gradient_cost_rel_diff(self):
        return self.gradient_cost_rel_diff

    def get_links(self):
        """ return link path """
        return self.links

    def get_nodes(self):
        """ return node path """
        return self.nodes

    def set_distance(self, d):
        self.dist = d

    def set_volume(self, v):
        self.vol = v

    def set_toll(self, t):
        self.toll = t

    def set_travel_time(self, tt):
        self.travel_time = tt

    def set_gradient_cost(self, c):
        self.gradient_cost = c

    def increase_volume(self, v):
        self.vol += v

    def set_geometry(self, g):
        self.geo = g

    def update_gradient_cost_diffs(self, least_gc):
        self.gradient_cost_abs_diff = self.gradient_cost - least_gc
        self.gradient_cost_rel_diff = (
            self.gradient_cost_abs_diff / max(EPSILON, least_gc)
        )

    def get_gap(self):
        return self.gradient_cost_abs_diff * self.vol

    def get_sys_travel_time(self):
        return self.gradient_cost * self.vol

    def reset(self):
        self.id = -1
        self.nodes = self.links = None
        self.travel_time = self.gradient_cost = 0
        self.gradient_cost_abs_diff = self.gradient_cost_rel_diff = 0

    def set_id(self, id):
        self.id = id


class ColumnVec:
    """ column pool for (at, dp, oz, dz)

    where, at is agent type id,
           dp is demand period id,
           oz is origin zone id,
           dz is destination zone id.
    """
    def __init__(self):
        self.od_vol = 0
        self.route_fixed = False
        self.node_seq_paths = []

    def is_route_fixed(self):
        return self.route_fixed

    def get_od_volume(self):
        return self.od_vol

    def get_column_num(self):
        return len(self.node_seq_paths)

    def get_columns(self):
        return self.node_seq_paths

    def get_column(self, k):
        return self.node_seq_paths[k]

    def add_new_column(self, col):
        self.node_seq_paths.append(col)

    def set_volume(self, vol):
        self.od_vol = vol

    def increase_volume(self, vol):
        self.od_vol += vol


class AgentType:

    def __init__(self, id=0, type='a', name='auto',
                 vot=10, flow_type=0, pce=1, ffs=60, use_link_ffs=True):
        """ default constructor """
        self.id = id
        self.type = type
        self.name = name
        self.vot = vot
        self.flow_type = flow_type
        self.pce = pce
        self.ffs = ffs
        self.use_link_ffs = use_link_ffs

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_vot(self):
        return self.vot

    def get_type_str(self):
        return self.type

    def get_pce(self):
        return self.pce

    def get_free_flow_speed(self):
        return self.ffs

    @staticmethod
    def get_default_type_str():
        return 'a'

    @staticmethod
    def get_default_name():
        return 'auto'

    @staticmethod
    def get_legacy_type_str():
        return 'p'

    @staticmethod
    def get_legacy_name():
        return 'passenger'


class SpecialEvent:

    def __init__(self, name) -> None:
        self.name = name
        self.affected_links = {}

    def get_affected_links(self):
        return self.affected_links.items()


class DemandPeriod:

    def __init__(self, id=0, period='AM', time_period='0700-0800'):
        self.id = id
        self.period = period
        self.time_period = time_period
        self.special_event = None
        self._setup_time()

    def _parse_time_period(self, delim='-'):
        s1, s2 = self.time_period.split(delim)
        t1 = datetime.strptime(s1, '%H%M')
        t2 = datetime.strptime(s2, '%H%M')
        if t2 <= t1:
            raise ValueError('ending time <= starting time')

        st_ = t1.hour * 60 + t1.minute
        et_ = t2.hour * 60 + t2.minute

        return st_, et_

    def _setup_time(self):
        try:
            st_, et_ = self._parse_time_period()
        except ValueError:
            # backward compatibility for versions <= v0.9.3
            st_, et_ = self._parse_time_period('_')
        except Exception as e:
            raise e

        self.st = st_
        self.et = et_

    def get_id(self):
        return self.id

    def get_period(self):
        return self.period

    def get_duration(self):
        """ duration of demand period in minutes """
        return self.et - self.st

    def get_start_time(self):
        return self.st


class Demand:

    def __init__(self, id=0, period='AM', agent_type='a', file='demand.csv'):
        self.id = id
        self.period = period
        self.agent_type_str = agent_type
        self.file = file

    def get_id(self):
        return self.id

    def get_file_name(self):
        return self.file

    def get_period(self):
        return self.period

    def get_agent_type_str(self):
        return self.agent_type_str


class VDFPeriod:

    def __init__(self, id, alpha=0.15, beta=4, mu=1000,
                 fftt=0, cap=99999, phf=-1):
        """ default constructor """
        self.id = id
        # the following four have been defined in class Link
        # they should be exactly the same with those in the corresponding link
        self.alpha = alpha
        self.beta = beta
        self.mu = mu
        # free flow travel time
        self.fftt = fftt
        self.capacity = cap
        self.phf = phf
        self.avg_travel_time = 0
        self.voc = 0
        self.capacity_ratio = 1

    def get_avg_travel_time(self):
        return self.avg_travel_time

    def get_voc(self):
        return self.voc

    def get_fftt(self):
        return self.fftt

    def run_bpr(self, vol):
        vol = max(0, vol)
        self.voc = vol / max(EPSILON, self.capacity * self.capacity_ratio)
        self.avg_travel_time = (
            self.fftt
            + self.fftt
            * self.alpha
            * pow(self.voc, self.beta)
        )

        return self.avg_travel_time


class SPNetwork(Network):
    """ attributes related to outputs from shortest path calculations """
    def __init__(self, base, at, dp):
        self.base = base
        self.nodes = self.base.get_nodes()
        self.links = self.base.get_links()
        # AgentType object
        self.agent_type = at
        # DemandPeriod object
        self.demand_period = dp
        # zone sequence no
        self.orig_zones = []
        self.capi_allocated = False
        super().allocate_for_CAPI()

    def allocate_for_CAPI(self):
        pass

    def get_agent_type(self):
        return self.agent_type

    def get_agent_type_name(self):
        # convert it to C char
        return self.agent_type.get_name()

    def get_demand_period(self):
        return self.demand_period

    def get_node_no(self, node_id):
        return self.base.get_node_no(node_id)

    def get_node_size(self):
        return super().get_node_size()

    def get_link_size(self):
        return super().get_link_size()

    def get_nodes(self):
        return super().get_nodes()

    def get_links(self):
        return super().get_links()

    def get_zones(self):
        return super().get_zones()

    def get_from_node_no_arr(self):
        return super().get_from_node_no_arr()

    def get_to_node_no_arr(self):
        return super().get_to_node_no_arr()

    def get_first_links(self):
        return super().get_first_links()

    def get_last_links(self):
        return super().get_last_links()

    def get_sorted_link_no_arr(self):
        return super().get_sorted_link_no_arr()

    def get_allowed_uses(self):
        return super().get_allowed_uses()

    def get_node_preds(self):
        return super().get_node_preds()

    def get_link_preds(self):
        return super().get_link_preds()

    def get_node_label_costs(self):
        return super().get_node_label_costs()

    def get_link_costs(self):
        return super().get_link_costs()

    def get_queue_next(self):
        return super().get_queue_next()

    # the following three are shared by all SPNetworks as the underlying
    # network topology
    def get_last_thru_node(self):
        """ node no of the first potential centroid """
        return self.base.get_last_thru_node()

    def get_orig_centroids(self):
        for z in self.orig_zones:
            yield self.base.zones[z].get_centroid()

    def get_centroids(self):
        return self.base.get_centroids()


class AccessNetwork(Network):
    """ network for accessibility evaluation """
    def __init__(self, base, add_cc=True):
        self.base = base
        self.nodes = self.base.get_nodes()
        self.links = self.base.get_links()
        # it will be used by add_centroids_connectors()
        self.zones = self.base.zones
        self.map_id_to_no = self.base.map_id_to_no
        self.map_no_to_id = self.base.map_no_to_id
        self.centroids_added = self.base.centroids_added
        self.agent_type_name = 'all'
        self.pre_source_node_id = ''
        if add_cc:
            self._add_centroids_connectors()
        self.capi_allocated = False
        super().allocate_for_CAPI()

    def _add_centroids_connectors(self):
        if self.centroids_added:
            return

        # deep copy
        self.nodes = deepcopy(self.nodes)
        self.links = deepcopy(self.links)
        self.map_id_to_no = deepcopy(self.map_id_to_no)
        self.map_no_to_id = deepcopy(self.map_no_to_id)

        super().add_centroids_connectors()

    def get_zones(self):
        return super().get_zones()

    def get_nodes_from_zone(self, zone_id):
        return self.base.get_nodes_from_zone(zone_id)

    def _get_zone_coord(self, zone_id):
        """ coordinate of each zone is from its first node """
        node_id = self.get_nodes_from_zone(zone_id)[0]
        node = self.get_node(node_id)
        return node.coord_x, node.coord_y

    def set_target_mode(self, mode):
        """ set up the target mode for accessibility evaluation

        Parameters
        ----------
        mode : agent name which is in settings.yml.
        """
        self.agent_type_name = mode

    def set_source_node_id(self, node_id):
        self.pre_source_node_id = node_id

    def get_agent_type_name(self):
        return self.agent_type_name

    def get_centroids(self):
        return super().get_centroids()

    def get_node(self, node_id):
        return super().get_node(node_id)

    def get_node_no(self, node_id):
        return super().get_node_no(node_id)

    def get_node_size(self):
        return super().get_node_size()

    def get_link_size(self):
        return super().get_link_size()

    def get_from_node_no_arr(self):
        return super().get_from_node_no_arr()

    def get_to_node_no_arr(self):
        return super().get_to_node_no_arr()

    def get_first_links(self):
        return super().get_first_links()

    def get_last_links(self):
        return super().get_last_links()

    def get_sorted_link_no_arr(self):
        return super().get_sorted_link_no_arr()

    def get_node_preds(self):
        return super().get_node_preds()

    def get_link_preds(self):
        return super().get_link_preds()

    def get_node_label_costs(self):
        return super().get_node_label_costs()

    def get_node_label_cost(self, node_no):
        return super().get_node_label_cost(node_no)

    def get_link_costs(self):
        return super().get_link_costs()

    def get_queue_next(self):
        return super().get_queue_next()

    def get_allowed_uses(self):
        return super().get_allowed_uses()

    def get_last_thru_node(self):
        """ node no of the first centroid """
        return self.base.get_last_thru_node()

    def get_pred_link_id(self, node_id):
        """ return id of the predecessor link to node_id """
        link_no = self.link_preds[self.get_node_no(node_id)]
        return self.links[link_no].get_link_id()

    def get_sp_distance(self, node_no):
        """ get the shortest path distance """
        if self.link_preds[node_no] == -1:
            return MAX_LABEL_COST

        dist = 0
        while node_no >= 0:
            link_no = self.link_preds[node_no]
            if link_no >= 0:
                dist += self.get_link(link_no).get_length()

            node_no = self.node_preds[node_no]

        return dist

    def update_generalized_link_cost(self, at, time_dependent, demand_period_id):
        """ update generalized link costs to calculate accessibility """
        vot = at.get_vot()

        if time_dependent:
            for link in self.get_links():
                # do not update connectors
                if link.get_link_id().startswith('conn_'):
                    continue

                self.link_cost_array[link.get_seq_no()] = (
                    link.get_period_fftt(demand_period_id)
                    + link.get_route_choice_cost()
                    + link.get_toll() / max(EPSILON, vot) * 60
                )
        else:
            if not at.use_link_ffs:
                ffs = at.get_free_flow_speed()

                for link in self.get_links():
                    self.link_cost_array[link.get_seq_no()] = (
                        (link.get_length() / max(EPSILON, ffs) * 60)
                        + link.get_route_choice_cost()
                        + link.get_toll() / max(EPSILON, vot) * 60
                    )
            else:
                for link in self.get_links():
                    self.link_cost_array[link.get_seq_no()] = (
                        link.get_free_flow_travel_time()
                        + link.get_route_choice_cost()
                        + link.get_toll() / max(EPSILON, vot) * 60
                    )


class Assignment:

    def __init__(self):
        self.agent_types = []
        self.demand_periods = []
        self.demands = []
        # 4-d array
        self.column_pool = {}
        # base physical network
        self.network = None
        # SPNetwork instance for computing shortest paths only
        self.spnet = None
        self.spnetworks = []
        self.accessnetwork = None
        self.map_atstr_id = {}
        self.map_dpstr_id = {}
        self.map_name_atstr = {}
        # number of seconds per simulation interval
        self.simu_rez = 6
        # duration of simulation in minutes
        self.simu_dur = 60
        # simulation start time in minutes
        self.simu_st = 0
        self.has_created_spnet = False

    def update_agent_types(self, at):
        if at.get_type_str() not in self.map_atstr_id:
            self.map_atstr_id[at.get_type_str()] = at.get_id()
        else:
            raise Exception(f'agent type is not unique: {at.get_type_str()}')

        if at.get_name() not in self.map_name_atstr:
            self.map_name_atstr[at.get_name()] = at.get_type_str()
        else:
            raise Exception(f'agent type name is not unique: {at.get_name()}')

        self.agent_types.append(at)

    def update_demand_periods(self, dp):
        if dp.get_period() not in self.map_dpstr_id:
            self.map_dpstr_id[dp.get_period()] = dp.get_id()
        else:
            raise Exception(f'demand period is not unique: {dp.get_period()}')

        self.demand_periods.append(dp)

    def get_agent_type_id(self, at_str):
        try:
            return self.map_atstr_id[at_str]
        except KeyError:
            raise Exception(f'NO agent type: {at_str}')

    def get_demand_period_id(self, dp_str):
        try:
            return self.map_dpstr_id[dp_str]
        except KeyError:
            raise Exception(f'NO demand period: {dp_str}')

    def get_agent_type(self, at_str):
        return self.agent_types[self.get_agent_type_id(at_str)]

    def get_demand_period(self, dp_str):
        return self.demand_periods[self.get_demand_period_id(dp_str)]

    def get_agent_type_str(self, at_id):
        try:
            return self.agent_types[at_id].get_type_str()
        except KeyError:
            raise Exception(f'NO agent type id: {at_id}')

    def get_demand_period_str(self, dp_id):
        try:
            return self.demand_periods[dp_id].get_period()
        except KeyError:
            raise Exception(f'NO demand period id: {dp_id}')

    def update_demands(self, d):
        self.demands.append(d)

    def get_agent_type_count(self):
        return len(self.agent_types)

    def get_demand_period_count(self):
        return len(self.demand_periods)

    def get_agent_types(self):
        return self.agent_types

    def get_demand_periods(self):
        return self.demand_periods

    def get_demands(self):
        return self.demands

    def get_spnetworks(self):
        for sp in self.spnetworks:
            yield sp

    def get_network(self):
        return self.network

    def get_nodes(self):
        """ return list of node objects """
        return self.network.get_nodes()

    def get_links(self):
        """ return list of link objects """
        return self.network.get_links()

    def get_zones(self):
        """ return list of zone IDs """
        return self.network.get_zones()

    def get_column_pool(self):
        return self.column_pool

    def get_column_vec(self, at, dp, orig_zone_id, dest_zone_id):
        return self.column_pool[(at, dp, orig_zone_id, dest_zone_id)]

    def get_agent_orig_node_id(self, agent_id):
        """ return the origin node id of an agent

        exception will be handled by _get_agent() in class Network
        """
        return self.network.get_agent_orig_node_id(agent_id)

    def get_agent_dest_node_id(self, agent_id):
        """ return the destination node id of an agent

        exception will be handled by _get_agent() in class Network
        """
        return self.network.get_agent_dest_node_id(agent_id)

    def get_agent_node_path(self, agent_id, cost_type='time', path_only=True):
        """ return the sequence of node IDs along the agent path

        exception will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_node_path(agent_id, cost_type, path_only)

    def get_agent_link_path(self, agent_id, cost_type='time', path_only=True):
        """ return the sequence of link IDs along the agent path

        exception will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_link_path(agent_id, cost_type, path_only)

    def _convert_mode(self, mode):
        """convert mode to the corresponding agent type name and string"""
        if mode in self.map_atstr_id:
            at = self.get_agent_type(mode)
            return at.get_name(), mode

        if mode in self.map_name_atstr:
            return mode, self.map_name_atstr[mode]

        # for distance-based shortest path calculation only
        # it shall not be used with any accessibility evaluations
        if mode.startswith('all'):
            return mode, mode

        raise Exception(f'{mode} is not existing in settings.yml! Please provide a valid mode!')

    def find_path_for_agents(self, mode, cost_type):
        """ find and set up shortest path for each agent """
        # reset agent type str or mode according to user's input
        at_name, _ = self._convert_mode(mode)
        self.network.set_agent_type_name(at_name)

        find_path_for_agents(self.network, self.column_pool, cost_type)

    def find_shortest_path(self, from_node_id, to_node_id, mode, seq_type, cost_type):
        """ call find_shortest_path() from path.py

        exceptions will be handled in find_shortest_path()
        """
        # reset agent type str or mode according to user's input
        at_name, _ = self._convert_mode(mode)
        self.network.set_agent_type_name(at_name)

        # add backward compatibility in case the user still use integer node id's
        from_node_id = str(from_node_id)
        to_node_id = str(to_node_id)

        return find_shortest_path(self.network, from_node_id,
                                  to_node_id, seq_type, cost_type)

    def get_shortest_path_tree(self, from_node_id, mode, seq_type, cost_type):
        # reset agent type str or mode according to user's input
        at_name, _ = self._convert_mode(mode)
        self.network.set_agent_type_name(at_name)

        is_int = isinstance(from_node_id, int)
        # add backward compatibility in case the user still use integer node id's
        from_node_id = str(from_node_id)

        return get_shortest_path_tree(self.network, from_node_id,
                                      seq_type, cost_type, is_int)

    def benchmark_apsp(self):
        benchmark_apsp(self.network)

    def _has_outgoing_links(self, zone_id):
        return self.network.zones[zone_id].get_centroid().has_outgoing_links()

    def setup_spnetwork(self, demand_directive=False):
        if self.has_created_spnet:
            return

        self.network.add_centroids_connectors()

        spvec = {}
        partial_keys = {}
        if demand_directive:
            partial_keys = {k[:3]: None for k in self.column_pool}

        # z is zone id
        for z in self.get_zones():
            if not z or not self._has_outgoing_links(z):
                continue

            for d in self.demands:
                at = self.get_agent_type(d.get_agent_type_str())
                dp = self.get_demand_period(d.get_period())
                pk = (at.get_id(), dp.get_id(), z)

                if demand_directive and pk not in partial_keys:
                    continue

                k = pk[:2]
                if k not in spvec:
                    sp = SPNetwork(self.network, at, dp)
                    spvec[k] = sp
                    sp.orig_zones.append(z)
                    self.spnetworks.append(sp)
                else:
                    sp = spvec[k]
                    sp.orig_zones.append(z)

        self.has_created_spnet = True

    def get_link(self, seq_no):
        """ return link object corresponding to link seq no """
        return self.network.get_link(seq_no)

    def get_link_no(self, id):
        """ id is string """
        return self.network.get_link_no(id)

    def get_node_no(self, id):
        """ id is integer """
        return self.network.get_node_no(id)

    def get_agents(self):
        return self.network.get_agents()

    def get_node_label_cost(self, node_no):
        return self.accessnetwork.get_node_label_cost(node_no)

    def get_accessible_nodes(self, source_node_id, time_budget,
                             mode, time_dependent, tau):
        source_node_id = str(source_node_id)
        if source_node_id not in self.network.map_id_to_no:
            raise Exception(f'Node ID: {source_node_id} not in the network')

        assert(time_budget>=0)

        if time_budget == 0:
            return []

        if not self.accessnetwork:
            self.accessnetwork = AccessNetwork(self.network, False)

        # simple caching to avoid duplicate shortest path calculation
        run_sp = False
        if self.accessnetwork.pre_source_node_id != source_node_id:
            self.accessnetwork.set_source_node_id(source_node_id)
            run_sp = True

        at_name, at_str = self._convert_mode(mode)
        if self.accessnetwork.agent_type_name != at_name:
            self.accessnetwork.set_target_mode(at_name)
            at = self.get_agent_type(at_str)
            self.accessnetwork.update_generalized_link_cost(at,
                                                            time_dependent,
                                                            tau)
            run_sp = True

        if run_sp:
            single_source_shortest_path(self.accessnetwork, source_node_id)

        # if max min travel time is less than or equal to time_budget,
        # output the entire node set directly without the following check?
        nodes = []
        for node in self.accessnetwork.get_nodes():
            # do not include the source node itself
            if node.get_node_id() == source_node_id:
                continue

            node_no = node.get_node_no()
            if self.accessnetwork.get_node_label_cost(node_no) <= time_budget:
                nodes.append(node.get_node_id())

        return nodes

    def get_accessible_links(self, source_node_id, time_budget,
                             mode, time_dependent, tau):
        # node id's
        nodes = self.get_accessible_nodes(source_node_id, time_budget,
                                          mode, time_dependent, tau)
        # convert to link id's
        return [self.accessnetwork.get_pred_link_id(x) for x in nodes]

    def get_total_simu_intervals(self):
        return ceil(self.simu_dur * 60 / self.simu_rez)

    def have_dep_agents(self, i):
        return self.network.have_dep_agents(i)

    def get_td_agents(self, i):
        return self.network.get_td_agents(i)

    def get_simu_duration(self):
        return self.simu_dur

    def get_simu_start_time(self):
        return self.simu_st

    def initialize_simulation(self, loading_profile):
        profiles = ['constant', 'random', 'uniform']
        if loading_profile not in profiles:
            Warning.warn(
                f'{loading_profile} is not supported!'
                ' constant loading profile will be adopted.'
            )

        agent_id = 1
        links = self.get_links()
        column_pool = self.get_column_pool()

        for k, cv in column_pool.items():
            if cv.get_od_volume() <= 0:
                continue

            # k= (at, dp, orig, dest)
            at = k[0]
            dp = k[1]
            oz = k[2]
            dz = k[3]

            for col in cv.get_columns():
                if col.nodes is None:
                    continue

                # link volume is already set up in UE
                vol = ceil(col.get_volume())
                for j in range(vol):
                    agent = Agent(agent_id, agent_id - 1, at, dp, oz, dz)

                    n = col.get_link_num()
                    agent.curr_link_pos = n - 1
                    agent.link_arr_interval = [-1] * n
                    agent.link_dep_interval = [-1] * n

                    # constant departure time by default
                    t = self.simu_st
                    if loading_profile.startswith('uniform'):
                        t += int(j / col.get_volume() * self.simu_dur)
                    elif loading_profile.startswith('random'):
                        t += randint(0, self.simu_dur - 1)

                    # simulation interval
                    i = self.cast_minute_to_interval(t - self.simu_st)
                    agent.link_arr_interval[-1] = i
                    agent.dep_time = t

                    # set up node path and link path
                    agent.link_path = [x for x in col.links]
                    agent.node_path = [x for x in col.nodes]
                    agent.path_cost = col.get_distance()
                    if i not in self.network.td_agents:
                        self.network.td_agents[i] = []
                    self.network.td_agents[i].append(agent.get_seq_no())
                    self.network.agents.append(agent)

                    agent_id += 1

        # replicate _update_link_travel_time_and_cost()
        for link in links:
            if link.length == 0:
                continue

            # link_capacity is for one hour, i.e., 3600 s
            cap = ceil(link.link_capacity / SECONDS_IN_HOUR * self.simu_rez)
            n1 = self.get_total_simu_intervals()
            n2 = self.get_simu_duration()

            link.outflow_cap = [cap] * n1
            link.cum_arr = [0] * n1
            link.cum_dep = [0] * n1
            # waiting time in terms of simulation interval
            link.waiting_time = [0] * n2

    def get_simu_resolution(self):
        return self.simu_rez

    def get_agent(self, agent_no):
        return self.network._get_agent(agent_no)

    def set_simu_resolution(self, res):
        self.simu_rez = res

    def set_simu_duration(self, dur):
        self.simu_dur = dur

    def set_simu_start_time(self, st):
        self.simu_st = st

    def set_capacity_ratio(self, tau, link_id, r):
        try:
            link_no = self.get_link_no(link_id)
        except KeyError:
            return

        link = self.get_link(link_no)
        link.set_capacity_ratio(tau, r)

    def cast_interval_to_minute(self, i):
        return floor(i * self.simu_rez / SECONDS_IN_MINUTE)

    def cast_interval_to_minute_float(self, i):
        return i * self.simu_rez / SECONDS_IN_MINUTE

    def cast_minute_to_interval(self, m):
        return floor(m * SECONDS_IN_MINUTE / self.simu_rez)


class UI:
    """ an abstract class only with user interfaces """
    def __init__(self, assignment):
        self._base_assignment = assignment
        self._agent_cost_type = 'time'

    def get_column_pool(self):
        return self._base_assignment.get_column_pool()

    def get_column_vec(self, at, dp, orig_zone_id, dest_zone_id):
        """ get all columns between two zones given agent type and demand period

        caller is responsible for checking if
        (at, dp, orig_zone_id, dest_zone_id) is in column pool
        """
        self._base_assignment.get_column_vec(at, dp, orig_zone_id, dest_zone_id)

    def get_agent_orig_node_id(self, agent_id):
        """ return the origin node id of an agent """
        return self._base_assignment.get_agent_orig_node_id(agent_id)

    def get_agent_dest_node_id(self, agent_id):
        """ return the destination node id of an agent """
        return self._base_assignment.get_agent_dest_node_id(agent_id)

    def get_agent_node_path(self, agent_id):
        """ return the sequence of node IDs along the agent path """
        return self._base_assignment.get_agent_node_path(agent_id, self._agent_cost_type)

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path """
        return self._base_assignment.get_agent_link_path(agent_id, self._agent_cost_type)

    def get_agent_num(self):
        return self._base_assignment.network.get_agent_count()

    def get_shortest_path_tree(self, from_node_id,
                               mode='all', seq_type='node', cost_type='time'):
        """ return the shorest path tree from the source node (from_node_id)

        Parameters
        ----------
        from_node_id
            the source (root) node id

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.

            The default is 'all', which means that links are open to all modes.

        seq_type
            'node' or 'link'. You will get the shortest path in sequence of
            either node IDs or link IDs. The default is 'node'.

        cost_type
            'time' or 'distance'. find the shortest path according travel time
            or travel distance.

        Returns
        -------
        dictionary
            shortest paths from the source node to any other nodes (the
            source node itself is excluded).

            key is to_node_id and value is the corresponding shortest path
            information including path cost and path details (as a tuple).

            path cost and path details are in line with the specified
            cost_type and seq_type.
        """

        return self._base_assignment.get_shortest_path_tree(
            from_node_id, mode, seq_type, cost_type
        )

    def find_path_for_agents(self, mode='all', cost_type='time'):
        """ DEPRECATED

        find and set up shortest path for each agent

        Parameters
        ----------
        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.

            The default is 'all', which means that links are open to all modes.

        cost_type
            'time' or 'distance'. find the shortest path according travel time
            or travel distance.

        Returns
        -------
        None
        """
        self._agent_cost_type = cost_type
        return self._base_assignment.find_path_for_agents(mode, cost_type)

    def find_shortest_path(self, from_node_id, to_node_id,
                           mode='all', seq_type='node', cost_type='time'):
        """ return shortest path between from_node_id and to_node_id

        Parameters
        ----------
        from_node_id
            the starting node id

        to_node_id
            the ending node id

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.

            The default is 'all', which means that links are open to all modes.

        seq_type
            'node' or 'link'. You will get the shortest path in sequence of
            either node IDs or link IDs. The default is 'node'.

        cost_type
            'time' or 'distance'. find the shortest path according travel time
            or travel distance.

        Returns
        -------
        str
            the shortest path between from_node_id and to_node_id.

        Note
        ----
            Exceptions will be thrown if either of from_node_id and and to_node_id
            is not valid node IDs.
        """
        return self._base_assignment.find_shortest_path(
            from_node_id,
            to_node_id,
            mode,
            seq_type,
            cost_type
        )

    def get_accessible_nodes(self,
                             source_node_id,
                             time_budget,
                             mode='auto',
                             time_dependent=False,
                             demand_period_id=0):
        """ get the accessible nodes from a node given mode and time budget

        Parameters
        ----------
        source_node_id
            the starting node id for evaluation, which shall be string

        time_budget
            the amount of time to travel in minutes

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs. Its default value is 'a' (i.e., mode auto).

            The default is 'auto'.

        time_dependent
            True or False. Its default value is False.

            If True, the accessibility will be evaluated using the period link
            free-flow travel time (i.e., VDF_fftt). In other words, the
            accessibility is time-dependent.

            If False, the accessibility will be evaluated using the link length
            and the free flow travel speed of each mode.

        demand_period_id
            The sequence number of demand period listed in demand_periods in
            settings.yml. demand_period_id of the first demand_period is 0.

            Use it with time_dependent when there are multiple demand periods.
            Its default value is 0.

        Returns
        -------
        int
            the number of nodes that can be accessible from source_node_id
            given time_budget and mode, and the node list
        """
        nodes = self._base_assignment.get_accessible_nodes(source_node_id,
                                                           time_budget,
                                                           mode,
                                                           time_dependent,
                                                           demand_period_id)

        node_strs = ';'.join(str(x) for x in nodes)

        print(f'number of accessible nodes is {len(nodes)}')
        print(f'accessible nodes are: {node_strs}')

    def get_accessible_links(self,
                             source_node_id,
                             time_budget,
                             mode='auto',
                             time_dependent=False,
                             demand_period_id=0):
        """ get the accessible links from a node given mode and time budget

        Parameters
        ----------
        source_node_id
            the starting node id for evaluation, which shall be string

        time_budget
            the amount of time to travel in minutes

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.

            The default is 'auto'.

        time_dependent
            True or False. Its default value is False.

            If True, the accessibility will be evaluated using the period link
            free-flow travel time (i.e., VDF_fftt). In other words, the
            accessibility is time-dependent.

            If False, the accessibility will be evaluated using the link length
            and the free flow travel speed of each mode.

        demand_period_id
            The sequence number of demand period listed in demand_periods in
            settings.yml. demand_period_id of the first demand_period is 0.

            Use it with time_dependent when there are multiple demand periods.
            Its default value is 0.

        Returns
        -------
        int
            the number of links that can be accessible from source_node_id
            given time_budget and mode, and the link list
        """
        links = self._base_assignment.get_accessible_links(source_node_id,
                                                           time_budget,
                                                           mode,
                                                           time_dependent,
                                                           demand_period_id)

        link_strs = ';'.join(str(x) for x in links)

        print(f'number of accessible links is {len(links)}')
        print(f'accessible links are: {link_strs}')

    def get_demand_period_str(self, demand_period_id):
        """ return the demand period name given its id

        Parameters
        ----------
        demand_period_id
            The sequence number of demand period listed in demand_periods in
            settings.yml. demand_period_id of the first demand_period is 0.

            Use it with time_dependent when there are multiple demand periods.
            Its default value is 0.

        Returns
        -------
        str
            The name of the corresponding demand period given demand_period_id (
            e.g., 'AM').
        """
        self._base_assignment.get_demand_period_str(demand_period_id)

    def benchmark_apsp(self):
        self._base_assignment.benchmark_apsp()