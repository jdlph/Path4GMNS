# Path4GMNS
[![platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)
 [![Downloads](https://pepy.tech/badge/path4gmns)](https://pepy.tech/badge/path4gmns) [![GitHub release](https://img.shields.io/badge/release-v0.8.2-brightgreen)](https://img.shields.io/badge/release-v0.8.2-brightgreen)

Path4GMNS is an open-source, cross-platform, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides finding static shortest paths for simple analyses, its main functionality is to provide an efficient and flexible framework for column-based (path-based) modeling and applications in transportation (e.g., activity-based demand modeling). Path4GMNS supports, in short,

1. finding (static) shortest path between two nodes,
2. constructing shortest paths for all individual agents,
3. performing path-based User-Equilibrium (UE) traffic assignment,
4. evaluating multimodal accessibility.

Path4GMNS also serves as an API to the C++-based [DTALite](https://github.com/jdlph/DTALite) to conduct various multimodal traffic assignments including,
   * Link-based UE,
   * Path-based UE,
   * UE + Dynamic Traffic Assignment (DTA),
   * Origin-Destination Matrix Estimation (ODME).

## Installation
Path4GMNS has been published on [PyPI](https://pypi.org/project/path4gmns/0.8.2/), and can be installed using
```
$ pip install path4gmns
```
If you need a specific version of Path4GMNS, say, 0.8.2,
```
$ pip install path4gmns==0.8.2
```

v0.8.2 comes with major performance improvement in column generation module. All previous releases shall be **deprecated**.

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

network = pg.read_network(load_demand=False)

print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, 'link'))
```

You can specify the absolute path or the relative path from your cwd in read_network() to use a particular network from the downloaded sample data set.

```python
import path4gmns as pg

network = pg.read_network(load_demand=False, input_dir='data/Chicago_Sketch')

print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, 'link'))
```

Retrieving the shortest path between any two (different) nodes under a specific mode is now available under v0.7.2 or higher.
```python
import path4gmns as pg

network = pg.read_network(load_demand=False)

print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w'))
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w', seq_type='link'))
```

The mode passed to find_shortest_path() must be defined in settings.yaml, which could be either the type or the name. Take the above sample code for example, the type 'w' and its name 'walk' are equivalent to each other. See **Perform Multimodal Accessibility Evaluation** for more information.

### Find Shortest Paths for All Individual Agents
Path4GMNS is capable of calculating and constructing the (static) shortest paths for all agents. Individual agents will be automatically set up using the aggregated travel demand between each OD pair within find_path_for_agents() on its first call.

The unique agent paths can be output to a csv file as shown in the example below.
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
# use pg.output_agent_paths(network, False)
pg.output_agent_paths(network)
```

v0.7.2 or higher features finding agent paths under a specific mode defined in settings.yaml. The following example demonstrates this new functionality under mode walk (i.e., w).
```python
import path4gmns as pg

network = pg.read_network()
network.find_path_for_agents()

# or equivalently network.find_path_for_agents('walk')
network.find_path_for_agents('w')

# retrieving the origin, the destination, and the shortest path of a given agent
# is exactly the same as before as well as outputting all unique agent paths
```

### Perform Path-Based UE Traffic Assignment using the Python Column-Generation Module
The Python column-generation module only implements path-based UE. If you need other assignment modes, e.g., link-based UE or DTA, please use perform_network_assignment_DTALite().

```python
import path4gmns as pg

network = pg.read_network()

column_gen_num = 20
column_update_num = 10

# path-based UE only
pg.perform_column_generation(column_gen_num, column_update_num, network)

# if you do not want to include geometry info in the output file,
# use pg.output_columns(network, False)
pg.output_columns(network)
pg.output_link_performance(network)
```

**NOTE THAT** you can still use the legacy _pg.perform_network_assignment(assignment_mode=1, column_gen_num, column_update_num, network)_ to perform the same functionality here. But it has been **deprecated**, and will be removed later.

Starting from v0.7.0a1, Path4GMNS supports loading columns/paths from existing files (generated from either the Python module or DTALite) and continue the column-generation procedure from where you left. Please **skip the column generation stage** and go directly to column pool optimization by setting **column_gen_num = 0**.

```python
import path4gmns as pg

network = pg.read_network()
# you can specify the input directory
# e.g., pg.load_columns(network, 'data/Chicago_Sketch')
pg.load_columns(network)

# we recommend NOT doing assignment again after loading columns
column_gen_num = 0
column_update_num = 10

pg.perform_column_generation(column_gen_num, column_update_num, network)

pg.output_columns(network)
pg.output_link_performance(network)
```

### Perform Traffic Assignment using DTALite
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
column_gen_num = 10
column_update_num = 10

pg.perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

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

The current implementation supports accessibility evaluation for any modes defined in settings.yml. Note that you can restrict the allowed uses (modes) on each link by adding a field of "allowed_uses" to link.csv following the example [here](https://github.com/zephyr-data-specs/GMNS/blob/master/Small_Network_Examples/Cambridge_v090/link.csv). Otherwise, links are open to all modes.

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

# no need to load demand file for accessibility evaluation
network = pg.read_network(load_demand=False)

print('\nstart accessibility evaluation\n')
st = time()

pg.evaluate_accessibility(network)

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
```

Two formats of accessibility will be output: accessibility between each OD pair in terms of free flow travel time (accessibility.csv) and aggregated accessibility as to the number of accessible zones from each zone for each transportation mode specified in settings.yml given a budget time (up to 240 minutes) (accessibility_aggregated.csv). The following example is to evaluate accessibility only under the default mode (i.e., mode auto or agent type passenger).

```python
import path4gmns as pg

# no need to load demand file for accessibility evaluation
network = pg.read_network(load_demand=False)

print('\nstart accessibility evaluation\n')
st = time()

pg.evaluate_accessibility(network, multimodal=False)
# the default is under mode auto (i.e., p)
# if you would like to evaluate accessibility under a target mode, say walk, then
# pg.evaluate_accessibility(network, multimodal=False, mode='w')
# or equivalently pg.evaluate_accessibility(network, multimodal=False, mode='walk')

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
```

You can also get the accessible nodes and links within a time budget given a mode. Similar to the accessibility evaluation, the selected mode must come from settings.yml.

```python
import path4gmns as pg

# no need to load demand file for accessibility evaluation
network = pg.read_network(load_demand=False)

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'p')
network.get_accessible_nodes(1, 5)
network.get_accessible_links(1, 5)

# get accessible nodes and links starting from node 1 with a 15-minute
# time window for mode walk (i.e., 'w')
network.get_accessible_nodes(1, 15, 'w')
network.get_accessible_links(1, 15, 'w')
# the following two work equivalently as their counterparts above
# network.get_accessible_nodes(1, 15, 'walk')
# network.get_accessible_links(1, 15, 'walk')
```

### When Time-Dependent Link Travel Time Matters
Link travel time is crucial in calculating accessibility. In the classic accessibility analysis, evaluation networks are usually considered to be static in terms of link travel time, which is determined by link length and link free-flow speed under a specific mode. The free-flow speed comes from either link.csv or settings.yml (both are denoted as "free_speed"). When they are different, the smaller one will be adopted. The cases demonstrated above are all falling within this category.

Link travel time varies over time so does accessibility. When the time-dependent accessibility is of interested, time-dependent link travel time (i.e., VDF_fftt from a given demand period in link.csv) will come into play by overwriting the (static) link free-flow speed. This new feature is now part of v0.7.3 and is illustrated as below.

```python
import path4gmns as pg

# no need to load demand file for accessibility evaluation
network = pg.read_network(load_demand=False)

print('\nstart accessibility evaluation\n')
st = time()

# time-dependent accessibility under the default mode auto (i.e., p)
# for demand period 0 (i.e., VDF_fftt1 in link.csv will be used in the evaluation)
pg.evaluate_accessibility(network, multimodal=False, time_dependent=True)

# if you would like to evaluate accessibility under a different demand period
# (say 1, which must be defined in settings.yml along with VDF_fftt2 in link.csv), then
pg.evaluate_accessibility(network, multimodal=False, time_dependent=True, demand_period_id=1)

# if you would like to evaluate accessibility under a target mode, say walk, then
pg.evaluate_accessibility(network, multimodal=False, mode='w', time_dependent=True)
```

While VDF_fftt begins with 1 (i.e., VDF_fftt1), the argument demand_period_id, corresponding to the sequence number of demand period appeared in demand_periods in settings.yml, starts from 0. So "demand_period_id=0" indicates that VDF_fftt1 will be used (and so on and so forth).

**As VDF_fftt in link.csv can only accommodate one mode, time-dependent accessibility evaluation will require the user to prepare a mode-specific link.csv with dedicated VDF_fftt and allowed_uses**. That's the reason that "multimodal=False" is always enforced in these examples.

Retrieve the time-dependent accessible nodes and links is similar to evaluate time-dependent accessibility by simply passing time_dependent and demand_period_id to get_accessible_nodes() and get_accessible_links().

```python
import path4gmns as pg

# no need to load demand file for accessibility evaluation
network = pg.read_network(load_demand=False)

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'p') for demand period 0
network.get_accessible_nodes(1, 5, time_dependent=True)

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'p') for demand period 1 if it is defined
network.get_accessible_links(1, 5, time_dependent=True, demand_period_id=1)

# get accessible nodes and links starting from node 1 with a 15-minute
# time window for mode walk (i.e., 'w') for demand periods 0 and 1 respectively
network.get_accessible_nodes(1, 15, 'w', time_dependent=True)
network.get_accessible_links(1, 15, 'w', time_dependent=True, demand_period_id=1)
```

## Benchmarks
Coming soon.

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
The last command can be replaced with $ make if your target system has Make installed. See [here](https://github.com/jdlph/DTALite) for details on how to build DTALite. After they are successfully compiled, move them to Path4GMNS/path4gmns/bin.

***Caveat***

As **CMAKE_BUILD_TYPE** will be **IGNORED** for IDE (Integrated Development Environment) generators, e.g., Visual Studio and Xcode, you will need to manually update the build type from debug to release in your IDE and build your target from there.

### 2. Build and Install the Python Package

```
# from the root directory of PATH4GMNS
$ python setup.py sdist bdist_wheel
$ cd dist
# or python -m pip instal pypath4gmns-0.8.2-py3-none-any.whl
$ python -m pip install path4gmns-0.8.2.tar.gz
```

Here, 0.8.2 is the version number. Replace it with the one specified in setup.py.

## Implementation Notes

The column generation scheme in Path4GMNS is an equivalent **single-processing implementation** as its [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) multiprocessing counterpart. **Note that** the results (i.e., column pool and trajectory for each agent) from Path4GMNS and DTALite are comparable but likely not identical as the shortest paths are usually not unique and subjected to implementations. This difference shall be subtle and the link performances shall be consistent if the iterations of column generation and column update are both large enough. You can always compare the results (i.e., link_performance.csv) from Path4GMNS and DTALite given the same network and demand.

The whole package is implemented towards **high performance**. The core shortest-path engine is implemented in C++ (deque implementation of the modified label correcting algorithm) along with the equivalent Python implementations for demonstration. To achieve the maximum efficiency, we use a fixed-length array as the deque (rather than the STL deque) and combine the scan eligible list (represented as deque) with the node presence status. Along with the minimum and fast argument interfacing between the underlying C++ path engine and the upper Python modules, its running time is comparable to the pure C++-based DTALite for small- and medium-size networks (e.g., the Chicago Sketch Network) without multiprocessing. If you have an extremely large network and/or have requirement on CPU time, we recommend using DTALite to fully utilize its parallel computing feature.

An easy and smooth installation process by **low dependency** is one of our major design goals. The core Python modules in Path4GMNS only require a handful of components from the Python standard library (e.g., csv, ctypes, and so on) with no any third-party libraries/packages. On the C++ side, the precompiled path engines as shared libraries are embedded to make this package portable across three major desktop environments (i.e., Windows, macOS, and Linux) and its source is implemented in C++11 with no dependency. Users can easily build the path engine from the source code towards their target system if it is not listed above as one of the three.

### More on the Column-Generation Module
The column generation module first identifies new columns (i.e., paths) between each OD pair at each iteration and adds them into the column pool before optimizing (i.e., shifting flows among columns to achieve the equilibrium state). The original implementations in both DTALite and Path4GMNS (prior to v0.8.0) rely on node sum as the unique key (or hash index) to differentiate columns, which is simply the summation of node sequence numbers along a column. However, it cannot guarantee that a non-existing column will always be added to the column pool as different columns may share the same node sum (and we presume a one-to-one mapping from node sum to column rather than an array of slots for different columns with the same node sum). An example would be 0->1->4->5 and 0->2->3->5, where 0 to 5 are node sequence numbers. One of the columns will be precluded from the column pool.

In order to resolve this issue, we have deprecated node sum and introduced a side-by-side column comparison in Path4GMNS only. As columns between an OD pair are largely different in number of nodes, this comparison can be very efficiently. Slight improvements are actually observed in both running time and convergence gap over the original implementation.

DTALite uses arrays rather than STL containers to store columns. These arrays are fixed in size (1,000), which prevents a fast filtering using the number of nodes as described above. For two (long) columns only different in the last few nodes, this side-by-side comparison has to be continued until the very end and ruins the performance. Thus, we decide **NOT TO ADOPT** this updated implementation to DTALite but do expect it in the future release after [refactoring](https://github.com/jdlph/DTALite#refactoring).

### Major Updates
1. Read and output node and link geometries (v0.6.0)
2. Set up individual agents from aggregated OD demand only when it is needed (v0.6.0)
3. Provide a setting file in yaml to let users control key parameters (v0.6.0)
4. Support for multi-demand-period and multi-agent-type (v0.6.0)
5. Load columns/paths from existing runs and continue path-base UE (v0.7.0a1)
6. Download the predefined GMNS test data sets to users' local machines when needed (v0.7.0a1)
7. Add allowed use in terms of agent type (i.e., transportation mode) for links (v0.7.0a1)
8. Calculate and show up multimodal accessibilities (v0.7.0a1)
9. Apply lightweight and faster implementation on accessibility evaluation using virtual centroids and connectors (v0.7.0)
10. Get accessible nodes and links given mode and time budget (v0.7.0)
11. Retrieve shortest paths under multimodal allowed uses (v0.7.2)
12. Time-dependent accessibility evaluation (v0.7.3)
13. Fix crucial bug in accessibility evaluation (v0.7.5)
14. Deprecate node_sum as hash index in column generation (v0.8.0)
15. Optimize class ColumnVec, setup_agents() in class Network, and column generation module (i.e., colgen.py) (v0.8.1)
16. Deep code optimization in column generation module with significant performance improvement (v0.8.2)

Detailed update information can be found in [Releases](https://github.com/jdlph/Path4GMNS/releases).

## Contribute

Any contributions are welcomed including advise new applications of Path4GMNS, enhance documentation (this guideline and [docstrings](https://docs.python-guide.org/writing/documentation/#writing-docstrings) in the source code), refactor and/or optimize the source code, report and/or resolve potential issues/bugs, suggest and/or add new functionalities, etc.

Path4GMNS has a very simple workflow setup, i.e., **master for release (on both GitHub and PyPI) and dev for development**. If you would like to work directly on the source code (and probably the documentation), please make sure that **the destination branch of your pull request is dev**, i.e., all potential changes/updates shall go to the dev branch before merging into master for release.

You are encouraged to join our Slack workspace for more discussions and collaborations. [Drop us an email](xzhou74@asu.edu;jdlph@hotmail.com) for invitation.

## How to Cite

Li, P. and Zhou, X. (2022, April 30). *Path4GMNS*. Retrieved from https://github.com/jdlph/Path4GMNS

## References
Lu, C. C., Mahmassani, H. S., Zhou, X. (2009). Equivalent gap function-based reformulation and solution algorithm for the dynamic user equilibrium problem. Transportation Research Part B: Methodological, 43, 345-364.

Jayakrishnan, R., Tsai, W. K., Prashker, J. N., Rajadyaksha, S. (1994). [A Faster Path-Based Algorithm for Traffic Assignment](https://escholarship.org/uc/item/2hf4541x) (Working Paper UCTC No. 191). The University of California Transportation Center.