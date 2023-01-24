#ifndef GUARD_PATH_ENGINE_H
#define GUARD_PATH_ENGINE_H

#ifdef _WIN32
#define PATH_ENGINE_API __declspec(dllexport)
#else
#define PATH_ENGINE_API
#endif

extern "C" PATH_ENGINE_API void shortest_path(const int orig_node,
                                              const int node_size,
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
                                              const char mode = 'a',
                                              int depart_time = 0,
                                              int first_thru_node = 0);

extern "C" PATH_ENGINE_API void shortest_path_n(int orig_node,
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
                                                int depart_time = 0);

#endif