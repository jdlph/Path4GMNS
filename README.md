# Path4GMNS

Path4GMNS is an open-source, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides the static and time-dependent shortest path calculations and retrievals for simple network analyses, its main functionality is to provide an efficient and flexible framework for column(path)-based modeling/application frameworks in transportations (e.g., activity-based demand modeling).

## Installation
Path4GMNS has been published on PyPI, and can be installed using
```
$ pip install path4gmns
```
If you need a specific version of Path4GMNS, say, 0.5.1,
```
$ pip install path4gmns==0.5.1
```
If you want to test the latest features of Path4GMNS, you can build the package from sources and install it offline, where **Python 3.x** is required.
```
# from the root directory of PATH4GMNS
$ python setup.py sdist bdist_wheel
$ cd dist
$ python -m pip install path4gmns-version.tar.gz
``` 
The shared libraries of DTALite and path_engine for Path4GMNS can be built with a C++ compiler supporting C++11 and higher. We use CMake to define the building process. Take path engine for example,
```
# from the root directory of engine
$ mkdir build
$ cd build
$ cmake .
$ cmake --build .
```
You can replace the last command with $ make if your target system has Make installed.
### Caveat
As CMAKE_BUILD_TYPE WILL BE INGNORED for IDE generators, like Visual Studio and Xcode, you will need to manually update the build type from debug to release in your IDE.

## Getting Started
*Download the test data set*

*Get the shortest path between two nodes based on distance*
```python
import path4gmns as pg

load_demand = False
network = pg.read_network(load_demand)
print('\nshortest path (node id) from node 1 to node 2 is '
      +pg.find_shortest_path(network, 1, 2))
```

*Find shortest paths for all individual agents*
```python
import path4gmns as pg

network = pg.read_network()
pg.find_path_for_agents(network)

```

*Perform path-based user-equilibrium (UE) traffic assignment using the python column-generation module*
```python
""" the python column-generation module only implements mode 1

if you need other assignment modes, 
e.g., link-based UE or dynamic traffic assignment (DTA),
please use perform_network_assignment_DTALite().
"""
import path4gmns as pg

network = pg.read_network()

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment(mode, assignment_num, column_update_num, network)

pg.output_columns(network.zones, network.column_pool)
pg.output_link_performance(network.link_list)

print('\npath finding results can be found in agent.csv')
```

*Perform path-based UE traffic assignment using DTALite*
```python
""" DTALite has the following four assignment modes to choose

0: Link-based UE
1: Path-based UE 
2: UE + DTA and simulation
3: ODME
"""
import path4gmns as pg

# no need to call read_network() like the python module
# as network and demand loading will be handled within DTALite

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment_DTALite(1, assignment_num,
                                      column_update_num, network)

# no need to call output_columns() and output_link_performance() 
# as the python module since outputs will be processed within DTALite

print('\npath finding results can be found in agent.csv')
```

## Notes on Implementations

The column generation scheme in Path4GMNS is an equivalent single-processing implementation as its [DTALite](https://github.com/asu-trans-ai-lab/PythonDTALite) multiprocessing counterpart. Support for the multi-demand-period and multi-agent-type is reserved for the future implementation. Note that the results (i.e., column pool and trajectory for an agent) from Path4GMNS and DTALite are comparable but likely not identical as the shortest paths are usually not unique and subjected to implementations. This subtle difference should be gone and the link performances should be consistent if the iterations on both assignment and column generation are large enough. You can always compare the results (i.e., link_performance.csv) from Path4GMNS and DTALite given the same network and demand.

The whole package is implemented towards high performance. The core shortest-path engine is implemented in C++ (deque implementation of the modified label correcting algorithm) along with the equivalent Python implementations for demonstrations. To achieve the maximum efficiency, we use a fixed-length array as the deque (rather than the STL deque) and combine the scan eligible list (represented as deque) with the node presence statutes. Along with the minimum and fast argument interfacing between the underlying C++ path engine and the upper Python modules, its running time is comparable to the pure C++-based DTALite. If you have an extremely large network and/or have requirement on CPU time, we recommend using DTALite to fully utilze its parallel computing feature.

An easy and smooth installation process by low dependency is one of our major design goals. The Python modules in Path4GMNS only requires a handful of components from the Python standard library (e.g., csv, cytpes, and so on) with no any third-party libraries/packages. On the C++ side, the precompiled path engine as shared libraries are embedded to make this package portable across three major desktop environments (i.e., Windows, macOS, and Linux) and its source is implemented in C++11 with no dependency. Users can easily build the path engine from the source code towards the target system if it is not listed as one of the three.