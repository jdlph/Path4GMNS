__all__ = ['perform_simple_simulation']


def perform_simple_simulation(ui):
    A = ui._base_assignment
    A.initialize_simulation()

    links = A.get_links()
    nodes = A.get_nodes()

    cum_arr = cum_dep = 0

    # number of simulation intervals in one minute (60s)
    num = 60 // A.get_simu_resolution()
    for i in range(A.get_total_simu_intervals()):
        if i % num == 0:
            print(f'simu time = {i/num} min, CA = {cum_arr}, CD = {cum_dep}')

        if i > 0:
            for link in links:
                link.cum_arr[i] = link.cum_arr[i-1]
                link.cum_dep[i] = link.cum_dep[i-1]

        if A.have_dep_agents(i):
            for a_no in A.get_td_agents(i):
                a = A.get_agent(a_no)
                if a.link_path is None:
                    continue

                # retrieve the first link given link path is in reverse order
                link_no = a.link_path[-1]
                link = links[link_no]
                link.cum_arr[i] += 1
                link.entr_queue.append(a_no)
                cum_arr +=1

        for link in links:
            while link.entr_queue:
                a_no = link.entr_queue.popleft()
                agent = A.get_agent(a_no)
                link.exit_queue.append(a_no)
                tt = int(link.get_period_travel_time(0) * num) + 1
                agent.update_dep_time(tt)

        for node in nodes:
            m = node.get_incoming_link_num()
            for j in range(m):
                # randomly select the first link
                pos = (i + j) % m
                link = node.incoming_links[pos]

                while link.outflow_cap[i] and link.exit_queue:
                    a_no = link.exit_queue[0]
                    agent = A.get_agent(a_no)

                    if agent.get_curr_dep_interval() > i:
                        break

                    if agent.reached_last_link():
                        link.cum_dep[i] +=1
                        cum_dep += 1
                    else:
                        link_no = agent.get_next_link_no()
                        next_link = links[link_no]
                        next_link.entr_queue.append(a_no)
                        agent.set_dep_time(i)
                        # set up arrival time for the next link, i.e., next_link
                        agent.set_arr_time(i, 1)

                        actual_tt = i - agent.get_arr_time()
                        waiting_t = actual_tt - link.get_period_travel_time(0)
                        minute = agent.get_arr_time() // A.get_simu_resolution()
                        link.update_waiting_time(minute, waiting_t)
                        link.cum_dep[i] += 1
                        next_link.cum_arr[i] += 1

                    agent.increment_link_pos()
                    # remove agent from exit queue
                    link.exit_queue.popleft()
                    link.outflow_cap[i] -= 1