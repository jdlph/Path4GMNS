import ctypes
import numpy
import collections
import heapq


# =========================
# -*- data block define -*- 
# =========================
MAX_LABEL_COST_IN_SHORTEST_PATH = 10000


# set up the return type and argument types for the shortest path 
# function in dll.
_cdll = ctypes.cdll.LoadLibrary(r"../bin/libstalite.dll")
_cdll.shortest_path.argtypes = [
    ctypes.c_int, ctypes.c_int, 
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.float64),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),                                        
    ctypes.c_int, ctypes.c_int, 
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.int32),
    numpy.ctypeslib.ndpointer(dtype=numpy.float64)
]


def optimal_label_correcting_CAPI(G, origin_node, destination_node=1):
    """ input : origin_node,destination_node,departure_time
        output : the shortest path
    """
    o_node_no = G.internal_node_seq_no_dict[origin_node]
    d_node_no = G.internal_node_seq_no_dict[destination_node]

    if not G.node_list[o_node_no].outgoing_link_list:
        return
    
    _cdll.shortest_path(G.node_size, 
                        G.link_size, 
                        G.from_node_no_array,
                        G.to_node_no_array,
                        G.link_cost_array,
                        G.FirstLinkFrom,
                        G.LastLinkFrom,
                        G.sorted_link_no_vector, 
                        o_node_no,
                        d_node_no, 
                        G.node_predecessor,
                        G.link_predecessor,
                        G.queue_next,
                        G.node_label_cost)


def single_source_shortest_path(G, origin_node, engine_type='c',
                                sp_algm='deque'):
    if engine_type.lower() == 'c':
        G.allocate_for_CAPI()
        optimal_label_correcting_CAPI(G, origin_node)
    else:
        origin_node_no = G.internal_node_seq_no_dict[origin_node]
        
        if not G.node_list[origin_node].outgoing_link_list:
            return
        
        # Initialization for all nodes
        G.node_label_cost = [MAX_LABEL_COST_IN_SHORTEST_PATH] * G.node_size
        # pointer to previous node index from the current label at current node
        G.node_predecessor = [-1] * G.node_size
        # pointer to previous node index from the current label at current node
        G.link_predecessor = [-1] * G.node_size

        G.node_label_cost[origin_node_no] = 0
        status = [0] * G.node_size

        if sp_algm.lower() == 'fifo':
            # scan eligible list
            SEList = []  
            SEList.append(origin_node)

            while SEList:
                from_node = SEList.pop(0)
                status[from_node] = 0
                for k in range(len(G.node_list[from_node].outgoing_link_list)):
                    to_node = G.node_list[from_node].outgoing_link_list[k].to_node_seq_no 
                    new_to_node_cost = G.node_label_cost[from_node] + G.link_cost_array[G.node_list[from_node].outgoing_link_list[k].link_seq_no]
                    # we only compare cost at the downstream node ToID at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index from the current label at current node and time
                        G.node_predecessor[to_node] = from_node 
                        # pointer to previous physical node index from the current label at current node and time
                        G.link_predecessor[to_node] = G.node_list[from_node].outgoing_link_list[k].link_seq_no  
                        if not status[to_node]:
                            SEList.append(to_node)
                            status[to_node] = 1

        elif sp_algm.lower() == 'deque':
            SEList = collections.deque()
            SEList.append(origin_node)

            while SEList:
                from_node = SEList.popleft()
                status[from_node] = 2
                for k in range(len(G.node_list[from_node].outgoing_link_list)):
                    to_node = G.node_list[from_node].outgoing_link_list[k].to_node_seq_no 
                    new_to_node_cost = G.node_label_cost[from_node] + G.link_cost_array[G.node_list[from_node].outgoing_link_list[k].link_seq_no]
                    # we only compare cost at the downstream node ToID at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index from the current label at current node and time
                        G.node_predecessor[to_node] = from_node 
                        # pointer to previous physical node index from the current label at current node and time
                        G.link_predecessor[to_node] = G.node_list[from_node].outgoing_link_list[k].link_seq_no  
                        if status[to_node] != 1:
                            if status[to_node] == 2:
                                SEList.appendleft(to_node)
                            else:
                                SEList.append(to_node)
                            status[to_node] = 1

        elif sp_algm.lower() == 'dijkstra':
            # scan eligible list
            SEList = []
            heapq.heapify(SEList)
            heapq.heappush(SEList, (G.node_label_cost[origin_node], origin_node))

            while SEList:
                (label_cost, from_node) = heapq.heappop(SEList)
                for k in range(len(G.node_list[from_node].outgoing_link_list)):
                    to_node = G.node_list[from_node].outgoing_link_list[k].to_node_seq_no 
                    new_to_node_cost = label_cost + G.link_cost_array[G.node_list[from_node].outgoing_link_list[k].link_seq_no]
                    # we only compare cost at the downstream node ToID at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index from the current label at current node and time
                        G.node_predecessor[to_node] = from_node 
                        # pointer to previous physical node index from the current label at current node and time
                        G.link_predecessor[to_node] = G.node_list[from_node].outgoing_link_list[k].link_seq_no  
                        heapq.heappush(SEList, (G.node_label_cost[to_node], to_node))
        
        else:
            raise Exception('Please choose correct shortest path algorithm: '
                            +'fifo or deque or dijkstra')
        # end of sp_algm == 'fifo':


def output_path_sequence(G, from_node_id, to_node_id, type='node'):
    """ output shortest path in terms of node sequence or link sequence """
    path = [] 
    current_node_seq_no = G.internal_node_seq_no_dict[to_node_id]
    
    if type.lower() == 'node':
        while current_node_seq_no >= 0:  
            path.insert(0, current_node_seq_no)
            current_node_seq_no = G.node_predecessor[current_node_seq_no]
    elif type.lower() == 'node':
        current_link_seq_no = G.link_predecessor[current_node_seq_no]
        while current_link_seq_no >= 0:
            path.insert(0, current_link_seq_no)
            current_link_seq_no = G.link_predecessor[current_node_seq_no]
    
    return path


def find_shortest_path(G, from_node_id, to_node_id, 
                       engine_type='c', sp_algm='deque', seq_type='node'):
    if from_node_id not in G.internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {from_node_id} not in the network")
    if to_node_id not in G.internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {to_node_id} not in the network")

    single_source_shortest_path(G, from_node_id, engine_type, sp_algm)
    return output_path_sequence(G, from_node_id, to_node_id, seq_type)


# def all_pairs_shortest_paths(G, engine_type='c', sp_algm='deque'):
#     for i in G.internal_node_seq_no_dict.keys():
#         single_source_shortest_path(G, i, engine_type, sp_algm)