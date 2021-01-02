import sys

sys.path.append('../')

import path4gmns as pg


if __name__=="__main__":
    network = pg.read_network()
    print('the shortest path from node 1 to node 2 is '
          +str(pg.find_shortest_path(network, 1, 2)))