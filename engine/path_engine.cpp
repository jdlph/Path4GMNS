#include "path_engine.h"
#include <cstring>

/**
 * The following deque implementation is motivated by and modified from the efficient implementiation by Dr. Hillel Bar-Gera
 *
 *     http://www.bgu.ac.il/~bargera/tntp/
 *     http://www.bgu.ac.il/~bargera/tntp/FW.zip
 *
 * Similar implementations can be also found in DYNASMART system designed by Dr. Hani Mahmassani and the original code of DTALite by Dr. Xuesong Zhou
 *
 * With constexpr, it is a C++ function (which requires C++11 or higher) rather than a pure C function
 * Follow C++ coding style (++i rather than i++) and the {} style in AgentLite
 */
void shortest_path(int o_node_no,
                   int node_size,
                   const int* from_node_no_arr,
                   const int* to_node_no_arr,
                   const int* first_link_from,
                   const int* last_link_from,
                   const int* sorted_link_no_arr,
                   const wchar_t** allowed_uses,
                   const double* link_cost,
                   double* label_cost,
                   int* node_pred,
                   int* link_pred,
                   int* deque_next,
                   const char mode,
                   int departure_time,
                   int first_thru_node)
{
    // construct and initialize the following three on the first call only
    static constexpr int invalid = -1, was_in_deque = -7;
    // used t filter out the TAZ based centriods
    // static constexpr int first_thru_node = 0;

    // initialization
    for (int node_no = 0; node_no < node_size; ++node_no)
    {
        // dueue_next is the implementation of scan eligible list for active nodes in label correcting
        deque_next[node_no] = invalid;
        // label cost, make it consistent with the python implemenation
        label_cost[node_no] = 10000;
        link_pred[node_no] = invalid;
        node_pred[node_no] = invalid;
    }

    int current_node, deque_head, deque_tail;

    // SEList initialization
    current_node = o_node_no;
    label_cost[current_node] = departure_time;
    deque_next[current_node] = was_in_deque;
    deque_head = deque_tail = invalid;

    // label correcting
    while (current_node != invalid && current_node != was_in_deque)
    {
        if (current_node >= first_thru_node || current_node == o_node_no)
        {
            for (int k = first_link_from[current_node]; k < last_link_from[current_node]; ++k)
            {
                int link_seq_no = sorted_link_no_arr[k];
                int new_node = to_node_no_arr[link_seq_no];

                // mode shall be in link's allowed uses or the allowed uses are for all modes (i.e., a)
                if (!wcschr(allowed_uses[link_seq_no], mode) && !wcschr(allowed_uses[link_seq_no], 'a'))
                    continue;

                double new_cost = label_cost[current_node] + link_cost[link_seq_no];
                if (label_cost[new_node] > new_cost)
                {
                    label_cost[new_node] = new_cost;
                    link_pred[new_node] = link_seq_no;
                    node_pred[new_node] = from_node_no_arr[link_seq_no];

                    // If the new node_indiex was in the queue before, add it as the first in the queue.
                    if (deque_next[new_node] == was_in_deque)
                    {
                        deque_next[new_node] = deque_head;
                        deque_head = new_node;

                        if (deque_tail == invalid)
                            deque_tail = new_node;
                    }
                    // If the new node_indiex is not in the queue, and wasn't there before, add it at the end of the queue.
                    else if (deque_next[new_node] == invalid && new_node != deque_tail)
                    {
                        if (deque_tail != invalid)
                        {
                            // deuqe is not empty
                            deque_next[deque_tail] = new_node;
                            deque_tail = new_node;
                        }
                        else
                        {
                            // the queue is empty, initialize it.
                            deque_head = deque_tail = new_node;
                            deque_next[deque_tail] = invalid;
                        }
                    }
                    // If the new node_indiex is in the queue, just leave it there. (Do nothing)
                }
            }
        }

        // Get the first node_indiex out of the queue, and use it as the current node_indiex.
        current_node = deque_head;
        if (current_node == invalid || current_node == was_in_deque)
            break;

        deque_head = deque_next[current_node];
        deque_next[current_node] = was_in_deque;
        if (deque_tail == current_node)
            deque_tail = invalid;
    }
}