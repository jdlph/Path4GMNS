# Path4GMNS

Path4GMNS is an open-source, cross-platform, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides finding the static and time-dependent shortest path for simple analyses, its main functionality is to provide an efficient and flexible framework for column(path)-based modeling and applications in transportations (e.g., activity-based demand modeling).

## Installation
Path4GMNS has been published on [PyPI](https://pypi.org/project/path4gmns/), and can be installed using
```
$ pip install path4gmns
```
If you need a specific version of Path4GMNS, say, 0.7.0a1,
```
$ pip install path4gmns==0.7.0a1
```

### Dependency
The Python modules are written in **Python 3.x**, which is the minimum requirement to explore the most of Path4GMNS. Some of its functions require further run-time support, which we will go through along with the corresponding use cases in the following section.

## Getting Started
### *Download the Test Data Set*
A sample data set with five different networks can be found from [here](https://github.com/jdlph/Path4GMNS/tree/master/data). You can manually download each individual test network or use the built-in helper function to download the whole data set automatically.

```python
import path4gmns as pg

pg.download_sample_data_sets()
```

Note that [requests](https://pypi.org/project/requests/) (2.21.1 or higher) is needed for you to proceed downloading.

### *Get the Shortest Path between Two Nodes*
Find the (static) shortest path (based on distance) and output it in the format of a sequence of node/link IDs.
```python
import path4gmns as pg

load_demand = False
network = pg.read_network(load_demand)

print('\nshortest path (node id) from node 1 to node 2 is '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2 is '
      +network.find_shortest_path(1, 2, 'link'))
```

If you want to use a specific network from the downloaded sample data set, you can spcicify the absolute path or the relative path from your cwd in read_network().

```python
import path4gmns as pg

load_demand = False
network = pg.read_network(load_demand, input_dir='data/Chicago_Sketch')

print('\nshortest path (node id) from node 1 to node 2 is '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2 is '
      +network.find_shortest_path(1, 2, 'link'))
```

### *Find Shortest Paths for All Individual Agents*
Path4GMNS is capable of calculating and constructing the (static) shortest path for each individual agent. Individual agents will be firstly set up using the aggregated travel demand between each OD pair within find_path_for_agents() on its first call.

```python
import path4gmns as pg

network = pg.read_network()
network.find_path_for_agents()

agent_id = 300
print('\norigin node id of agent is '
      +str(network.get_agent_orig_node_id(agent_id)))

print('destination node id of agent is '
      +str(network.get_agent_dest_node_id(agent_id)))

print('shortest path (node id) of agent is '
      +str(network.get_agent_node_path(agent_id)))

print('shortest path (link id) of agent is '
      +str(network.get_agent_link_path(agent_id)))

agent_id = 1000
print('\norigin node id of agent is '
      +str(network.get_agent_orig_node_id(agent_id)))

print('destination node id of agent is '
      +str(network.get_agent_dest_node_id(agent_id)))

print('shortest path (node id) of agent is '
      +str(network.get_agent_node_path(agent_id)))

print('shortest path (link id) of agent is '
      +str(network.get_agent_link_path(agent_id)))
```

### *Perform Path-Based User-Equilibrium (UE) Traffic Assignment using the Python Column-Generation Module*
The python column-generation module only implements mode 1 (i.e., Path-Based UE). If you need other assignment modes, e.g., link-based UE or dynamic traffic assignment (DTA), please use perform_network_assignment_DTALite().

```python
import path4gmns as pg

network = pg.read_network()

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment(mode, assignment_num, column_update_num, network)

pg.output_columns(network)
pg.output_link_performance(network)

print('\npath finding results can be found in agent.csv')
```

v0.7.0a1 supports loading column/path results from existing files (generated from either the Python module or DTALite in the next example) and continue the column-generation procedure from where you left in the previous run by using this Python module only.

```python
import path4gmns as pg

network = pg.read_network()
# you can specify the input directory like pg.load_columns('data/Chicago_Sketch', nework)
pg.load_columns(nework)

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment(mode, assignment_num, column_update_num, network)

pg.output_columns(network)
pg.output_link_performance(network)

print('\npath finding results can be found in agent.csv')
```

### *Perform Path-Based UE Traffic Assignment using DTALite*
DTALite has the following four assignment modes to choose.

      0: Link-based UE
      1: Path-based UE
      2: UE + DTA and simulation
      3: ODME

```python
import path4gmns as pg

# no need to call read_network() like the python module
# as network and demand loading will be handled within DTALite

# path-based UE
mode = 1
assignment_num = 10
column_update_num = 10

pg.perform_network_assignment_DTALite(1, assignment_num, column_update_num)

# no need to call output_columns() and output_link_performance()
# since outputs will be processed within DTALite

print('\npath finding results can be found in agent.csv')
```

The OpenMP Run-Time Library must be installed to utilize the built-in parallel computing feature in DTALite. DTALite would not be able to run if the run-time support is absent. Installation of the OpenMP run-time library varies by operating systems.

***Windows Users***

Download [Microsoft Visual C++ Redistributable for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/#microsoft-visual-c-redistributable-for-visual-studio-2019) and check [here](https://support.microsoft.com/en-us/topic/the-latest-supported-visual-c-downloads-2647da03-1eea-4433-9aff-95f26a218cc0) for more information and earlier versions.

***Linux Users***

No actions are needed as most Linux distributions have GCC installed with OpenMP support.

***macOS Users***

You will need to install libomp using [Homebrew](https://brew.sh/).

```
$ brew install libomp
```

### *Perform multimodal accessibility evaluation*

The current implemenation supprts accessibility evaluations for the following three modes. More modes will be added in the future to accommodate the full set of allowed uses for links as specified by GMNS.

      1. passenger (i.e., auto)
      2. bike
      3. walk

In order to perform multimodal accessibility evaluation, the corresponding modes (i.e., agent types) must be presented in [settings.yml](https://github.com/jdlph/Path4GMNS/blob/master/tests/settings.yml). It will be parsed by [pyyaml](https://pypi.org/project/PyYAML/) (5.1 or higher) to the Python engine at run-time.

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
network = pg.read_network()

print('\nstart accessibility evaluation\n')
st = time()

pg.evaluate_accessiblity(network)

print('complete accessibility evaluation.\n')
print('processing time of accessibility evaluation:{0: .2f}'
      .format(time()-st)+'s')
print('accessibility matrices can be found in accessibility.csv '
      'and accessibility_aggregated.csv')
```

The following example is to evaluate accessibility only under the default mode (i.e. mode 'auto' or agent type 'passenger').

```python
network = pg.read_network()

print('\nstart accessibility evaluation\n')
st = time()

multimodal = False

pg.evaluate_accessiblity(network, multimodal)

print('complete accessibility evaluation.\n')
print('processing time of accessibility evaluation:{0: .2f}'
      .format(time()-st)+'s')
print('accessibility matrices can be found in accessibility.csv '
      'and accessibility_aggregated.csv')
```

## Build Path4GMNS from Source

If you want to test the latest features of Path4GMNS, you can build the package from source and install it offline, where **Python 3.x** is required.

### 1. Build the shared libraries of DTALite and path_engine and move them to Path4GMSN/path4gmns/bin

The shared libraries of [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) and [path_engine](https://github.com/jdlph/Path4GMNS/tree/master/engine) for Path4GMNS can be built with a C++ compiler supporting C++11 and higher, where we use CMake to define the building process. Take path_engine for example,
```
# from the root directory of engine
$ mkdir build
$ cd build
$ cmake ..
$ cmake --build .
```
You can replace the last command with $ make if your target system has Make installed. See [here](https://github.com/jdlph/DTALite) for details on building the shared library of DTALite.

***Caveat***

As **CMAKE_BUILD_TYPE** will be **IGNORED** for IDE (Integrated Development Environment) generators, e.g., Visual Studio and Xcode, you will need to manually update the build type from debug to release in your IDE and build your target from there.

### 2. Build the Python Package and Install It

```
# from the root directory of PATH4GMNS
$ python setup.py sdist bdist_wheel
$ cd dist
$ python -m pip install path4gmns-version.tar.gz
```

## Upcoming Features
- [x] Read and output node and link geometries (v0.6.0)
- [x] Set up individual agents from aggregated OD demand only when it is needed (v0.6.0)
- [x] Load columns/paths from existing runs and continue path-base UE (v0.7.0a1)
- [x] Download the predefined GMNS test data sets to usrs' local machines when needed (v0.7.0a1)
- [x] Calculate and show up multimodal accessibilities (v0.7.0a1)
- [ ] Visualize individual column/paths on user's call
- [ ] Let users modify the network topology in a simple way by adding/removing nodes and links
- [ ] Enable manipulations on the overall travel demand and the demand between an OD pair
- [x] Support for multi-demand-period and multi-agent-type (v0.6.0)
- [x] Add allowed use in terms of agent type (i.e., transportation mode) for links (v0.7.0a1)
- [x] Provide a setting file in yaml to let users control key parameters (v0.6.0)
- [ ] Adopt parallel computing to further boost the performance

##  Implementation Notes

The column generation scheme in Path4GMNS is an equivalent **single-processing implementation** as its [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) multiprocessing counterpart. **Note that the results (i.e., column pool and trajectory for an agent) from Path4GMNS and DTALite are comparable but likely not identical as the shortest paths are usually not unique and subjected to implementations**. This subtle difference should be gone and the link performances should be consistent if the iterations on both assignment and column generation are large enough. You can always compare the results (i.e., link_performance.csv) from Path4GMNS and DTALite given the same network and demand.

The whole package is implemented towards **high performance**. The core shortest-path engine is implemented in C++ (deque implementation of the modified label correcting algorithm) along with the equivalent Python implementations for demonstrations. To achieve the maximum efficiency, we use a fixed-length array as the deque (rather than the STL deque) and combine the scan eligible list (represented as deque) with the node presence statutes. Along with the minimum and fast argument interfacing between the underlying C++ path engine and the upper Python modules, its running time is comparable to the pure C++-based DTALite. If you have an extremely large network and/or have requirement on CPU time, we recommend using DTALite to fully utilze its parallel computing feature.

An easy and smooth installation process by **low dependency** is one of our major design goals. The core Python modules in Path4GMNS only requires a handful of components from the Python standard library (e.g., csv, cytpes, and so on) with no any third-party libraries/packages. On the C++ side, the precompiled path engine as shared libraries are embedded to make this package portable across three major desktop environments (i.e., Windows, macOS, and Linux) and its source is implemented in C++11 with no dependency. Users can easily build the path engine from the source code towards the target system if it is not listed as one of the three.