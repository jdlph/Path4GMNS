from math import max


def conduct_odme(column_pool, links, zones):
    delta = 0.05
    step_size = 0.01

    # k = (at, dp, oz, dz)
    for k, cv in column_pool.items():
        if cv.is_route_fixed():
            continue

        for col in cv.get_columns():
            vol = col.get_volume()
            path_gradient_cost = 0

            orig_zone = zones[k[2]]
            if orig_zone.prod_obs > 0:
                if not orig_zone.is_prod_obs_upper_bounded:
                    path_gradient_cost += orig_zone.est_prod_dev
                elif orig_zone.is_prod_obs_upper_bounded and orig_zone.est_prod_dev > 0:
                    path_gradient_cost += orig_zone.est_prod_dev

            dest_zone = zones[k[3]]
            if dest_zone.attr_obs > 0:
                if not dest_zone.is_attr_obs_upper_bounded:
                    path_gradient_cost += dest_zone.est_attr_dev
                elif dest_zone.is_attr_obs_upper_bounded and dest_zone.est_attr_dev > 0:
                    path_gradient_cost += dest_zone.est_attr_dev

            for i in col.links:
                link = links[i]
                if link.obs >= 1:
                    if not link.is_obs_upper_bounded:
                        path_gradient_cost += link.est_count_dev
                    elif link.is_obs_upper_bounded and link.est_count_dev > 0:
                        path_gradient_cost += link.est_count_dev

            col.set_gradient_cost(path_gradient_cost)

            change_vol = step_size * path_gradient_cost
            change_vol_ub = vol * delta
            change_vol_lb = -change_vol_ub

            if change_vol < change_vol_lb:
                change_vol = change_vol_lb
            elif change_vol > change_vol_ub:
                change_vol = change_vol_ub

            col.set_volume = max(1, vol - change_vol)
