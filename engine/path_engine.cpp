/**
 * The following deque implementations are inspired by the efficient implementation
 * from Dr. Hillel Bar-Gera
 *
 *     http://www.bgu.ac.il/~bargera/tntp/
 *     http://www.bgu.ac.il/~bargera/tntp/FW.zip
 *
 * shortest_path() and shortest_path_n() enhance the forgoing implementation by removing its duplicate
 * checks on empty deque. shortest_path_n() further improves shortest_path() by making better use of
 * stack memory (i.e., define cur_node, deque_head, and deque_tail within the for loop), which features
 * THE MOST efficient deque implementation of the modified label correcting (MLC) algorithm.
 *
 * Similar implementations can be also found in DYNASMART system designed by Dr. Hani Mahmassani and
 * the original code of DTALite by Dr. Xuesong Zhou.
 *
 * With constexpr, it is a C++ function (which requires C++11 or higher) rather than a pure C function.
 */

#include "path_engine.h"

#include <cstring>
#include <cwchar>
#include <climits>

using std::wcsstr;
using std::wcscmp;

// keep it as legacy support for other packages using this old engine
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
    // construct and initialize the following two on the first call only
    static constexpr int nullnode = -1, was_in_deque = -7;

    for (int node_no = 0; node_no < node_size; ++node_no)
    {
        // dueue_next is the scan eligible list for active nodes in label correcting
        deque_next[node_no] = nullnode;
        label_cost[node_no] = INT_MAX;
        link_pred[node_no] = nullnode;
        node_pred[node_no] = nullnode;
    }

    int cur_node = o_node_no;
    int deque_head = nullnode;
    int deque_tail = nullnode;
    label_cost[cur_node] = departure_time;
    deque_next[cur_node] = was_in_deque;

    // label correcting
    while (true)
    {
        // filter out the TAZ based centroids
        if (cur_node >= first_thru_node || cur_node == o_node_no)
        {
            for (int k = first_link_from[cur_node]; k < last_link_from[cur_node]; ++k)
            {
                int link_seq_no = sorted_link_no_arr[k];
                int new_node = to_node_no_arr[link_seq_no];

                /**
                 * if mode == 'a', we are doing static shortest path calculation using distance and
                 * all links shall be considered; otherwise, mode shall be in link's allowed uses or
                 * the allowed uses are for all modes (i.e., a)
                 */
                if (mode != 'a'
                    && !wcschr(allowed_uses[link_seq_no], mode)
                    && !wcschr(allowed_uses[link_seq_no], 'a'))
                    continue;

                double new_cost = label_cost[cur_node] + link_cost[link_seq_no];
                if (label_cost[new_node] > new_cost)
                {
                    label_cost[new_node] = new_cost;
                    link_pred[new_node] = link_seq_no;
                    node_pred[new_node] = from_node_no_arr[link_seq_no];

                    /**
                     * three cases
                     *
                     * case i:  new_node was in deque before, add it to the begin of deque
                     * case ii: new_node is not in the queue, and wasn't there before, add it to the end of deque
                     * case iii: new_node is in deque, do nothing
                     */
                    if (deque_next[new_node] == was_in_deque)
                    {
                        deque_next[new_node] = deque_head;
                        deque_head = new_node;

                        // deque is empty, initialize it.
                        if (deque_tail == nullnode)
                            deque_tail = new_node;
                    }
                    else if (deque_next[new_node] == nullnode && new_node != deque_tail)
                    {
                        deque_tail = new_node;

                        if (deque_tail == nullnode)
                        {
                            deque_head = new_node;
                            deque_next[deque_tail] = nullnode;
                        }
                        else
                            deque_next[deque_tail] = new_node;
                    }
                }
            }
        }

        // deque is empty, terminate the process
        if (deque_head < 0)
            break;

        // get the first node out of deque and use it as the current node
        cur_node = deque_head;
        deque_head = deque_next[cur_node];
        deque_next[cur_node] = was_in_deque;
        if (deque_tail == cur_node)
            deque_tail = nullnode;
    }
}

void shortest_path_n(int o_node_no,
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
                     const wchar_t* mode,
                     int max_label_cost,
                     int last_thru_node,
                     int departure_time)
{
    // construct and initialize the following three on the first call only
    static constexpr int nullnode = -1, was_in_deque = -7;
    static constexpr wchar_t all_mode[] = L"all";

    for (int node_no = 0; node_no < node_size; ++node_no)
    {
        // dueue_next is the scan eligible list for active nodes in label correcting
        deque_next[node_no] = nullnode;
        label_cost[node_no] = max_label_cost;
        link_pred[node_no] = nullnode;
        node_pred[node_no] = nullnode;
    }

    label_cost[o_node_no] = departure_time;
    deque_next[o_node_no] = was_in_deque;

    // label correcting
    for(int cur_node = o_node_no, deque_head = nullnode, deque_tail = nullnode;;)
    {
        // filter out the TAZ based centroids
        if (cur_node <= last_thru_node || cur_node == o_node_no)
        {
            for (int k = first_link_from[cur_node]; k < last_link_from[cur_node]; ++k)
            {
                int link_seq_no = sorted_link_no_arr[k];
                int new_node = to_node_no_arr[link_seq_no];

                /**
                 * if mode == 'a', we are doing static shortest path calculation using distance and
                 * all links shall be considered; otherwise, mode shall be in link's allowed uses or
                 * the allowed uses are for all modes (i.e., a)
                 */
                if (wcscmp(mode, all_mode) != 0
                    && !wcsstr(allowed_uses[link_seq_no], mode)
                    && !wcsstr(allowed_uses[link_seq_no], all_mode))
                    continue;

                double new_cost = label_cost[cur_node] + link_cost[link_seq_no];
                if (label_cost[new_node] > new_cost)
                {
                    label_cost[new_node] = new_cost;
                    link_pred[new_node] = link_seq_no;
                    node_pred[new_node] = from_node_no_arr[link_seq_no];

                    /**
                     * three cases
                     *
                     * case i:  new_node was in deque before, add it to the begin of deque
                     * case ii: new_node is not in the queue, and wasn't there before, add it to the end of deque
                     * case iii: new_node is in deque, do nothing
                     */
                    if (deque_next[new_node] == was_in_deque)
                    {
                        deque_next[new_node] = deque_head;
                        deque_head = new_node;

                        // deque is empty, initialize it.
                        if (deque_tail == nullnode)
                            deque_tail = new_node;
                    }
                    else if (deque_next[new_node] == nullnode && new_node != deque_tail)
                    {
                        deque_tail = new_node;

                        if (deque_tail == nullnode)
                        {
                            deque_head = new_node;
                            deque_next[deque_tail] = nullnode;
                        }
                        else
                            deque_next[deque_tail] = new_node;
                    }
                }
            }
        }

        // deque is empty, terminate the process
        if (deque_head < 0)
            break;

        // get the first node out of deque and use it as the current node
        cur_node = deque_head;
        deque_head = deque_next[cur_node];
        deque_next[cur_node] = was_in_deque;
        if (deque_tail == cur_node)
            deque_tail = nullnode;
    }
}