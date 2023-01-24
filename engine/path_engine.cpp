/**
 * The following deque implementations are inspired by the efficient implementation
 * from Dr. Hillel Bar-Gera
 *
 *     http://www.bgu.ac.il/~bargera/tntp/
 *     http://www.bgu.ac.il/~bargera/tntp/FW.zip
 *
 * Similar implementations can be also found in DYNASMART system designed by Dr. Hani Mahmassani and
 * DTALite by Dr. Xuesong Zhou.
 *
 * shortest_path() and shortest_path_n() enhance Bar-Gera's implementation by removing its duplicate
 * checks on empty deque. shortest_path_n() further improves shortest_path() by making better use of
 * stack memory (i.e., define cur_node, deque_head, and deque_tail within the for loop), which features
 * THE MOST efficient deque implementation of the modified label correcting (MLC) algorithm.
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
void shortest_path(int orig_node,
                   int node_size,
                   const int* from_nodes,
                   const int* to_nodes,
                   const int* first_link_from,
                   const int* last_link_from,
                   const int* sorted_links,
                   const wchar_t** allowed_uses,
                   const double* link_cost,
                   double* label_costs,
                   int* node_preds,
                   int* link_preds,
                   int* deque_next,
                   const char mode,
                   int depart_time,
                   int first_thru_node)
{
    // construct and initialize the following two on the first call only
    static constexpr int nullnode = -1, was_in_deque = -7;

    for (int node_no = 0; node_no < node_size; ++node_no)
    {
        // dueue_next is the scan eligible list for active nodes in label correcting
        deque_next[node_no] = nullnode;
        label_costs[node_no] = INT_MAX;
        link_preds[node_no] = nullnode;
        node_preds[node_no] = nullnode;
    }

    int cur_node = orig_node;
    int deque_head = nullnode;
    int deque_tail = nullnode;
    label_costs[cur_node] = depart_time;
    deque_next[cur_node] = was_in_deque;

    // label correcting
    while (true)
    {
        // filter out the TAZ based centroids
        if (cur_node >= first_thru_node || cur_node == orig_node)
        {
            for (int k = first_link_from[cur_node]; k < last_link_from[cur_node]; ++k)
            {
                int link = sorted_links[k];
                int new_node = to_nodes[link];

                /**
                 * if mode == 'a', we are doing static shortest path calculation using distance and
                 * all links shall be considered; otherwise, mode shall be in link's allowed uses or
                 * the allowed uses are for all modes (i.e., a)
                 */
                if (mode != 'a'
                    && !wcschr(allowed_uses[link], mode)
                    && !wcschr(allowed_uses[link], 'a'))
                    continue;

                double new_cost = label_costs[cur_node] + link_cost[link];
                if (label_costs[new_node] > new_cost)
                {
                    label_costs[new_node] = new_cost;
                    link_preds[new_node] = link;
                    node_preds[new_node] = from_nodes[link];

                    /**
                     * three cases
                     *
                     * case i: new_node was in deque before, add it to the begin of deque
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

void shortest_path_n(int orig_node,
                     int node_size,
                     const int* from_nodes,
                     const int* to_nodes,
                     const int* first_link_from,
                     const int* last_link_from,
                     const int* sorted_links,
                     const wchar_t** allowed_uses,
                     const double* link_costs,
                     double* label_costs,
                     int* node_preds,
                     int* link_preds,
                     int* deque_next,
                     const wchar_t* mode,
                     int max_label_cost,
                     int last_thru_node,
                     int depart_time)
{
    // construct and initialize the following three on the first call only
    static constexpr int nullnode = -1, was_in_deque = -7;
    static constexpr wchar_t all_mode[] = L"all";

    for (int node_no = 0; node_no < node_size; ++node_no)
    {
        // dueue_next is the scan eligible list for active nodes in label correcting
        deque_next[node_no] = nullnode;
        label_costs[node_no] = max_label_cost;
        link_preds[node_no] = nullnode;
        node_preds[node_no] = nullnode;
    }

    label_costs[orig_node] = depart_time;
    deque_next[orig_node] = was_in_deque;

    // label correcting
    for(int cur_node = orig_node, deque_head = nullnode, deque_tail = nullnode;;)
    {
        // filter out the TAZ based centroids
        if (cur_node <= last_thru_node || cur_node == orig_node)
        {
            for (int k = first_link_from[cur_node]; k < last_link_from[cur_node]; ++k)
            {
                int link = sorted_links[k];
                int new_node = to_nodes[link];

                /**
                 * if mode == 'a', we are doing static shortest path calculation using distance and
                 * all links shall be considered; otherwise, mode shall be in link's allowed uses or
                 * the allowed uses are for all modes (i.e., a)
                 */
                if (wcscmp(mode, all_mode) != 0
                    && !wcsstr(allowed_uses[link], mode)
                    && !wcsstr(allowed_uses[link], all_mode))
                    continue;

                double new_cost = label_costs[cur_node] + link_costs[link];
                if (label_costs[new_node] > new_cost)
                {
                    label_costs[new_node] = new_cost;
                    link_preds[new_node] = link;
                    node_preds[new_node] = from_nodes[link];

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