#pragma once

#ifdef _WIN32
#define SSSP_API __declspec(dllexport)
#else
#define SSSP_API
#endif

extern "C" SSSP_API void shortest_path(const int o_node_no, const int node_size,
				   					   const int* from_node_no_arr, const int* to_node_no_arr, 
				   					   const int* first_link_from, const int* last_link_from, 
									   const int* sorted_link_no_arr, const double* link_cost,
									   double* label_cost, int* node_pred, 
									   int* link_pred, int* deque_next);