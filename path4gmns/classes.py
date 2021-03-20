import ctypes

from .path import MAX_LABEL_COST


_NUM_OF_SECS_PER_SIMU_INTERVAL = 6 

MIN_OD_VOL = 0.000001
MAX_TIME_PERIODS = 1
MAX_AGNET_TYPES = 1


class Node:         
    """ 
    external_node_id: the id of node
    node_seq_no: the index of the node and we call the node by its index
    
    we use g_internal_node_seq_no_dict(id to index) and 
    g_external_node_id_dict(index to id) to map them
    """

    def __init__(self, node_seq_no, external_node_id, zone_id): 
        """ the attribute of node  """ 
        self.node_seq_no = node_seq_no
        self.external_node_id = external_node_id
        self.outgoing_link_list = []
        self.incoming_link_list = []
        self.zone_id = zone_id
        self.coord_x = 0
        self.coord_y = 0

    def has_outgoing_links(self):
        return len(self.outgoing_link_list) > 0

    def get_zone_id(self):
        return self.zone_id

    def get_node_id(self):
        return self.external_node_id

    def get_node_no(self):
        return self.node_seq_no

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
                 vdf_alpha=0.15,
                 vdf_beta=4):   
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
        self.bpr_alpha = vdf_alpha
        self.bpr_beta = vdf_beta
        self.cost = self.free_flow_travel_time_in_min
        self.flow_volume = 0
        # add for CG
        self.toll = 0
        self.route_choice_cost = 0
        self.travel_time_by_period = [0] * MAX_TIME_PERIODS
        self.flow_vol_by_period = [0] * MAX_TIME_PERIODS
        self.vol_by_period_by_at = [
            [0] * MAX_TIME_PERIODS for i in range(MAX_AGNET_TYPES)
        ]
        # self.queue_length_by_slot = [0] * MAX_TIME_PERIODS
        self.vdfperiods = [VDFPeriod(i) for i in range(MAX_TIME_PERIODS)]
        self.travel_marginal_cost_by_period = [
            [0] * MAX_TIME_PERIODS for i in range(MAX_AGNET_TYPES)
        ]
        self._setup_vdfperiod()

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

    def _setup_vdfperiod(self):
        for tau in range(MAX_TIME_PERIODS):
            vp = self.vdfperiods[tau]
            vp.capacity = self.link_capacity
            vp.fftt = self.free_flow_travel_time_in_min
            

class Network:
    
    def __init__(self):
        self.node_list = []
        self.link_list = []
        self.agent_list = []
        self.node_size = 0
        self.link_size = 0
        self.agenet_size = 0
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
        self.tau = 0
        self.agent_type = 0
        self.column_pool = {}
        self.has_capi_allocated = False

    def update(self):
        self.node_size = len(self.node_list)
        self.link_size = len(self.link_list)
        self.agenet_size = len(self.agent_list)
        self.zones = self.zone_to_nodes_dict.keys()

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


# not used in the current implementation
# this is for future multi-demand-period and multi-agent-type implementation
class Assignment:
    
    def __init__(self):
        # 4-d array
        self.column_pool = None


class VDFPeriod:
    
    def __init__(self, id):
        self.id = id
        self.marginal_base = 1
        # the following four have been defined in class Link
        # they should be exactly the same with those in the corresponding link
        self.alpha = 0.15
        self.beta = 4
        self.capacity = 99999
        # free flow travel time
        self.fftt = 0
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