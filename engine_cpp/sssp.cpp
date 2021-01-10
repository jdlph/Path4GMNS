#include "sssp.h"

// Folllow C++ coding style (++i rather than i++) and be consistent with that in AgentLite
// even the following function can be consider as a pure C function.
void shortest_path(const int o_node_no, const int node_size, 
				   const int* from_node_no_arr, const int* to_node_no_arr, 
				   const int* first_link_from, const int* last_link_from, 
				   const int* sorted_link_no_arr, const double* link_cost,
				   double* label_cost, int* node_pred,
				   int* link_pred, int* deque_next)
{
    /*
	The following deque based implementation is motivated and adpated by the efficient implementiation by Dr. Hillel Bar-Gera from
		http://www.bgu.ac.il/~bargera/tntp/
		http://www.bgu.ac.il/~bargera/tntp/FW.zip

	Similar implementation can be also found at DYNASMART system design by Dr. Hani Mahmassani and original code in DTALite by Dr. Xuesong Zhou
	*/

	// construct and initialize the following three on the first call
	static const int INVALID = -1, WAS_IN_DEQUE = -7;
	// used t filter out the TAZ based centriods
	static const int FIRST_THRU_NODE = 0;  

	int node_indiex, current_node, new_node;
	int deque_head, deque_tail;

	//SEList_queue_next_vector is the implementation of scan eligible list for active nodes in label correcting 
	for (node_indiex = 0; node_indiex < node_size; ++node_indiex)
	{
		// scan eligible list
		deque_next[node_indiex] = INVALID;
		// label cost, make it consisent with the python implemenation
		label_cost[node_indiex] = 10000;  
		link_pred[node_indiex] = INVALID;
		node_pred[node_indiex] = INVALID;
	}

	//initialization 
	current_node = o_node_no;
	deque_next[current_node] = WAS_IN_DEQUE;
	link_pred[current_node] = INVALID;
	node_pred[node_indiex] = INVALID;
	label_cost[current_node] = 0.0;

	//SEList initialization
	deque_head = deque_tail = INVALID;

	//label correction scanning
	while ((current_node != INVALID) && (current_node != WAS_IN_DEQUE))
	{
		if (current_node >= FIRST_THRU_NODE || current_node == o_node_no)
		{
			for (int k = first_link_from[current_node]; k < last_link_from[current_node]; ++k) 
			{
				int link_seq_no = sorted_link_no_arr[k];
				new_node = to_node_no_arr[link_seq_no];

				double new_cost = label_cost[current_node] + link_cost[link_seq_no];
				if (label_cost[new_node] > new_cost)
				{
					label_cost[new_node] = new_cost;
					link_pred[new_node] = link_seq_no;
					node_pred[new_node] = from_node_no_arr[link_seq_no];

					// If the new node_indiex was in the queue before, add it as the first in the queue.
					if (deque_next[new_node] == WAS_IN_DEQUE)
					{
						deque_next[new_node] = deque_head;
						deque_head = new_node;

						if (deque_tail == INVALID)
							deque_tail = new_node;
					}
					// If the new node_indiex is not in the queue, and wasn't there before, add it at the end of the queue.
					else if (deque_next[new_node] == INVALID && new_node != deque_tail) 
					{
						if (deque_tail != INVALID) 
						{ 					
							// deuqe is not empty
							deque_next[deque_tail] = new_node;
							deque_tail = new_node;
						}
						else
						{			  
							// the queue is empty, initialize it.
							deque_head = deque_tail = new_node;
							deque_next[deque_tail] = INVALID;
						}
					}
					// If the new node_indiex is in the queue, just leave it there. (Do nothing)
				}
			}
		}

		// Get the first node_indiex out of the queue, and use it as the current node_indiex.
		current_node = deque_head;
		if ((current_node == INVALID) || (current_node == WAS_IN_DEQUE))
			break;

		deque_head = deque_next[current_node];
		deque_next[current_node] = WAS_IN_DEQUE;
		if (deque_tail == current_node)
			deque_tail = INVALID;
	}
}