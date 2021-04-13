import ctypes
from random import choice

from .path import find_path_for_agents, find_shortest_path
from .consts import MAX_LABEL_COST


__all__ = ['UI']


class Node:

    def __init__(self, node_seq_no, external_node_id, zone_id, x='', y=''):
        """ the attributes of node  """
        # external_node_id: user defined node id from input
        self.node_seq_no = node_seq_no
        # node_seq_no: internal node index used for calculation
        self.external_node_id = external_node_id
        self.outgoing_link_list = []
        self.incoming_link_list = []
        self.zone_id = zone_id
        self.coord_x = x
        self.coord_y = y

    def has_outgoing_links(self):
        return len(self.outgoing_link_list) > 0

    def get_zone_id(self):
        return self.zone_id

    def get_node_id(self):
        return self.external_node_id

    def get_node_no(self):
        return self.node_seq_no

    def get_coordinate(self):
        return self.coord_x + ' ' + self.coord_y

    def add_outgoing_link(self, link):
        self.outgoing_link_list.append(link)

    def add_incoming_link(self, link):
        self.incoming_link_list.append(link)


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
        self.external_from_node = from_node_id
        self.external_to_node = to_node_id
        # length is mile or km
        self.length = length
        self.lanes = lanes
        # 1:one direction, 2:two way, 3: virtual connector
        self.type = link_type
        # length:km, free_speed: km/h
        self.free_flow_travel_time_in_min = (
            length / max(0.001, free_speed) * 60
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
        # Peiheng, 04/05/21, not needed for the current implementation
        # self.queue_length_by_slot = [0] * MAX_TIME_PERIODS
        # self.vol_by_period_by_at = [
        #     [0] * demand_period_size for i in range(agent_type_size)
        # ]
        # self.travel_marginal_cost_by_period = [
        #     [0] * demand_period_size for i in range(agent_type_size)
        # ]

    def get_link_id(self):
        return self.id

    def get_seq_no(self):
        return self.link_seq_no

    def get_from_node_id(self):
        return self.external_from_node

    def get_to_node_id(self):
        return self.external_to_node

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

    def get_period_avg_travel_time(self, tau):
        return self.vdfperiods[tau].get_avg_travel_time()

    def get_generalized_cost(self, tau, value_of_time):
        return (
            self.travel_time_by_period[tau]
            + self.toll / max(0.001, value_of_time) * 60
        )

    def reset_period_flow_vol(self, tau):
        self.flow_vol_by_period[tau] = 0

    # def reset_period_agent_vol(self, tau, agent_type):
    #     self.vol_by_period_by_at[tau][agent_type] = 0

    def increase_period_flow_vol(self, tau, fv):
        self.flow_vol_by_period[tau] += fv

    # def increase_period_agent_vol(self, tau, agent_type, v):
    #     self.vol_by_period_by_at[tau][agent_type] += v

    def calculate_td_vdfunction(self):
        for tau in range(self.demand_period_size):
            self.travel_time_by_period[tau] = (
                self.vdfperiods[tau].run_bpr(self.flow_vol_by_period[tau])
            )

    # Peiheng, 04/05/21, not needed for the current implementation
    # def calculate_agent_marginal_cost(self, tau, agent_type):
    #     self.travel_marginal_cost_by_period[tau][agent_type.get_id()] = (
    #         self.vdfperiods[tau].marginal_base * agent_type.get_pce()
    #     )


class Agent:
    """ individual agent derived from aggragted demand between an OD pair

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
        self.current_link_seq_no_in_path = 0
        self.departure_time_in_min = 0
        # Passenger Car Equivalent (PCE) of the agent
        self.PCE_factor = 1
        self.path_cost = 0
        # self.departure_time_in_simu_interval = int(
        #     self.departure_time_in_min
        #     * 60 /_NUM_OF_SECS_PER_SIMU_INTERVAL
        #     + 0.5)
        self.b_generated = False
        self.b_complete_trip = False
        self.feasible_path_exist_flag = False

    def get_orig_node_id(self):
        return self.o_node_id

    def get_dest_node_id(self):
        return self.d_node_id

    def get_seq_no(self):
        return self.agent_seq_no

    # def get_dep_simu_intvl(self):
    #     return self.departure_time_in_simu_interval


class Network:

    def __init__(self):
        self.node_list = []
        self.link_list = []
        self.agent_list = []
        self.node_size = 0
        self.link_size = 0
        self.agent_size = 0
        # key: external node id, value:internal node id
        self.internal_node_seq_no_dict = {}
        # key: internal node id, value:external node id
        self.external_node_id_dict = {}
        # map link id to link seq no
        self.link_id_dict = {}
        # td:time-dependent, key:simulation time interval,
        # value:agents(list) need to be activated
        self.agent_td_list_dict = {}
        # key: zone id, value: node id list
        self.zone_to_nodes_dict = {}
        self.node_label_cost = None
        self.node_predecessor = None
        self.link_predecessor = None
        # added for CG
        self.zones = None
        self.has_capi_allocated = False
        # the following two are IDs rather than objects
        self._agent_type_size = 1
        self._demand_period_size = 1

    def update(self, agent_type_size, demand_period_size):
        self.node_size = len(self.node_list)
        self.link_size = len(self.link_list)
        self.agent_size = len(self.agent_list)
        self.zones = self.zone_to_nodes_dict.keys()
        self._agent_type_size = agent_type_size
        self._demand_period_size = demand_period_size

    @staticmethod
    def convert_allowed_use(au):
        if au.lower().startswith('auto'):
            return 'p'
        elif au.lower().startswith('bike'):
            return 'b'
        elif au.lower().startswith('walk'):
            return 'w'
        elif au.lower().startswith('all'):
            return 'a'
        else:
            raise Exception('allowed use type is not in the predefined list!')

    def _setup_allowed_use(self, allowed_uses):
        for i, link in enumerate(self.link_list):
            modes = link.allowed_uses.split(',')
            if not modes:
                continue

            allowed_uses[i] = ''.join(
                Network.convert_allowed_use(m) for m in modes
            )

    def allocate_for_CAPI(self):
        # execute only on the first call
        if self.has_capi_allocated:
            return

        node_size = self.node_size
        link_size = self.link_size

        # initialization for predecessors and label costs
        node_predecessor = [-1] * node_size
        link_predecessor = [-1] * node_size
        node_label_cost = [MAX_LABEL_COST] * node_size

        # initialize from_node_no_array, to_node_no_array, and link_cost_array
        from_node_no_array = [link.from_node_seq_no for link in self.link_list]
        to_node_no_array = [link.to_node_seq_no for link in self.link_list]
        link_cost_array = [link.cost for link in self.link_list]

        # initialize others as numpy arrays directly
        queue_next = [0] * node_size
        first_link_from = [-1] * node_size
        last_link_from = [-1] * node_size
        sorted_link_no_array = [-1] * link_size

        # internal link index used for shortest path calculation only
        j = 0
        for i, node in enumerate(self.node_list):
            if not node.outgoing_link_list:
                continue
            first_link_from[i] = j
            for link in node.outgoing_link_list:
                # set up the mapping from j to the true link seq no
                sorted_link_no_array[j] = link.link_seq_no
                j += 1
            last_link_from[i] = j

        # setup allowed uses
        allowed_uses = [''] * link_size
        self._setup_allowed_use(allowed_uses)

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
        self.node_predecessor = int_arr_node(*node_predecessor)
        self.link_predecessor = int_arr_node(*link_predecessor)
        self.queue_next = int_arr_node(*queue_next)
        self.allowed_uses = char_arr_link(*allowed_uses)

        self.has_capi_allocated = True

    def setup_agents(self, column_pool):
        agent_id = 1
        agent_no = 0

        for orig in self.zones:
            for dest in self.zones:
                for at in range(self._agent_type_size):
                    for dp in range(self._demand_period_size):
                        if (at, dp, orig, dest) not in column_pool.keys():
                                continue

                        cv = column_pool[(at, dp, orig, dest)]

                        if cv.get_od_volume() <= 0:
                            continue

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
                                self.zone_to_nodes_dict[orig]
                            )
                            agent.d_node_id = choice(
                                self.zone_to_nodes_dict[dest]
                            )

                            # step 2 update agent_id and agent_seq_no
                            agent_id += 1
                            agent_no += 1

                            # step 3: update the g_simulation_start_time_in_min and
                            # g_simulation_end_time_in_min
                            # if agent.departure_time_in_min < g_simulation_start_time_in_min:
                            #     g_simulation_start_time_in_min = agent.departure_time_in_min
                            # if agent.departure_time_in_min > g_simulation_end_time_in_min:
                            #     g_simulation_end_time_in_min = agent.departure_time_in_min

                            #step 4: add the agent to the time dependent agent list
                            # departure_time = agent.get_dep_simu_intvl()
                            # if departure_time not in self.agent_td_list_dict.keys():
                            #     self.agent_td_list_dict[departure_time] = []
                            # self.agent_td_list_dict[departure_time].append(
                            #     agent.get_seq_no()
                            # )

                            self.agent_list.append(agent)

        # 03/22/21, comment out until departure time is enabled
        # in the future release

        #step 3.6:sort agents by the departure time
        # agents.sort(key=lambda agent: agent.departure_time_in_min)
        # for i, agent in enumerate(agents):
        #     agent.agent_seq_no = i

        self.agent_size = len(self.agent_list)
        print(f"the number of agents is {self.agent_size}")

    def _get_agent(self, agent_no):
        """ retrieve agent using agent_no """
        try:
            return self.agent_list[agent_no]
        except KeyError:
            print('Please provide a valid agent id, which shall be a\
                  positive integer!')

    def get_agent_node_path(self, agent_id):
        """ return the sequence of node IDs along the agent path """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        if not agent.node_path:
            return ''

        return ';'.join(
            str(self.external_node_id_dict[x]) for x in reversed(agent.node_path)
        )

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)

        if not agent.link_path:
            return ''

        return ';'.join(
            self.link_list[x].get_link_id() for x in reversed(agent.link_path)
        )

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
        return self.zone_to_nodes_dict[zone_id]

    def get_node_no(self, node_id):
        return self.internal_node_seq_no_dict[node_id]

    def get_node_size(self):
        return self.node_size

    def get_link_size(self):
        return self.link_size

    def get_nodes(self):
        return self.node_list

    def get_links(self):
        return self.link_list

    def get_zones(self):
        return self.zones

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
        return self.node_predecessor

    def get_link_preds(self):
        return self.link_predecessor

    def get_node_label_costs(self):
        return self.node_label_cost

    def get_link_costs(self):
        return self.link_cost_array

    def get_queue_next(self):
        return self.queue_next

    def get_allowed_uses(self):
        return self.allowed_uses

    def get_link(self, seq_no):
        return self.link_list[seq_no]

    def get_agent_type_str(self):
        """ for allowed uses in single_source_shortest_path()"""
        # convert it to C char
        return 'a'.encode()

    def get_link_seq_no(self, id):
        return self.link_id_dict[id]


class Column:

    def __init__(self, seq_no=-1):
        self.seq_no = seq_no
        self.vol = 0
        self.dist = 0
        self.toll = 0
        self.travel_time = 0
        self.switch_vol = 0
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

    def get_seq_no(self):
        return self.seq_no

    def get_distance(self):
        return self.dist

    def get_volume(self):
        return self.vol

    def get_toll(self):
        return self.toll

    def get_travel_time(self):
        return self.travel_time

    def get_switch_volume(self):
        return self.switch_vol

    def get_gradient_cost(self):
        return self.gradient_cost

    def get_gradient_cost_abs_diff(self):
        return self.gradient_cost_abs_diff

    def get_gradient_cost_rel_diff(self):
        return self.gradient_cost_rel_diff

    def get_links(self):
        """ return link seq no """
        return self.links

    def set_distance(self, d):
        self.dist = d

    def set_volume(self, v):
        self.vol = v

    def set_toll(self, t):
        self.toll = t

    def set_travel_time(self, tt):
        self.travel_time = tt

    def set_switch_volume(self, sv):
        self.switch_vol = sv

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

    def __init__(self):
        self.od_vol = 0
        self.route_fixed = False
        self.path_node_seq_map = {}
        # minimum free-flow travel time between O and D
        # for accessiblity evaluation
        self.min_tt = -1

    def is_route_fixed(self):
        return self.route_fixed

    def get_od_volume(self):
        return self.od_vol

    def get_column_num(self):
        return len(self.path_node_seq_map)

    def get_columns(self):
        return self.path_node_seq_map

    def get_column(self, k):
        return self.path_node_seq_map[k]

    def add_new_column(self, node_sum, col):
        self.path_node_seq_map[node_sum] = col

    def get_min_travel_time(self):
        return self.min_tt

    def update_min_travel_time(self, t):
        if self.min_tt > t or self.min_tt == -1:
           self.min_tt = t


class AgentType:

    def __init__(self, id=0, type='p', name='passenger',
                 vot=10, flow_type=0, pce=1, ffs=60):
        """ default constructor """
        self.id = id
        self.type = type
        self.name = name
        self.vot = vot
        self.flow_type = flow_type
        self.pce = pce
        self.ffs = ffs

    def get_id(self):
        return self.id

    def get_vot(self):
        return self.vot

    def get_type(self):
        return self.type

    def get_pce(self):
        return self.pce

    def get_free_flow_speed(self):
        return self.ffs


class DemandPeriod:

    def __init__(self, id=0, period='AM', time_period='0700_0800'):
        self.id = id
        self.period = period
        self.time_period = time_period

    def get_id(self):
        return self.id

    def get_file_name(self):
        return self.file

    def get_period(self):
        return self.period


class Demand:

    def __init__(self, id=0, period='AM', agent_type='p', file='demand.csv'):
        self.id = id
        self.period = period
        self.agent_type = agent_type
        self.file = file

    def get_id(self):
        return self.id

    def get_file_name(self):
        return self.file

    def get_period(self):
        return self.period

    def get_agent_type(self):
        return self.agent_type


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
        self.marginal_base = 1
        self.avg_travel_time = 0
        self.voc = 0

    def get_avg_travel_time(self):
        return self.avg_travel_time

    def get_voc(self):
        return self.voc

    def run_bpr(self, vol):
        vol = max(0, vol)
        self.voc = vol / max(0.00001, self.capacity)

        self.marginal_base = (
            self.fftt
            * self.alpha
            * self.beta
            * pow(self.voc, self.beta - 1)
        )

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
        # to retrieve network topoloy
        if not base.has_capi_allocated:
            base.allocate_for_CAPI()

        # set up attributes unique to each instance
        node_preds = [-1] * base.node_size
        link_preds = [-1] * base.node_size
        node_lables = [MAX_LABEL_COST] * base.node_size
        queue_next = [0] * base.node_size
        link_cost_array = [link.cost for link in base.link_list]

        int_arr_node = ctypes.c_int * base.node_size
        double_arr_node = ctypes.c_double * base.node_size
        double_arr_link = ctypes.c_double * base.link_size

        self.node_predecessor = int_arr_node(*node_preds)
        self.link_predecessor = int_arr_node(*link_preds)
        self.node_label_cost = double_arr_node(*node_lables)
        self.link_cost_array = double_arr_link(*link_cost_array)
        self.queue_next = int_arr_node(*queue_next)

        # node id
        self.orig_nodes = []
        # zone sequence no
        self.orig_zones = []
        self.node_id_to_no = {}
        self.has_capi_allocated = True

    def add_orig_nodes(self, nodes):
        self.orig_nodes.extend(nodes)

    def allocate_for_CAPI(self):
        pass

    def get_node_no(self, node_id):
        try:
            return self.node_id_to_no[node_id]
        except KeyError:
            raise(f"EXCEPTION: Node ID {node_id} NOT IN THE NETWORK!!")

    def get_agent_type(self):
        return self.agent_type

    def get_agent_type_str(self):
        # convert it to C char
        return self.agent_type.get_type().encode()

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
        return self.node_predecessor

    def get_link_preds(self):
        return self.link_predecessor

    def get_node_label_costs(self):
        return self.node_label_cost

    def get_link_costs(self):
        return self.link_cost_array

    def get_queue_next(self):
        return self.queue_next


class Assignment:

    def __init__(self):
        self.agent_types = []
        self.demand_periods = []
        self.demands = []
        # 4-d array
        self.column_pool = {}
        self.network = None
        self.spnetworks = []
        self.memory_blocks = 4
        self.map_at_id = {}
        self.map_dp_id = {}

    def update_agent_types(self, at):
        self.agent_types.append(at)
        self.map_at_id[at.get_type()] = at.get_id()

    def update_demand_periods(self, dp):
        self.demand_periods.append(dp)
        self.map_dp_id[dp.get_period()] = dp.get_id()

    def get_agent_type_id(self, at_str):
        try:
            return self.map_at_id[at_str]
        except KeyError:
            raise Exception('NO agent type: '+at_str)

    def get_demand_period_id(self, dp_str):
        try:
            return self.map_dp_id[dp_str]
        except KeyError:
            raise Exception('NO demand period: '+dp_str)

    def get_agent_type(self, at_str):
        return self.agent_types[self.get_agent_type_id(at_str)]

    def get_demand_period(self, dp_str):
        return self.demand_periods[self.get_demand_period_id(dp_str)]

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

        excepition will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_orig_node_id(agent_id)

    def get_agent_dest_node_id(self, agent_id):
        """ return the destnation node id of an agent

        excepition will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_dest_node_id(agent_id)

    def get_agent_node_path(self, agent_id):
        """ return the sequence of node IDs along the agent path

        excepition will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_node_path(agent_id)

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path

        excepition will be handled by  _get_agent() in class Network
        """
        return self.network.get_agent_link_path(agent_id)

    def find_path_for_agents(self):
        """ find and set up shortest path for each agent """
        find_path_for_agents(self.network, self.column_pool)

    def find_shortest_path(self, from_node_id, to_node_id, seq_type='node'):
        """ call find_shortest_path() from path.py

        exceptions will be handled in find_shortest_path()
        """
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
                at = self.get_agent_type(d.get_agent_type())
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

    def setup_spntwork_a(self):
        """ set up SPNetworks for accessibility evaluation """
        spvec = {}
        # we only need one demand period even multiple could exist
        dp = self.demand_periods[0]

        # z is zone id starting from 1
        for z in self.network.zones:
            for at in self.get_agent_types():
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

    def setup_column_pool_a(self):
        """ set up column_pool for accessibility evaluation """
        dp = 0
        for oz in self.get_zones():
            if oz == -1:
                continue
            for dz in self.get_zones():
                if dz == -1:
                    continue
                for atype in self.agent_types:
                    at = atype.get_id()
                    self.column_pool[(at, dp, oz, dz)] = ColumnVec()
                    if oz == dz:
                        continue
                    # set up volume/demand for all OD pairs where O != D
                    self.column_pool[(at, dp, oz, dz)].od_vol = 1

    def get_link(self, seq_no):
        """ return link object corresponding to link seq no """
        return self.network.get_link(seq_no)

    def get_link_seq_no(self, id):
        """ id is string """
        return self.network.get_link_seq_no(id)

    def get_node_no(self, id):
        """ id is integer """
        return self.network.get_node_no(id)


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
        return self._base_assignment.network.get_agent_orig_node_id(agent_id)

    def get_agent_dest_node_id(self, agent_id):
        """ return the destnation node id of an agent """
        return self._base_assignment.network.get_agent_dest_node_id(agent_id)

    def get_agent_node_path(self, agent_id):
        """ return the sequence of node IDs along the agent path """
        return self._base_assignment.network.get_agent_node_path(agent_id)

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path """
        return self._base_assignment.network.get_agent_link_path(agent_id)

    def find_path_for_agents(self):
        """ find and set up shortest path for each agent """
        return self._base_assignment.find_path_for_agents()

    def find_shortest_path(self, from_node_id, to_node_id, seq_type='node'):
        """ return shortest path between from_node_id and to_node_id

        Parameters
        ----------
        from_node_id: the starting node id
        to_node_id  : the ending node id
        seq_type    : 'node' or 'link'. You will get the shortest path in
                      sequence of either node IDs or link IDs. The default is
                      'node'

        Outputs
        -------
        the shortest path between from_node_id and to_node_id

        Exceptions will be thrown if either of them or both are not valid node
        IDs.
        """
        return self._base_assignment.find_shortest_path(
            from_node_id,
            to_node_id,
            seq_type
        )