from .colgen import _update_link_travel_time_and_cost


__all__ = ['perform_simple_simulation']


def perform_simple_simulation(ui):
    A = ui._base_assignment
    links = A.get_links()
    nodes = A.get_nodes()

    A.initialize_simulation()
    _update_link_travel_time_and_cost(links)

    cum_arr = 0
    cum_dep = 0

    num = A.get_simu_interval_num_per_minute()
    for i in A.get_simulation_intervals():
        if i % num == 0:
            print(
                f'simu time = {i/num} min'
                f'CA = {cum_arr}'
                f'CD = {cum_dep}'
            )

        if i > 0:
            for link in links:
                link.cum_arr[i] = link.cum_arr[i-1]
                link.cum_dep[i] = link.cum_dep[i-1]

        if A.have_dep_agents(i):
            for a_no in A.get_td_agents(i):
                a = A.network._get_agent(a_no)
                path = a.link_path
                if path is None:
                    continue

                # link path is in reverse order
                first_link_no = path[-1]
                links[first_link_no].cum_arr[i] += 1
                links[first_link_no].entr_queue.append(a_no)
                cum_arr +=1

        for link in links:
            while link.entr_queue:
                a_no = link.entr_queue.pop_left()
                link.exit_queue_append(a_no)
                agent = A.network._get_agent(a_no)
                t = link.get_period_travel_time(0)
                agent.update_dep_time(t)

        for node in nodes:
            m = node.get_incoming_link_num()
            for j in range(m):
                pos = (i + j) % m
                link = node.incoming_links[pos]

                while link.outflow_cap[i] and link.exit_queue:
                    a_no = link.exit_queue.pop_left()
                    agent = A.network._get_agent(a_no)

                    if agent.get_curr_dep_interval() > i:
                        break

                    if agent.reached_last_link():
                        link.exit_queue.pop_left()
                        link.cum_dep[i] +=1
                        cum_dep += 1
                    else:
                        link.exit_queue.pop_left()
                        link_no = agent.get_next_link_no()
                        link_ = links[link_no]
                        link_.entr_queue.append(a_no)
                        agent.set_dep_time(i)
                        # set up arrival time for the next link, i.e., link_
                        agent.set_arr_time(i, 1)
                        
                        actual_tt = i - agent.get_arr_time()
                        waiting_t = actual_tt - link.get_period_travel_time(0)
                        minute = agent.get_arr_time() // A.simu_interval
                        link.update_waiting_time(minute, waiting_t)
                        link.cum_dep[i] += 1
                        link_.cum_arr[i] += 1

                    agent.increment_link_pos()
                    link.outflow_cap[i] -= 1