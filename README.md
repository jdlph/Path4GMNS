# Path4GMNS

Path4GMNS is an open-source, cross-platform, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides finding the static and time-dependent shortest path for simple analyses, its main functionality is to provide an efficient and flexible framework for column(path)-based modeling and applications in transportation (e.g., activity-based demand modeling). Path4GMNS supports, in short,

1. finding (static) shortest path between two nodes;
2. constructing shortest paths for all individual agents;
3. performing various multimodal traffic assignments including
   * Link-based User-Equilibrium (UE),
   * Path-based UE,
   * UE + Dynamic Traffic Assignment (DTA),
   * Origin-Destination Matrix Estimation (ODME);
4. evaluating multimodal accessibility.

## Installation
Path4GMNS has been published on [PyPI](https://pypi.org/project/path4gmns/0.7.0/), and can be installed using
```
$ pip install path4gmns
```
If you need a specific version of Path4GMNS, say, 0.7.0,
```
$ pip install path4gmns==0.7.0
```

v0.7.0 comes with new functionalities, improved performance, and potential issue fix. All previous releases shall be deprecated for any purposes.

### Dependency
The Python modules are written in **Python 3.x**, which is the minimum requirement to explore the most of Path4GMNS. Some of its functions require further run-time support, which we will go through along with the corresponding use cases in the following section.

## Getting Started
### Download the Test Data Set
A sample data set with six different networks are provided. You can manually retrieve each individual test network from [here](https://github.com/jdlph/Path4GMNS/tree/master/data) or use the built-in helper function to automatically download the whole data set.

```python
import path4gmns as pg

pg.download_sample_data_sets()
```

Note that [requests](https://pypi.org/project/requests/) (2.21.1 or higher) is needed for you to proceed downloading.

### Get the Shortest Path between Two Nodes
Find the (static) shortest path (based on distance) and output it in the format of a sequence of node/link IDs.
```python
import path4gmns as pg

load_demand = False
network = pg.read_network(load_demand)

print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, 'link'))
```

You can specify the absolute path or the relative path from your cwd in read_network() to use a particular network from the downloaded sample data set.

```python
import path4gmns as pg

load_demand = False
network = pg.read_network(load_demand, input_dir='data/Chicago_Sketch')

print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, 'link'))
```

### Find Shortest Paths for All Individual Agents
Path4GMNS is capable of calculating and constructing the (static) shortest paths for all agents. Individual agents will be automatically set up using the aggregated travel demand between each OD pair within find_path_for_agents() on its first call.

The unique agent paths can be outputed to a csv file as shown in the example below.
```python
import path4gmns as pg

network = pg.read_network()
network.find_path_for_agents()

agent_id = 300
print('\norigin node id of agent is '
      f'{network.get_agent_orig_node_id(agent_id)}')
print('destination node id of agent is '
      f'{network.get_agent_dest_node_id(agent_id)}')
print('shortest path (node id) of agent, '
      f'{network.get_agent_node_path(agent_id)}')
print('shortest path (link id) of agent, '
      f'{network.get_agent_link_path(agent_id)}')

agent_id = 1000
print('\norigin node id of agent is '
      f'{network.get_agent_orig_node_id(agent_id)}')
print('destination node id of agent is '
      f'{network.get_agent_dest_node_id(agent_id)}')
print('shortest path (node id) of agent, '
      f'{network.get_agent_node_path(agent_id)}')
print('shortest path (link id) of agent, '
      f'{network.get_agent_link_path(agent_id)}')

# output unique agent paths to a csv file
# if you do not want to include geometry info in the output file,
# you can do pg.output_agent_paths(network, False)
pg.output_agent_paths(network)
```

### Perform Path-Based UE Traffic Assignment using the Python Column-Generation Module
The Python column-generation module only implements path-based UE (i.e., mode 1). If you need other assignment modes, e.g., link-based UE or DTA, please use perform_network_assignment_DTALite().

```python
import path4gmns as pg

network = pg.read_network()

# path-based UE
mode = 1
assignment_num = 20
column_update_num = 10

pg.perform_network_assignment(mode, assignment_num, column_update_num, network)

# if you do not want to include geometry info in the output file,
# you can do pg.output_columns(network, False)
pg.output_columns(network)
pg.output_link_performance(network)

print('\npath finding results can be found in agent.csv')
```

Starting from v0.7.0a1, Path4GMNS supports loading columns/paths from existing files (generated from either the Python module or DTALite) and continue the column-generation procedure from where you left. Please **skip the assignment stage** and go directly to column pool optimization by setting **assignment_num = 0**.

```python
import path4gmns as pg

network = pg.read_network()
# you can specify the input directory
# like pg.load_columns(network, 'data/Chicago_Sketch')
pg.load_columns(network)

# path-based UE
mode = 1
# we recommend NOT doing assignemnt again after loading columns
assignment_num = 0
column_update_num = 10

pg.perform_network_assignment(mode, assignment_num, column_update_num, network)

pg.output_columns(network)
pg.output_link_performance(network)

print('\npath finding results can be found in agent.csv')
```

### Perform Path-Based UE Traffic Assignment using DTALite
DTALite has the following four assignment modes to choose.

      0: Link-based UE
      1: Path-based UE
      2: UE + DTA
      3: ODME

The next example demonstrates how to perform path-based UE (i.e., mode 1) using DTALite from Path4GMNS.

```python
import path4gmns as pg

# no need to call read_network() like the python module
# as network and demand loading will be handled within DTALite

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment_DTALite(mode, assignment_num, column_update_num)

# no need to call output_columns() and output_link_performance()
# since outputs will be processed within DTALite

print('\npath finding results can be found in agent.csv')
```

The OpenMP run-time library must be installed to utilize the built-in parallel computing feature in DTALite (and DTALite would not be able to run if the run-time support is absent). Its installation varies by operating systems.

***Windows Users***

Download [Microsoft Visual C++ Redistributable for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/#microsoft-visual-c-redistributable-for-visual-studio-2019) and check [here](https://support.microsoft.com/en-us/topic/the-latest-supported-visual-c-downloads-2647da03-1eea-4433-9aff-95f26a218cc0) for more information and earlier versions.

***Linux Users***

No actions are needed as most Linux distributions have GCC installed with OpenMP support.

***macOS Users***

You will need to install libomp using [Homebrew](https://brew.sh/).

```
$ brew install libomp
```

### Perform Multimodal Accessibility Evaluation

The current implemenation under v0.7.0a1 supprts accessibility evaluation for the following three modes. More modes will be added in the future to accommodate the full set of allowed uses for links as specified by GMNS. Note that you can restrict the allowed uses (modes) on each link by adding a field of "allowed_uses" to link.csv following the example [here](https://github.com/zephyr-data-specs/GMNS/blob/master/Small_Network_Examples/Cambridge_v090/link.csv). Othewise, links are open to all modes.

      1. passenger (i.e., auto)
      2. bike
      3. walk

In order to perform multimodal accessibility evaluation, the corresponding modes (i.e., agent types) must be presented in [settings.yml](https://github.com/jdlph/Path4GMNS/blob/master/tests/settings.yml). It will be parsed by [pyyaml](https://pypi.org/project/PyYAML/) (5.1 or higher) to the Python engine at run-time. **Note that demand.csv is not necessary for accessibility evaluation**.

```yaml
agents:
  - type: p
    name: passenger
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 60
  - type: w
    name: walk
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 10

demand_periods:
  - period: AM
    time_period: 0700_0800

demand_files:
  - file_name: demand.csv
    format_type: column
    period: AM
    agent_type: p
```

If pyyaml is not installed or settings.yml is not provided, one demand period (AM) and one agent type (passenger) will be automatically created.

```python
import path4gmns as pg

# you do not need to load demand file to evaluate accessibility
load_demand = False
network = pg.read_network(load_demand)

print('\nstart accessibility evaluation\n')
st = time()

pg.evaluate_accessibility(network)

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
print('accessibility matrices can be found in accessibility.csv '
      'and accessibility_aggregated.csv')
```

Two formats of accessibility will be outputed: accessibility between each OD pair in terms of free flow travel time (accessibility.csv) and aggregated accessibility as to the number of accessible zones from each zone for each transportation mode specified in settings.yml given a budget time (up to 240 minutes) (accessibility_aggregated.csv). The following example is to evaluate accessibility only under the default mode (i.e. mode auto or agent type passenger).

```python
import path4gmns as pg

# you do not need to load demand file to evaluate accessibility
load_demand = False
network = pg.read_network(load_demand)

print('\nstart accessibility evaluation\n')
st = time()

multimodal = False

pg.evaluate_accessiblity(network, multimodal)

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
print('accessibility matrices can be found in accessibility.csv '
      'and accessibility_aggregated.csv')
```

You can also get the accessible nodes and links within a time budget given a mode. Similar to the accessibility evalution, the selected mode must come from settings.yml.

```python
import path4gmns as pg

# you do not need to load demand file to evaluate accessibility
load_demand = False
network = pg.read_network(load_demand)

# get accessible nodes and links starting from node 1 with a 5-minitue
# time window for the default mode auto (i.e., 'p')
network.get_accessible_nodes(1, 5)
network.get_accessible_links(1, 5)

# get accessible nodes and links starting from node 1 with a 15-minitue
# time window for mode walk (i.e., 'w')
network.get_accessible_nodes(1, 15, 'w')
network.get_accessible_links(1, 15, 'w')
```

## Build Path4GMNS from Source

If you would like to test the latest features of Path4GMNS or have a compatible version to a specific operating system or an architecture, you can build the package from source and install it offline, where **Python 3.x** is required.

### 1. Build the Shared Libraries

The shared libraries of [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) and [path_engine](https://github.com/jdlph/Path4GMNS/tree/master/engine) for Path4GMNS can be built with a C++ compiler supporting C++11 and higher, where we use CMake to define the building process. Take path_engine for example,
```
# from the root directory of engine
$ mkdir build
$ cd build
$ cmake ..
$ cmake --build .
```
The last command can be replaced with $ make if your target system has Make installed. See [here](https://github.com/jdlph/DTALite) for details on how to build DTALite. After they are successfully compiled, move them to Path4GMSN/path4gmns/bin.

***Caveat***

As **CMAKE_BUILD_TYPE** will be **IGNORED** for IDE (Integrated Development Environment) generators, e.g., Visual Studio and Xcode, you will need to manually update the build type from debug to release in your IDE and build your target from there.

### 2. Build and Install the Python Package

```
# from the root directory of PATH4GMNS
$ python setup.py sdist bdist_wheel
$ cd dist
# or python -m pip instal pypath4gmns-0.7.0-py3-none-any.whl
$ python -m pip install path4gmns-0.7.0.tar.gz
```

Here, 0.7.0 is the version number. Replace it with the one specified in setup.py.

## Benchmarks
Coming soon.

## Upcoming Features
- [x] Read and output node and link geometries (v0.6.0)
- [x] Set up individual agents from aggregated OD demand only when it is needed (v0.6.0)
- [x] Provide a setting file in yaml to let users control key parameters (v0.6.0)
- [x] Support for multi-demand-period and multi-agent-type (v0.6.0)
- [x] Load columns/paths from existing runs and continue path-base UE (v0.7.0a1)
- [x] Download the predefined GMNS test data sets to usrs' local machines when needed (v0.7.0a1)
- [x] Add allowed use in terms of agent type (i.e., transportation mode) for links (v0.7.0a1)
- [x] Calculate and show up multimodal accessibilities (v0.7.0a1)
- [x] Apply lightweight and faster implementation on accessibility evaluation using virtual centroids and connectors (v0.7.0)
- [x] Get accessible nodes and links given mode and time budget (v0.7.0)
- [ ] Let users modify the network topology in a simple way by adding/removing nodes and links
- [ ] Enable manipulations on the overall travel demand and the demand between an OD pair
- [ ] Visualize individual column/paths on user's call
- [ ] Adopt parallel computing to further boost the performance

## Implementation Notes

The column generation scheme in Path4GMNS is an equivalent **single-processing implementation** as its [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) multiprocessing counterpart. **Note that the results (i.e., column pool and trajectory for an agent) from Path4GMNS and DTALite are comparable but likely not identical as the shortest paths are usually not unique and subjected to implementations**. This subtle difference should be gone and the link performances should be consistent if the iterations on both assignment and column generation are large enough. You can always compare the results (i.e., link_performance.csv) from Path4GMNS and DTALite given the same network and demand.

The whole package is implemented towards **high performance**. The core shortest-path engine is implemented in C++ (deque implementation of the modified label correcting algorithm) along with the equivalent Python implementations for demonstrations. To achieve the maximum efficiency, we use a fixed-length array as the deque (rather than the STL deque) and combine the scan eligible list (represented as deque) with the node presence status. Along with the minimum and fast argument interfacing between the underlying C++ path engine and the upper Python modules, its running time is comparable to the pure C++-based DTALite. If you have an extremely large network and/or have requirement on CPU time, we recommend using DTALite to fully utilze its parallel computing feature.

An easy and smooth installation process by **low dependency** is one of our major design goals. The core Python modules in Path4GMNS only require a handful of components from the Python standard library (e.g., csv, cytpes, and so on) with no any third-party libraries/packages. On the C++ side, the precompiled path engine as shared libraries are embedded to make this package portable across three major desktop environments (i.e., Windows, macOS, and Linux) and its source is implemented in C++11 with no dependency. Users can easily build the path engine from the source code towards the target system if it is not listed as one of the three.