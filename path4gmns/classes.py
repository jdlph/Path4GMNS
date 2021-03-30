import ctypes
from random import choice

from .path import MAX_LABEL_COST, find_path_for_agents, find_shortest_path


_NUM_OF_SECS_PER_SIMU_INTERVAL = 6 
MAX_TIME_PERIODS = 1
MAX_AGENT_TYPES = 1


class Node:         
    """ 
    external_node_id: the id of node
    node_seq_no: the index of the node and we call the node by its index
    
    we use g_internal_node_seq_no_dict(id to index) and 
    g_external_node_id_dict(index to id) to map them
    """

    def __init__(self, node_seq_no, external_node_id, zone_id, x='', y=''): 
        """ the attribute of node  """ 
        self.node_seq_no = node_seq_no
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
                 allowed_uses='auto',
                 geometry=''):   
        """ the attribute of link """
        self.id = id
        self.link_seq_no = link_seq_no
        self.from_node_seq_no = from_node_no
        self.to_node_seq_no = to_node_no
        self.external_from_node = from_node_id
        self.external_to_node = to_node_id
        # length is mile or km
        self.length = length
        self.lanes = lanes
        # 1:one direction 2:two way
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
        self.toll = 0
        self.route_choice_cost = 0
        self.travel_time_by_period = [0] * MAX_TIME_PERIODS
        self.flow_vol_by_period = [0] * MAX_TIME_PERIODS
        self.vol_by_period_by_at = [
            [0] * MAX_TIME_PERIODS for i in range(MAX_AGENT_TYPES)
        ]
        # self.queue_length_by_slot = [0] * MAX_TIME_PERIODS
        self.vdfperiods = []
        self.travel_marginal_cost_by_period = [
            [0] * MAX_TIME_PERIODS for i in range(MAX_AGENT_TYPES)
        ]

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

    def get_generalized_cost(self, tau, agent_type, value_of_time=10):
        return self.travel_time_by_period[tau] + self.toll / value_of_time * 60

    def reset_period_flow_vol(self, tau):
        self.flow_vol_by_period[tau] = 0

    def reset_period_agent_vol(self, tau, agent_type):
        self.vol_by_period_by_at[tau][agent_type] = 0

    def increase_period_flow_vol(self, tau, fv):
        self.flow_vol_by_period[tau] += fv

    def increase_period_agent_vol(self, tau, agent_type, v):
        self.vol_by_period_by_at[tau][agent_type] += v

    def calculate_td_vdfunction(self):
        for tau in range(MAX_TIME_PERIODS):
            self.travel_time_by_period[tau] = (
                self.vdfperiods[tau].run_bpr(self.flow_vol_by_period[tau])
            )
    
    def calculate_agent_marginal_cost(self, tau, agent_type, PCE_agent_type=1):
        self.travel_marginal_cost_by_period[tau][agent_type] = (
            self.vdfperiods[tau].marginal_base * PCE_agent_type
        )


class Agent:
    """ individual agent derived from aggragted demand between an OD pair

    agent_id: the id of agent
    agent_seq_no: the index of the agent and we call the agent by its index
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
        self.departure_time_in_simu_interval = int(
            self.departure_time_in_min 
            * 60 /_NUM_OF_SECS_PER_SIMU_INTERVAL
            + 0.5)
        self.b_generated = False
        self.b_complete_trip = False
        self.feasible_path_exist_flag = False

    def get_orig_node_id(self):
        return self.o_node_id

    def get_dest_node_id(self):
        return self.d_node_id

    def get_seq_no(self):
        return self.agent_seq_no

    def get_dep_simu_intvl(self):
        return self.departure_time_in_simu_interval
 

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
        self._agent_types = 0
        self._demand_periods = 0

    def update(self, agent_types=0, demand_periods=0):
        self.node_size = len(self.node_list)
        self.link_size = len(self.link_list)
        self.agent_size = len(self.agent_list)
        self.zones = self.zone_to_nodes_dict.keys()
        self._agent_types = agent_types
        self._demand_periods = demand_periods

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

        # set up arrays using ctypes
        int_arr_node = ctypes.c_int * node_size
        int_arr_link = ctypes.c_int * link_size
        double_arr_node = ctypes.c_double * node_size
        double_arr_link = ctypes.c_double * link_size

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
        
        self.has_capi_allocated = True

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
        
        return ';'.join(
            str(self.external_node_id_dict[x]) for x in agent.node_path
        )

    def get_agent_link_path(self, agent_id):
        """ return the sequence of link IDs along the agent path """
        agent_no = agent_id - 1
        agent = self._get_agent(agent_no)
            
        return ';'.join(
            self.link_list[x].get_link_id() for x in agent.link_path
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

    def setup_agents(self, column_pool):
        agent_id = 1
        agent_no = 0
        
        for orig in self.zones:
            for dest in self.zones:
                for at in range(self._agent_types):
                    for dp in range(self._demand_periods):
                        if (at, dp, orig, dest) not in column_pool.keys():
                                continue

                        cv = column_pool[(at, dp, orig, dest)]

                        if cv.get_od_volume() <= 0:
                            continue

                        vol = int(cv.get_od_volume()+1)

                        for i in range(vol):
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
                            departure_time = agent.get_dep_simu_intvl()
                            if departure_time not in self.agent_td_list_dict.keys():
                                self.agent_td_list_dict[departure_time] = []
                            self.agent_td_list_dict[departure_time].append(
                                agent.get_seq_no()
                            )
                            
                            self.agent_list.append(agent)

        # 03/22/21, comment out until departure time is enabled 
        # in the future release
        
        #step 3.6:sort agents by the departure time
        # agents.sort(key=lambda agent: agent.departure_time_in_min)
        # for i, agent in enumerate(agents):
        #     agent.agent_seq_no = i

        self.agent_size = len(self.agent_list)
        print(f"the number of agents is {self.agent_size}")

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

    def get_node_list(self):
        return self.node_list

    def get_link_list(self):
        return self.link_list

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

    def get_link_costs(self):
        return self.link_cost_array

    def get_node_preds(self):
        return self.node_predecessor

    def get_link_preds(self):
        return self.link_predecessor

    def get_node_label_costs(self):
        return self.node_label_cost

    def get_queue_next(self):
        return self.queue_next


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


class ColumnVec:
    
    def __init__(self):
        self.od_vol = 0
        self.route_fixed = False
        self.path_node_seq_map = {}

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


class AgentType:

    def __init__(self, id=0, type='p', name='passenger', 
                 vot=10, flow_type=0, pce=1):
                 
        self.id = id
        self.type = type
        self.name = name
        self.vot = vot
        self.flow_type = flow_type
        self.pce = pce

    def get_id(self):
        return self.id

    def get_vot(self):
        return self.vot

    def get_type(self):
        return self.type


class DemandPeriod:

    def __init__(self, id=0, period='AM', time_period='0700_0800', 
                 agent_type='p', file='demand.csv'):

        self.id = id
        self.period = period
        self.time_period = time_period
        self.agent_type = agent_type
        self.file = file

    def get_id(self):
        return self.id

    def get_file_name(self):
        return self.file

    def get_period(self):
        return self.period
                 

class VDFPeriod:
    
    def __init__(self, id, alpha=0.15, beta=4, mu=1000,
                 fftt=0, cap=99999, phf=-1):
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

        int_arr_node = ctypes.c_int * base.node_size
        double_arr_node = ctypes.c_double * base.node_size

        self.node_predecessor = int_arr_node(*node_preds)
        self.link_predecessor = int_arr_node(*link_preds)
        self.node_label_cost = double_arr_node(*node_lables)
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

    def get_demand_period(self):
        return self.demand_period

    def get_orig_nodes(self):
        for i in self.orig_nodes:
            yield i

    # the following eight are shared by all SPNetworks
    # network topology
    def get_node_size(self):
        return self.base.get_node_size()

    def get_link_size(self):
        return self.base.get_link_size()

    def get_node_list(self):
        return self.base.get_node_list()

    def get_link_list(self):
        return self.base.get_link_list()

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

    def get_link_costs(self):
        return self.base.get_link_costs()

    # the following four are unique to each SPNetwork 
    def get_node_preds(self):
        return self.node_predecessor

    def get_link_preds(self):
        return self.link_predecessor

    def get_node_label_costs(self):
        return self.node_label_cost

    def get_queue_next(self):
        return self.queue_next


class Assignment:
    
    def __init__(self):
        self.agent_types = []
        self.demand_periods = []
        # 4-d array
        self.column_pool = {}
        self.demands = {}
        self.network = None
        self.spnetworks = []
        self.memory_blocks = 4
    
    def get_agent_type_count(self):
        return len(self.agent_types)

    def get_demand_period_count(self):
        return len(self.demand_periods)

    def get_agent_types(self):
        for at in self.agent_types:
            yield at

    def get_demand_periods(self):
        for dp in self.demand_periods:
            yield dp

    def get_network(self):
        return self.network

    def get_nodes(self):
        return self.network.node_list

    def get_links(self):
        return self.network.link_list

    def get_zones(self):
        return self.network.zones

    def get_column_pool(self):
        return self.column_pool

    def get_agent_orig_node_id(self, agent_id):
        return self.network.get_agent_orig_node_id(agent_id)

    def get_agent_dest_node_id(self, agent_id):
        return self.network.get_agent_dest_node_id(agent_id)

    def get_agent_node_path(self, agent_id):
        return self.network.get_agent_node_path(agent_id)

    def get_agent_link_path(self, agent_id):
        return self.network.get_agent_link_path(agent_id)

    def find_path_for_agents(self):
        find_path_for_agents(self.network, self.column_pool)

    def find_shortest_path(self, from_node_id, to_node_id, seq_type='node'):
        return find_shortest_path(self.network, from_node_id, 
                                  to_node_id, seq_type='node')

    def perform_network_assignment(self, assignment_mode, iter_num, column_update_num):
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

        for at in self.get_agent_types():
            for dp in self.get_demand_periods():
                # z is zone id starting from 1
                for z in self.network.zones:
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
                        if (at.get_id(), dp.get_id(), m) not in spvec.keys():
                            spvec[(at.get_id(), dp.get_id(), m)] = SPNetwork(
                                self.network, at, dp
                            )
                        else:
                            sp = spvec[(at.get_id(), dp.get_id(), m)]
                        sp.orig_zones.append(z)
                        sp.add_orig_nodes(self.network.get_nodes_from_zone(z))
                        for node_id in self.network.get_nodes_from_zone(z):
                            sp.node_id_to_no[node_id] = (
                                self.network.get_node_no(node_id)
                            )