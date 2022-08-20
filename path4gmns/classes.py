import ctypes
from copy import deepcopy
from random import choice

from .consts import MAX_LABEL_COST, SMALL_DIVISOR
from .path import find_path_for_agents, find_shortest_path, \
                  single_source_shortest_path


__all__ = ['UI']


class Node:

    def __init__(self, node_seq_no, node_id, zone_id, x='', y='', b=False):
        """ the attributes of node  """
        # node_seq_no: internal node index used for calculation
        self.node_seq_no = node_seq_no
        # node_id: user defined node id from input
        self.node_id = node_id
        # link objects
        self.outgoing_links = []
        self.incoming_links = []
        self.zone_id = zone_id
        self.coord_x = x
        self.coord_y = y
        self.is_activity_node = b

    def has_outgoing_links(self):
        return len(self.outgoing_links) > 0

    def has_incoming_links(self):
        return len(self.incoming_links) > 0

    def get_zone_id(self):
        return self.zone_id

    def get_node_id(self):
        return self.node_id

    def get_node_no(self):
        return self.node_seq_no

    def get_coordinate(self):
        return self.coord_x + ' ' + self.coord_y

    def add_outgoing_link(self, link):
        self.outgoing_links.append(link)

    def add_incoming_link(self, link):
        self.incoming_links.append(link)

    def update_coordinate(self, args):
        self.coord_x = args[0]
        self.coord_y = args[1]


class Link:

    def __init__(self,
                 id,
                 link_seq_no,
                 from_node_no,
                 to_node_no,
                 from_node_id,
                 to_node_id,
                 length,
                 lanes=1,
                 link_type=1,
                 free_speed=60,
                 capacity=49500,
                 allowed_uses='all',
                 geometry='',
                 agent_type_size=1,
                 demand_period_size=1):
        """ the attributes of link """
        self.id = id
        self.link_seq_no = link_seq_no
        self.from_node_seq_no = from_node_no
        self.to_node_seq_no = to_node_no
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        # length is mile or km
        self.length = length
        self.lanes = lanes
        # 1: one direction, 2: two way
        self.type = link_type
        # free_speed: mile/h or km/h
        self.free_flow_travel_time_in_min = (
            length / max(SMALL_DIVISOR, free_speed) * 60
        )
        # capacity is lane capacity per hour
        self.link_capacity = capacity * lanes
        self.allowed_uses = allowed_uses
        self.geometry = geometry
        self.cost = self.free_flow_travel_time_in_min
        self.flow_volume = 0
        # add for CG
        self.agent_type_size = agent_type_size
        self.demand_period_size = demand_period_size
        self.toll = 0
        self.route_choice_cost = 0
        self.travel_time_by_period = [0] * demand_period_size
        self.flow_vol_by_period = [0] * demand_period_size
        self.vdfperiods = []

    def get_link_id(self):
        return self.id

    def get_seq_no(self):
        return self.link_seq_no

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
        return self.free_flow_travel_time_in_min

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
            + self.toll / max(SMALL_DIVISOR, value_of_time) * 60
        )

    def reset_period_flow_vol(self, tau):
        self.flow_vol_by_period[tau] = 0

    def increase_period_flow_vol(self, tau, fv):
        self.flow_vol_by_period[tau] += fv

    def calculate_td_vdf(self, demand_periods=None, iter_num=None):
        if demand_periods is None or iter_num is None:
            for tau in range(self.demand_period_size):
                self.travel_time_by_period[tau] = (
                    self.vdfperiods[tau].run_bpr(self.flow_vol_by_period[tau])
                )
        else:
            for dp in demand_periods:
                tau = dp.get_id()
                reduction_ratio = dp.get_reduction_ratio(self.id, iter_num)
                self.travel_time_by_period[tau] = (
                    self.vdfperiods[tau].run_bpr(self.flow_vol_by_period[tau],
                                                 reduction_ratio)
                )


class Agent:
    """ individual agent derived from aggregated demand between an OD pair

    agent_id: integer starts from 1
    agent_seq_no: internal agent index starting from 0 used for calculation
    """
    def __init__(self, agent_id, agent_seq_no, agent_type,
                 o_zone_id, d_zone_id):
        """ the attribute of agent """
        self.agent_id = agent_id
        self.agent_seq_no = agent_seq_no
        # vehicle
        self.agent_type = agent_type
        self.o_zone_id = o_zone_id
        self.d_zone_id = d_zone_id
        self.o_node_id = 0
        self.d_node_id = 0
        self.node_path = None
        self.link_path = None
        # Passenger Car Equivalent (PCE) of the agent
        self.PCE_factor = 1
        self.path_cost = 0

    def get_orig_node_id(self):
        return self.o_node_id

    def get_dest_node_id(self):
        return self.d_node_id

    def get_seq_no(self):
        return self.agent_seq_no

    def get_id(self):
        return self.agent_id

    def get_orig_zone_id(self):
        return self.o_zone_id

    def get_dest_zone_id(self):
        return self.d_zone_id

    def get_path_cost(self):
        return self.path_cost

    def get_node_path(self):
        return self.node_path


class Network:

    def __init__(self):
        self.nodes = []
        self.links = []
        self.agents = []
        self.node_size = 0
        self.link_size = 0
        self.agent_size = 0
        # key: node id, value: node seq no
        self.map_id_to_no = {}
        # key: node seq no, value: node id
        self.map_no_to_id = {}
        # map link id to link seq no
        self.link_ids = {}
        # key: zone id, value: node id list
        self.zone_to_nodes = {}
        # key: zone id, value: bin_index
        self.zone_bin_index = {}
        self.node_label_cost = None
        self.node_preds = None
        self.link_preds = None
        # added for CG
        self.zones = None
        self.capi_allocated = False
        # the following two are IDs rather than objects
        self._agent_type_size = 1
        self._demand_period_size = 1
        self.agent_type_name = 'all'
        # temporary implementations which will be replaced by class Zone
        self.activity_nodes = {}
        self.zone_info = {}
        self.ODMatrix = {}
        self.activity_node_num = 0

    def update(self, agent_type_size, demand_period_size):
        self.node_size = len(self.nodes)
        self.link_size = len(self.links)
        self.agent_size = len(self.agents)
        # it is needed for setup_spnetwork() and setup_spnetwork_a()
        self.zones = sorted(self.zone_to_nodes.keys())
        self._agent_type_size = agent_type_size
        self._demand_period_size = demand_period_size

    def allocate_for_CAPI(self):
        # execute only on the first call
        if self.capi_allocated:
            return

        node_size = self.node_size
        link_size = self.link_size

        # initialization for predecessors and label costs
        node_preds = [-1] * node_size
        link_preds = [-1] * node_size
        node_label_cost = [MAX_LABEL_COST] * node_size

        # initialize from_node_no_array, to_node_no_array, and link_cost_array
        from_node_no_array = [link.from_node_seq_no for link in self.links]
        to_node_no_array = [link.to_node_seq_no for link in self.links]
        link_cost_array = [link.cost for link in self.links]

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
                sorted_link_no_array[j] = link.link_seq_no
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

    def setup_agents(self, column_pool):
        agent_id = 1
        agent_no = 0

        for k, cv in column_pool.items():
            if cv.get_od_volume() <= 0:
                continue

            # k= (at, dp, orig, dest)
            at = k[0]
            orig = k[2]
            dest = k[3]

            vol = int(cv.get_od_volume()+1)
            for _ in range(vol):
                # construct agent using valid record
                agent = Agent(agent_id,
                              agent_no,
                              at,
                              orig,
                              dest)

                # step 1 generate o_node_id and d_node_id randomly
                # according to o_zone_id and d_zone_id
                agent.o_node_id = choice(
                    self.zone_to_nodes[orig]
                )
                agent.d_node_id = choice(
                    self.zone_to_nodes[dest]
                )

                # step 2 update agent_id and agent_seq_no
                agent_id += 1
                agent_no += 1

                self.agents.append(agent)

        self.agent_size = len(self.agents)
        print(f'the number of agents is {self.agent_size}')

    def _get_agent(self, agent_no):
        """ retrieve agent using agent_no """
        try:
            return self.agents[agent_no]
        except KeyError:
            print('Please provide a valid agent id, which shall be a\
                  positive integer!')

    def get_agent_node_path(self, agent_id, path_only):
        """ return the sequence of node IDs along the agent path

        developer's note: consider changing its name to
        get_agent_node_path_str()
        """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        path_cost = agent.get_path_cost()
        if path_cost >= MAX_LABEL_COST:
            return f'distance: infinity | path: '

        path = ''
        if agent.node_path:
            path = ';'.join(
                str(self.map_no_to_id[x]) for x in reversed(agent.node_path)
            )

        if path_only:
            return path
        else:
            return f'distance: {path_cost:.2f} | node path: {path}'

    def get_agent_link_path(self, agent_id, path_only):
        """ return the sequence of link IDs along the agent path

        developer's note: consider changing its name to
        get_agent_link_path_str()
        """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        path_cost = agent.get_path_cost()
        if path_cost >= MAX_LABEL_COST:
            return f'distance: infinity | path: '

        path = ''
        if agent.link_path:
            path = ';'.join(
            self.links[x].get_link_id() for x in reversed(agent.link_path)
        )

        if path_only:
            return path
        else:
            return f'distance: {path_cost:.2f} | link path: {path}'

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
        return self.agent_size

    def get_nodes_from_zone(self, zone_id):
        return self.zone_to_nodes[zone_id]

    def get_node_no(self, node_id):
        return self.map_id_to_no[node_id]

    def get_node_size(self):
        return self.node_size

    def get_link_size(self):
        return self.link_size

    def get_nodes(self):
        return self.nodes

    def get_links(self):
        return self.links

    def get_zones(self):
        return self.zones

    def get_zone_size(self):
        return len(self.zone_to_nodes)

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

    def get_link_costs(self):
        return self.link_cost_array

    def get_queue_next(self):
        return self.queue_next

    def get_allowed_uses(self):
        return self.allowed_uses

    def get_link(self, seq_no):
        return self.links[seq_no]

    def get_agent_type_name(self):
        """ for allowed uses in single_source_shortest_path()"""
        return self.agent_type_name

    def get_link_seq_no(self, id):
        return self.link_ids[id]

    def get_agents(self):
        return self.agents

    def get_last_thru_node(self):
        """ node no of the first potential centroid """
        return self.get_node_size()

    def set_agent_type_name(self, at_name):
        self.agent_type_name = at_name


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

    def set_gradient_cost_abs_diff(self, ad):
        self.gradient_cost_abs_diff = ad

    def set_gradient_cost_rel_diff(self, rd):
        self.gradient_cost_rel_diff = rd

    def increase_toll(self, t):
        self.toll += t

    def increase_volume(self, v):
        self.vol += v

    def set_geometry(self, g):
        self.geo = g


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

    def __init__(self, id=0, type='p', name='passenger',
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


class SpecialEvent:

    def __init__(self, name, beg_iteration, end_iteration) -> None:
        self.name = name
        self.beg_iter = beg_iteration
        self.end_iter = end_iteration
        self.affected_links = {}

    def get_beg_iteration(self):
        return self.beg_iter

    def get_end_iteration(self):
        return self.end_iter


class DemandPeriod:

    def __init__(self, id=0, period='AM', time_period='0700_0800'):
        self.id = id
        self.period = period
        self.time_period = time_period
        self.special_event = None

    def get_id(self):
        return self.id

    def get_period(self):
        return self.period

    def get_beg_iteration(self):
        return self.special_event.get_beg_iteration()

    def get_end_iteration(self):
        return self.special_event.get_end_iteration()

    def get_reduction_ratio(self, link_id, iter_num):
        if self.special_event is None:
            return 1

        if iter_num < self.get_beg_iteration() - 1 or iter_num > self.get_end_iteration() - 1:
            return 1

        try:
            return self.special_event.affected_links[link_id]
        except KeyError:
            return 1

class Demand:

    def __init__(self, id=0, period='AM', agent_type='p', file='demand.csv'):
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

    def get_avg_travel_time(self):
        return self.avg_travel_time

    def get_voc(self):
        return self.voc

    def get_fftt(self):
        return self.fftt

    def run_bpr(self, vol, reduction_ratio=1):
        vol = max(0, vol)
        self.voc = vol / max(SMALL_DIVISOR, self.capacity * reduction_ratio)
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
        # AgentType object
        self.agent_type = at
        # DemandPeriod object
        self.demand_period = dp

        # this is necessary for each instance of SPNetwork
        # to retrieve network topology
        if not base.capi_allocated:
            base.allocate_for_CAPI()

        # set up attributes unique to each instance
        node_preds = [-1] * base.node_size
        link_preds = [-1] * base.node_size
        node_lables = [MAX_LABEL_COST] * base.node_size
        queue_next = [0] * base.node_size
        link_cost_array = [link.cost for link in base.links]

        int_arr_node = ctypes.c_int * base.node_size
        double_arr_node = ctypes.c_double * base.node_size
        double_arr_link = ctypes.c_double * base.link_size

        self.node_preds = int_arr_node(*node_preds)
        self.link_preds = int_arr_node(*link_preds)
        self.node_label_cost = double_arr_node(*node_lables)
        self.link_cost_array = double_arr_link(*link_cost_array)
        self.queue_next = int_arr_node(*queue_next)

        # node id
        self.orig_nodes = []
        # zone sequence no
        self.orig_zones = []
        self.node_id_to_no = {}
        self.capi_allocated = True

    def add_orig_nodes(self, nodes):
        self.orig_nodes.extend(nodes)

    def allocate_for_CAPI(self):
        pass

    def get_node_no(self, node_id):
        try:
            return self.node_id_to_no[node_id]
        except KeyError:
            raise(f'EXCEPTION: Node ID {node_id} NOT IN THE NETWORK!!')

    def get_agent_type(self):
        return self.agent_type

    def get_agent_type_name(self):
        # convert it to C char
        return self.agent_type.get_name()

    def get_demand_period(self):
        return self.demand_period

    def get_orig_nodes(self):
        for i in self.orig_nodes:
            yield i

    # the following ten are shared by all SPNetworks
    # network topology
    def get_node_size(self):
        return self.base.get_node_size()

    def get_link_size(self):
        return self.base.get_link_size()

    def get_nodes(self):
        return self.base.get_nodes()

    def get_link(self, seq_no):
        self.base.get_link(seq_no)

    def get_links(self):
        return self.base.get_links()

    def get_zones(self):
        return self.base.get_zones()

    def get_from_node_no_arr(self):
        return self.base.get_from_node_no_arr()

    def get_to_node_no_arr(self):
        return self.base.get_to_node_no_arr()

    def get_first_links(self):
        return self.base.get_first_links()

    def get_last_links(self):
        return self.base.get_last_links()

    def get_sorted_link_no_arr(self):
        return self.base.get_sorted_link_no_arr()

    def get_allowed_uses(self):
        return self.base.get_allowed_uses()

    # the following five are unique to each SPNetwork
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

    def get_last_thru_node(self):
        """ node no of the first potential centroid """
        return super().get_last_thru_node()


class AccessNetwork(Network):
    """ network for accessibility evaluation """
    def __init__(self, base, add_cc=True):
        self.base = base
        self.nodes = self.base.get_nodes()
        self.links = self.base.get_links()
        self.map_id_to_no = self.base.map_id_to_no
        self.map_no_to_id = self.base.map_no_to_id
        self.node_size = base.get_node_size()
        self.link_size = base.get_link_size()
        self.centroids = []
        self.agent_type_name = 'all'
        self.pre_source_node_id = -1
        if add_cc:
            self._add_centroids_connectors()
        self.capi_allocated = False
        super().allocate_for_CAPI()

    def _add_centroids_connectors(self):
        # deep copy
        self.nodes = deepcopy(self.nodes)
        self.links = deepcopy(self.links)

        node_seq_no = self.node_size
        link_seq_no = self.link_size
        # get zones
        for z in self.get_zones():
            if z == -1:
                continue

            # create a centroid
            node_id = 'c_' + str(z)
            centroid = Node(node_seq_no, node_id, z)
            centroid.update_coordinate(self._get_zone_coord(z))

            self.nodes.append(centroid)
            self.centroids.append(centroid)

            self.map_id_to_no[node_id] = node_seq_no
            self.map_no_to_id[node_seq_no] = node_id

            # build connectors

            for i in self.get_nodes_from_zone(z):
                link_id_f = 'conn_' + str(link_seq_no)
                from_node_no = node_seq_no
                to_node_id = i

                try:
                    to_node_no = self.map_id_to_no[i]
                except KeyError:
                    continue

                # connector from centroid to activity nodes in this zone
                c_forward = Link(link_id_f,
                                 link_seq_no,
                                 from_node_no,
                                 to_node_no,
                                 node_id,
                                 to_node_id,
                                 0)

                # connector from activity nodes in this zone to centroid
                link_id_b = 'conn_' + str(link_seq_no+1)
                c_backward = Link(link_id_b,
                                  link_seq_no+1,
                                  to_node_no,
                                  from_node_no,
                                  to_node_id,
                                  node_id,
                                  0)

                self.nodes[from_node_no].add_outgoing_link(c_forward)
                self.nodes[to_node_no].add_outgoing_link(c_backward)

                self.links.append(c_forward)
                self.links.append(c_backward)

                link_seq_no += 2

            node_seq_no += 1

        self.node_size = len(self.nodes)
        self.link_size = len(self.links)

    def get_zones(self):
        return self.base.get_zones()

    def get_nodes_from_zone(self, zone_id):
        return self.base.zone_to_nodes[zone_id]

    def _get_zone_coord(self, zone_id):
        """ coordinate of each zone is from its first node """
        node_id = self.get_nodes_from_zone(zone_id)[0]
        node_seq_no = self.base.get_node_no(node_id)
        node = self.base.get_nodes()[node_seq_no]
        return node.coord_x, node.coord_y

    def get_zone_bin_indices(self):
        return self.base.zone_bin_index

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
        return self.centroids

    def get_node_no(self, node_id):
        return self.map_id_to_no[node_id]

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
        return self.node_label_cost[node_no]

    def get_link_costs(self):
        return super().get_link_costs()

    def get_queue_next(self):
        return super().get_queue_next()

    def get_allowed_uses(self):
        return super().get_allowed_uses()

    def get_last_thru_node(self):
        """ node no of the first centroid """
        return self.base.get_node_size()

    def get_pred_link_id(self, node_id):
        """ return id of the predecessor link to node_id """
        link_no = self.link_preds[self.get_node_no(node_id)]
        return self.links[link_no].get_link_id()

    def get_sp_distance(self, node_no):
        """ get the shortest path distance """
        dist = 0
        while node_no >= 0:
            link_seq_no = self.link_preds[node_no]
            if link_seq_no >= 0:
                dist += self.get_link(link_seq_no).get_length()

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
                    + link.get_toll() / max(SMALL_DIVISOR, vot) * 60
                )
        else:
            if not at.use_link_ffs:
                ffs = at.get_free_flow_speed()

                for link in self.get_links():
                    self.link_cost_array[link.get_seq_no()] = (
                        (link.get_length() / max(SMALL_DIVISOR, ffs) * 60)
                        + link.get_route_choice_cost()
                        + link.get_toll() / max(SMALL_DIVISOR, vot) * 60
                    )
            else:
                for link in self.get_links():
                    self.link_cost_array[link.get_seq_no()] = (
                        link.get_free_flow_travel_time()
                        + link.get_route_choice_cost()
                        + link.get_toll() / max(SMALL_DIVISOR, vot) * 60
                    )


class Assignment:

    def __init__(self):
        self.agent_types = []
        self.demand_periods = []
        self.demands = []
        # 4-d array
        self.column_pool = {}
        self.network = None
        self.spnetworks = []
        self.accessnetwork = None
        self.memory_blocks = 4
        self.map_atstr_id = {}
        self.map_dpstr_id = {}
        self.map_name_atstr = {}

    def update_agent_types(self, at):
        if at.get_type_str() not in self.map_atstr_id:
            self.map_atstr_id[at.get_type_str()] = at.get_id()
        else:
            raise Exception('agent type is not unique:'+at.get_type_str())

        if at.get_name() not in self.map_name_atstr:
            self.map_name_atstr[at.get_name()] = at.get_type_str()
        else:
            raise Exception('agent type name is not unique:'+at.get_name())

        self.agent_types.append(at)

    def update_demand_periods(self, dp):
        if dp.get_period() not in self.map_dpstr_id:
            self.map_dpstr_id[dp.get_period()] = dp.get_id()
        else:
            raise Exception('demand period is not unique:'+dp.get_period())

        self.demand_periods.append(dp)

    def get_agent_type_id(self, at_str):
        try:
            return self.map_atstr_id[at_str]
        except KeyError:
            raise Exception('NO agent type: '+at_str)

    def get_demand_period_id(self, dp_str):
        try:
            return self.map_dpstr_id[dp_str]
        except KeyError:
            raise Exception('NO demand period: '+dp_str)

    def get_agent_type(self, at_str):
        return self.agent_types[self.get_agent_type_id(at_str)]

    def get_demand_period(self, dp_str):
        return self.demand_periods[self.get_demand_period_id(dp_str)]

    def get_agent_type_str(self, at_id):
        try:
            return self.agent_types[at_id].get_type_str()
        except KeyError:
            raise Exception('NO agent type id: '+at_id)

    def get_demand_period_str(self, dp_id):
        try:
            return self.demand_periods[dp_id].get_period()
        except KeyError:
            raise Exception('NO demand period id: '+dp_id)

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

    def get_agent_node_path(self, agent_id, path_only=False):
        """ return the sequence of node IDs along the agent path

        exception will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_node_path(agent_id, path_only)

    def get_agent_link_path(self, agent_id, path_only=False):
        """ return the sequence of link IDs along the agent path

        exception will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_link_path(agent_id, path_only)

    def _convert_mode(self, mode):
        """convert mode to the corresponding agent type name and string"""
        if mode in self.map_atstr_id:
            at = self.get_agent_type(mode)
            return at.get_name(), mode

        if mode in self.map_name_atstr:
            return mode, self.map_name_atstr[mode]

        # for distance-based shortest path calculation only
        # it shall not be used with any accessibility evaluations
        if mode == 'all':
            return mode, mode

        raise Exception('Please provide a valid mode!')

    def find_path_for_agents(self, mode):
        """ find and set up shortest path for each agent """
        # reset agent type str or mode according to user's input
        at_name, _ = self._convert_mode(mode)
        self.network.set_agent_type_name(at_name)

        find_path_for_agents(self.network, self.column_pool)

    def find_shortest_path(self, from_node_id, to_node_id, mode, seq_type='node'):
        """ call find_shortest_path() from path.py

        exceptions will be handled in find_shortest_path()
        """
        # reset agent type str or mode according to user's input
        at_name, _ = self._convert_mode(mode)
        self.network.set_agent_type_name(at_name)

        return find_shortest_path(self.network, from_node_id,
                                  to_node_id, seq_type)

    def perform_network_assignment(self, assignment_mode,
                                   iter_num, column_update_num):
        # perform_network_assignment(assignment_mode, iter_num, column_update_num)
        pass

    def perform_network_assignment_DTALite(self, assignment_mode,
                                           iter_num, column_update_num):

        # perform_network_assignment_DTALite(assignment_mode,
        #                                    iter_num,
        #                                    column_update_num)
        pass

    def setup_spnetwork(self):
        spvec = {}

        # z is zone id starting from 1
        for z in self.network.zones:
            if z == -1:
                continue

            for d in self.demands:
                at = self.get_agent_type(d.get_agent_type_str())
                dp = self.get_demand_period(d.get_period())
                if z - 1 < self.memory_blocks:
                    sp = SPNetwork(self.network, at, dp)
                    spvec[(at.get_id(), dp.get_id(), z-1)] = sp
                    sp.orig_zones.append(z)
                    sp.add_orig_nodes(self.network.get_nodes_from_zone(z))
                    for node_id in self.network.get_nodes_from_zone(z):
                        sp.node_id_to_no[node_id] = (
                            self.network.get_node_no(node_id)
                        )
                    self.spnetworks.append(sp)
                else:
                    m = (z - 1) % self.memory_blocks
                    sp = spvec[(at.get_id(), dp.get_id(), m)]
                    sp.orig_zones.append(z)
                    sp.add_orig_nodes(self.network.get_nodes_from_zone(z))
                    for node_id in self.network.get_nodes_from_zone(z):
                        sp.node_id_to_no[node_id] = (
                            self.network.get_node_no(node_id)
                        )

    def get_link(self, seq_no):
        """ return link object corresponding to link seq no """
        return self.network.get_link(seq_no)

    def get_link_seq_no(self, id):
        """ id is string """
        return self.network.get_link_seq_no(id)

    def get_node_no(self, id):
        """ id is integer """
        return self.network.get_node_no(id)

    def get_agents(self):
        return self.network.get_agents()

    def get_node_label_cost(self, node_no):
        return self.accessnetwork.get_node_label_cost(node_no)

    def get_accessible_nodes(self, source_node_id, time_budget,
                             mode, time_dependent, tau):
        if source_node_id not in self.network.map_id_to_no.keys():
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
            node_no = node.get_node_no()
            # do not include the source node itself
            if node.get_node_id() == source_node_id:
                continue
            if self.accessnetwork.get_node_label_cost(node_no) <= time_budget:
                nodes.append(node.get_node_id())

        return nodes

    def get_accessible_links(self, source_node_id, time_budget,
                             mode, time_dependent, tau):
        # node id's
        nodes = self.get_accessible_nodes(source_node_id, time_budget,
                                          mode, time_dependent, tau)
        # convert to link id's
        return [
            self.accessnetwork.get_pred_link_id(x) for x in nodes
        ]

    def activity_nodes(self):
        return self.network.activity_nodes


class UI:
    """ an abstract class only with user interfaces """
    def __init__(self, assignment):
        self._base_assignment = assignment

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
        return self._base_assignment.get_agent_node_path(agent_id)

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path """
        return self._base_assignment.get_agent_link_path(agent_id)

    def find_path_for_agents(self, mode='all'):
        """ find and set up shortest path for each agent """
        return self._base_assignment.find_path_for_agents(mode)

    def find_shortest_path(self, from_node_id, to_node_id,
                           mode='all', seq_type='node'):
        """ return shortest path between from_node_id and to_node_id

        Parameters
        ----------
        from_node_id
            the starting node id

        to_node_id
            the ending node id

        seq_type
            'node' or 'link'. You will get the shortest path in sequence of
            either node IDs or link IDs. The default is 'node'.

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.

            The default is 'all', which means that links are open to all modes.

        Outputs
        -------
        the shortest path between from_node_id and to_node_id

        Exceptions will be thrown if either of them or both are not valid node
        IDs.
        """
        return self._base_assignment.find_shortest_path(
            from_node_id,
            to_node_id,
            mode,
            seq_type
        )

    def get_accessible_nodes(self,
                             source_node_id,
                             time_budget,
                             mode='p',
                             time_dependent=False,
                             demand_period_id=0):
        """ get the accessible nodes from a node given mode and time budget

        Parameters
        ----------
        source_node_id
            the starting node id for evaluation

        time_budget
            the amount of time to travel in minutes

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs. Its default value is 'p' (i.e., mode auto).

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

        Outputs
        -------
        print out the number of nodes that can be accessible from \
        source_node_id given time_budget and mode, and the node list
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
                             mode='p',
                             time_dependent=False,
                             demand_period_id=0):
        """ get the accessible links from a node given mode and time budget

        Parameters
        ----------
        source_node_id
            the starting node id for evaluation

        time_budget
            the amount of time to travel in minutes

        mode
            the target transportation mode which is defined in settings.yml. It
            can be either agent type or its name. For example, 'w' and 'walk'
            are equivalent inputs.


        Outputs
        -------
        print out the number of links that can be accessible from \
        source_node_id given time_budget and mode, and the link list
        """
        links = self._base_assignment.get_accessible_links(source_node_id,
                                                           time_budget,
                                                           mode,
                                                           time_dependent,
                                                           demand_period_id)

        link_strs = ';'.join(str(x) for x in links)

        print(f'number of accessible links is {len(links)}')
        print(f'accessible links are: {link_strs}')