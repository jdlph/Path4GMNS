""" Find shortest path given a from node and a to node

Two path engines are provided:
1. C++ engine which is a special implementation of the deque implementation in
   CPP and built into libstalite.dll.
2. Python engine which provides three implementations: FIFO, Deque, and 
   Dijkstra. The default is deque.

The code is adopted and modified from 
https://github.com/asu-trans-ai-lab/DTALite 
"""


import ctypes
import numpy 

from .path import MAX_LABEL_COST_IN_SHORTEST_PATH


class Node:         
    """ external_node_id: the id of node
    node_seq_no: the index of the node and we call the node by its index
    
    we use g_internal_node_seq_no_dict(id to index) and 
    g_external_node_id_dict(index to id) to map them
    """

    def __init__(self, node_seq_no, external_node_id, zone_id): 
        """ the attribute of node  """ 
        self.node_seq_no = node_seq_no
        self.external_node_id = int(external_node_id)
        self.outgoing_link_list = list()
        self.incoming_link_list = list()
        if len(zone_id) == 0:
            self.zone_id = -1
        else:    
            self.zone_id = int(zone_id)
        

class Link:

    def __init__(self, link_seq_no, from_node_no, to_node_no, 
                 from_node_id, to_node_id, length, lanes,
                 free_speed, capacity, link_type, VDF_alpha, VDF_beta):   
        """ the attribute of link """
        self.link_seq_no = link_seq_no
        self.from_node_seq_no = from_node_no
        self.to_node_seq_no = to_node_no
        self.external_from_node = int(from_node_id)
        self.external_to_node = int(to_node_id)
        # 1:one direction 2:two way
        self.type = int(link_type)
        self.lanes = int(lanes)
        self.BPR_alpha = float(VDF_alpha)
        self.BPR_beta = float(VDF_beta)
        self.flow_volume = 0
        # capacity is lane capacity per hour
        self.link_capacity = float(capacity) * int(lanes)
        # length is mile or km
        self.length = float(length) 
        # length:km, free_speed: km/h
        self.free_flow_travel_time_in_min = self.length / max(0.001,int(free_speed)) * 60  
        self.cost = self.free_flow_travel_time_in_min


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
        self.node_label_cost = []
        self.node_predecessor = []
        self.link_predecessor = []
        self._count = 0

    def update(self):
        self.node_size = len(self.node_list)
        self.link_size = len(self.link_list)
        self.agenet_size = len(self.agent_list)   

    def allocate_for_CAPI(self):
        # execute only on the first call
        if self._count >= 1:
            return

        # initialization for predecessors and label costs
        self.node_predecessor = numpy.full(self.node_size, -1, numpy.int32)
        self.link_predecessor = numpy.full(self.node_size, -1, numpy.int32)
        self.node_label_cost = numpy.full(self.node_size, 
                                          MAX_LABEL_COST_IN_SHORTEST_PATH,
                                          numpy.float64)

        # initialize from_node_no_array, to_node_no_array, and link_cost_array
        self.from_node_no_array = [
            self.link_list[j].from_node_seq_no for j in range(self.link_size)
        ]
        self.to_node_no_array = [
            self.link_list[j].to_node_seq_no for j in range(self.link_size)
        ]
        self.link_cost_array = [
            self.link_list[j].cost for j in range(self.link_size)
        ]

        # convert the above three into numpy array to be passed as 
        # pointers to dll
        self.from_node_no_array = numpy.array(self.from_node_no_array, 
                                              numpy.int32)
        self.to_node_no_array = numpy.array(self.to_node_no_array, numpy.int32)
        self.link_cost_array = numpy.array(self.link_cost_array, numpy.float64)
        
        # initialize others as numpy arrays directly
        self.queue_next = numpy.full(self.node_size, 0, numpy.int32)
        self.FirstLinkFrom = numpy.full(self.node_size, -1, numpy.int32)
        self.LastLinkFrom = numpy.full(self.node_size, -1, numpy.int32)
        self.sorted_link_no_vector = numpy.full(self.link_size, -1, 
                                                numpy.int32)

        # count the size of outgoing links for each node
        node_OutgoingLinkSize = [0] * self.node_size
        for j in range(self.link_size):
            node_OutgoingLinkSize[self.link_list[j].from_node_seq_no] += 1

        cumulative_count = 0
        for i in range(self.node_size):
            self.FirstLinkFrom[i] = cumulative_count
            self.LastLinkFrom[i] = self.FirstLinkFrom[i] + node_OutgoingLinkSize[i]
            cumulative_count += node_OutgoingLinkSize[i]

        # reset the counter # need to construct sorted_link_no_vector
        # we are converting a 2 dimensional dynamic array to a fixed size 
        # one-dimisonal array, with the link size 
        for i in range(self.node_size):
            node_OutgoingLinkSize[i] = 0

        # count again the current size of outgoing links for each node
        for j in range(self.link_size):
            # fetch the curent from node seq no of this link
            from_node_seq_no = self.link_list[j].from_node_seq_no
            # j is the link sequence no in the original link block
            k = (self.FirstLinkFrom[from_node_seq_no] 
                 + node_OutgoingLinkSize[from_node_seq_no])
            self.sorted_link_no_vector[k] = j
            # continue to count, increase by 1
            node_OutgoingLinkSize[self.link_list[j].from_node_seq_no] += 1
        
        self._count += 1 