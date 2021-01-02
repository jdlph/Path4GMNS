import ctypes
import numpy
import collections
import heapq


# for initialization in shortest path calculation
MAX_LABEL_COST_IN_SHORTEST_PATH = 10000


# note that the following path is the PATH at RUN TIME when imported as package
# it is NOT the path when used as offline module.
# see data_files in setup.py for details.
_cdll = ctypes.cdll.LoadLibrary(r"./bin/libstalite.dll")
# set up the argument types for the shortest path function in dll.
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


def _optimal_label_correcting_CAPI(G, origin_node, destination_node=1):
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


def _single_source_shortest_path_fifo(G, origin_node):
    """ FIFO implementation of MLC using built-in list and indicator array
    
    The caller is responsible for initializing node_label_cost, 
    node_predecessor, and link_predecessor.
    """
    # node status array
    status = [0] * G.node_size
    # scan eligible list
    SEList = []  
    SEList.append(origin_node)

    while SEList:
        from_node = SEList.pop(0)
        status[from_node] = 0
        for link in G.node_list[from_node].outgoing_link_list:
            to_node = link.to_node_seq_no 
            new_to_node_cost = (G.node_label_cost[from_node] 
                                + G.link_cost_array[link.link_seq_no])
            # we only compare cost at the downstream node ToID 
            # at the new arrival time t
            if new_to_node_cost < G.node_label_cost[to_node]:
                # update cost label and node/time predecessor
                G.node_label_cost[to_node] = new_to_node_cost
                # pointer to previous physical node index 
                # from the current label at current node and time
                G.node_predecessor[to_node] = from_node 
                # pointer to previous physical node index
                # from the current label at current node and time
                G.link_predecessor[to_node] = link.link_seq_no 
                if not status[to_node]:
                    SEList.append(to_node)
                    status[to_node] = 1


def _single_source_shortest_path_deque(G, origin_node):
    """ Deque implementation of MLC using deque list and indicator array
    
    The caller is responsible for initializing node_label_cost, 
    node_predecessor, and link_predecessor.

    Adopted and modified from
    https://github.com/jdlph/shortest-path-algorithms
    """
    # node status array
    status = [0] * G.node_size
    # scan eligible list
    SEList = collections.deque()
    SEList.append(origin_node)

    while SEList:
        from_node = SEList.popleft()
        status[from_node] = 2
        for link in G.node_list[from_node].outgoing_link_list:
            to_node = link.to_node_seq_no  
            new_to_node_cost = (G.node_label_cost[from_node] 
                                + G.link_cost_array[link.link_seq_no])
            # we only compare cost at the downstream node ToID
            # at the new arrival time t
            if new_to_node_cost < G.node_label_cost[to_node]:
                # update cost label and node/time predecessor
                G.node_label_cost[to_node] = new_to_node_cost
                # pointer to previous physical node index 
                # from the current label at current node and time
                G.node_predecessor[to_node] = from_node
                # pointer to previous physical node index 
                # from the current label at current node and time
                G.link_predecessor[to_node] = link.link_seq_no
                if status[to_node] != 1:
                    if status[to_node] == 2:
                        SEList.appendleft(to_node)
                    else:
                        SEList.append(to_node)
                    status[to_node] = 1


def _single_source_shortest_path_dijkstra(G, origin_node):
    """ Simplified heap-Dijkstra's Algorithm using heapq
    
    The caller is responsible for initializing node_label_cost, 
    node_predecessor, and link_predecessor.

    Adopted and modified from
    https://github.com/jdlph/shortest-path-algorithms
    """
    # scan eligible list
    SEList = []
    heapq.heapify(SEList)
    heapq.heappush(SEList, (G.node_label_cost[origin_node], origin_node))

    while SEList:
        (label_cost, from_node) = heapq.heappop(SEList)
        for link in G.node_list[from_node].outgoing_link_list:
            to_node = link.to_node_seq_no
            new_to_node_cost = label_cost + G.link_cost_array[link.link_seq_no]
            # we only compare cost at the downstream node ToID 
            # at the new arrival time t
            if new_to_node_cost < G.node_label_cost[to_node]:
                # update cost label and node/time predecessor
                G.node_label_cost[to_node] = new_to_node_cost
                # pointer to previous physical node index 
                # from the current label at current node and time
                G.node_predecessor[to_node] = from_node 
                # pointer to previous physical node index 
                # from the current label at current node and time
                G.link_predecessor[to_node] = link.link_seq_no
                heapq.heappush(SEList, (G.node_label_cost[to_node], to_node))


def single_source_shortest_path(G, origin_node, engine_type='c',
                                sp_algm='deque'):
    if engine_type.lower() == 'c':
        G.allocate_for_CAPI()
        _optimal_label_correcting_CAPI(G, origin_node)
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
                for link in G.node_list[from_node].outgoing_link_list:
                    to_node = link.to_node_seq_no 
                    new_to_node_cost = (G.node_label_cost[from_node] 
                                        + G.link_cost_array[link.link_seq_no])
                    # we only compare cost at the downstream node ToID 
                    # at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index 
                        # from the current label at current node and time
                        G.node_predecessor[to_node] = from_node 
                        # pointer to previous physical node index
                        # from the current label at current node and time
                        G.link_predecessor[to_node] = link.link_seq_no 
                        if not status[to_node]:
                            SEList.append(to_node)
                            status[to_node] = 1

        elif sp_algm.lower() == 'deque':
            SEList = collections.deque()
            SEList.append(origin_node)

            while SEList:
                from_node = SEList.popleft()
                status[from_node] = 2
                for link in G.node_list[from_node].outgoing_link_list:
                    to_node = link.to_node_seq_no  
                    new_to_node_cost = (G.node_label_cost[from_node] 
                                        + G.link_cost_array[link.link_seq_no])
                    # we only compare cost at the downstream node ToID
                    # at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index 
                        # from the current label at current node and time
                        G.node_predecessor[to_node] = from_node
                        # pointer to previous physical node index 
                        # from the current label at current node and time
                        G.link_predecessor[to_node] = link.link_seq_no
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
            heapq.heappush(
                SEList, 
                (G.node_label_cost[origin_node], origin_node)
            )

            while SEList:
                (label_cost, from_node) = heapq.heappop(SEList)
                for link in G.node_list[from_node].outgoing_link_list:
                    to_node = link.to_node_seq_no
                    new_to_node_cost = (label_cost 
                                        + G.link_cost_array[link.link_seq_no])
                    # we only compare cost at the downstream node ToID 
                    # at the new arrival time t
                    if new_to_node_cost < G.node_label_cost[to_node]:
                        # update cost label and node/time predecessor
                        G.node_label_cost[to_node] = new_to_node_cost
                        # pointer to previous physical node index 
                        # from the current label at current node and time
                        G.node_predecessor[to_node] = from_node 
                        # pointer to previous physical node index 
                        # from the current label at current node and time
                        G.link_predecessor[to_node] = link.link_seq_no
                        heapq.heappush(
                            SEList, 
                            (G.node_label_cost[to_node], to_node)
                        )
        
        else:
            raise Exception('Please choose correct shortest path algorithm: '
                            +'fifo or deque or dijkstra')
        # end of sp_algm == 'fifo':


def output_path_sequence(G, from_node_id, to_node_id, type='node'):
    """ output shortest path in terms of node sequence or link sequence
    
    Note that this function returns GENERATOR rather than list.
    """
    path = [] 
    current_node_seq_no = G.internal_node_seq_no_dict[to_node_id]
    
    if type.lower() == 'node':
        # retrieve the sequence backwards
        while current_node_seq_no >= 0:  
            path.append(current_node_seq_no)
            current_node_seq_no = G.node_predecessor[current_node_seq_no]
        # reverse the sequence
        for node_seq_no in reversed(path):
            yield G.external_node_id_dict[node_seq_no]

    elif type.lower() == 'node':
        # retrieve the sequence backwards
        current_link_seq_no = G.link_predecessor[current_node_seq_no]
        while current_link_seq_no >= 0:
            path.append(current_link_seq_no)
            current_link_seq_no = G.link_predecessor[current_node_seq_no]
        # reverse the sequence
        for link_seq_no in reversed(path):
            yield link_seq_no


def find_shortest_path(G, from_node_id, to_node_id, seq_type='node'):
    if from_node_id not in G.internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {from_node_id} not in the network")
    if to_node_id not in G.internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {to_node_id} not in the network")

    single_source_shortest_path(G, from_node_id, engine_type='c')
    return list(output_path_sequence(G, from_node_id, to_node_id, seq_type))


# def all_pairs_shortest_paths(G, engine_type='c', sp_algm='deque'):
#     for i in G.internal_node_seq_no_dict.keys():
#         single_source_shortest_path(G, i, engine_type, sp_algm)