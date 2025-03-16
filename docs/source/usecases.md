# Use Cases

## Download the Test Data Set
A sample data set with six different networks are provided. You can manually retrieve each individual test network from [here](https://github.com/jdlph/Path4GMNS/tree/master/data) or use the built-in helper function to automatically download the whole data set.

```python
import path4gmns as pg

pg.download_sample_data_sets()
```

Note that [requests](https://pypi.org/project/requests/) (2.21.1 or higher) is needed for you to proceed downloading.

## Get the Shortest Path between Two Nodes
Find the (static) shortest path per travel time or distance and output it in the format of a sequence of node/link IDs.

### Shortest Path in terms of Travel Time
By default, find_shortest_path() will return the shortest path according to the travel time.
```python
import path4gmns as pg

network = pg.read_network()

# node path from node 1 to node 2
print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
# link path from node 1 to node 2
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, seq_type='link'))
```

You can specify the absolute path or the relative path from your cwd in read_network() to use a particular network from the downloaded sample data set.

```python
import path4gmns as pg

network = pg.read_network(input_dir='data/Chicago_Sketch')

# node path from node 1 to node 2 measured by travel time
print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2))
# link path from node 1 to node 2 measured by travel time
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, seq_type='link'))
```

Retrieving the shortest path between any two (different) nodes under a specific mode is available under v0.7.2 or higher.
```python
import path4gmns as pg

network = pg.read_network()

# node path from node 1 to node 2 under mode w measured by travel time
print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w'))
# link path from node 1 to node 2 under mode w measured by travel time
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w', seq_type='link'))
```

The mode passed to find_shortest_path() must be defined in settings.yaml, which could be either the type or the name. Take the above sample code for example, the type 'w' and its name 'walk' are equivalent to each other. See **Perform Multimodal Accessibility Evaluation** for more information.

### Shortest Path in terms of Travel Distance
Starting from v0.9.10, you can find the shortest path between any two different nodes in distance by specifying cost_type as 'distance'. The distance unit is the one passed to read_network(), which by default is mile.

```python
import path4gmns as pg

network = pg.read_network()

# node path from node 1 to node 2 measured by distance
print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, cost_type='distance'))
# link path from node 1 to node 2 measured by distance
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, seq_type='link', cost_type='distance'))

# node path from node 1 to node 2 under mode w measured by distance
print('\nshortest path (node id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w', cost_type='distance'))
# link path from node 1 to node 2 under mode w measured by distance
print('\nshortest path (link id) from node 1 to node 2, '
      +network.find_shortest_path(1, 2, mode='w', seq_type='link', cost_type='distance'))
```

## Retrieve the Shortest Path Tree
If you need to find the shortest paths from a source node to any other nodes in the network. You can use get_shortest_path_tree() instead of repeatedly calling find_shortest_path(). Its usage is very similar to find_shortest_path(). You can get the shortest path tree in either node sequences or link sequences.

```python
import path4gmns as pg

network = pg.read_network()

# get shortest path tree (in node sequences) from node 1
# cost is measured by time (in minutes)
sp_tree_node = network.get_shortest_path_tree(1)
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (node id) from node 1 to node 2: {sp_tree_node[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (node id) from node 1 to node 3: {sp_tree_node[3]}')

# get shortest path tree (in link sequences) from node 1
# cost is measured by time (in minutes)
sp_tree_link = network.get_shortest_path_tree(1, seq_type='link')
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (link id) from node 1 to node 2: {sp_tree_link[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (link id) from node 1 to node 3: {sp_tree_link[3]}')
```

Similarly, you can get the distance-based shortest path tree as well. The distance unit is in line with the one passed to read_network().

```python
import path4gmns as pg

network = pg.read_network()

# get shortest path tree (in node sequences) from node 1
# cost is measured by distance (in miles)
sp_tree_node = network.get_shortest_path_tree(1, cost_type='distance')
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (node id) from node 1 to node 2: {sp_tree_node[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (node id) from node 1 to node 3: {sp_tree_node[3]}')

# get shortest path tree (in link sequences) from node 1 (cost is measured by distance (in miles))
sp_tree_link = network.get_shortest_path_tree(1, seq_type='link', cost_type='distance')
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (link id) from node 1 to node 2: {sp_tree_link[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (link id) from node 1 to node 3: {sp_tree_link[3]}')
```

You can also get a shortest path tree with respect to a specific mode, which is specified in settings.yml.

```python
import path4gmns as pg

network = pg.read_network()

# get shortest path tree (in node sequences) from node 1 under mode 'w'
# cost is measured by time (in minutes)
sp_tree_node = network.get_shortest_path_tree(1, mode='w')
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (node id) from node 1 to node 2: {sp_tree_node[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (node id) from node 1 to node 3: {sp_tree_node[3]}')

# get shortest path tree (in link sequences) from node 1 under mode 'w'
# cost is measured by distance
sp_tree_link = network.get_shortest_path_tree(1, mode='w', seq_type='link', cost_type='distance')
# retrieve the shortest path from the source node (i.e., node 1) to node 2
print(f'shortest path (link id) from node 1 to node 2: {sp_tree_link[2]}')
# retrieve the shortest path from the source node (i.e., node 1) to node 3
print(f'shortest path (link id) from node 1 to node 3: {sp_tree_link[3]}')
```

## Find Path-Based UE
The Python column-generation module only implements path-based UE. If you need other assignment modes, e.g., link-based UE or DTA, please use perform_network_assignment_DTALite(). Note that **column_gen_num** below specifies the maximum number of paths / columns for each OD pair.

```python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network)

# path-based UE only
column_gen_num = 20
column_upd_num = 20

pg.find_ue(network, column_gen_num, column_upd_num)

# if you do not want to include geometry info in the output file,
# use pg.output_columns(network, False)
pg.output_columns(network)
pg.output_link_performance(network)
```

Starting from v0.7.0a1, Path4GMNS supports loading columns/paths from existing files (generated from either the Python module or DTALite) and continue the column-generation procedure from where you left. Please **skip the column generation stage** and go directly to column pool optimization by setting **column_gen_num = 0**.

```python
import path4gmns as pg

# no need to load demand file as we will infer the demand from columns
network = pg.read_network()
# you can specify the input directory
# e.g., pg.load_columns(network, 'data/Chicago_Sketch')
pg.load_columns(network)

# we recommend NOT doing assignment again after loading columns
column_gen_num = 0
column_upd_num = 20

pg.find_ue(network, column_gen_num, column_upd_num)

pg.output_columns(network)
pg.output_link_performance(network)
```

v0.9.10 provides users more flexibility to control UE convergency with the relative gap tolerance (i.e., the target relative gap). find_ue() will terminate when either column_upd_num or rel_gap_tolerance is reached and return the final relative gap.
```python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network)

# path-based UE only
column_gen_num = 20
column_upd_num = 20

# the default value of rel_gap_tolerance is 0.0001 if not specified
rel_gap = pg.find_ue(network, column_gen_num, column_upd_num, rel_gap_tolerance = 0.001)
print(f'the final relative UE gap is {rel_gap:.4%}')

# if you do not want to include geometry info in the output file,
# use pg.output_columns(network, False)
pg.output_columns(network)
pg.output_link_performance(network)
```

### In Case of Special Events

A special event often comes with capacity reduction over affected links, which is supported in v0.8.4 or higher. You can introduce one special event for each demand period in settings.yml as below.

```yaml
demand_periods:
  - period: AM
    time_period: 0700-0800
    special_event:
      name: work_zone
      enable: true
      affected_links:
        - link_id: 1
          capacity_ratio: 0.5
        - link_id: 2
          capacity_ratio: 0.4
        - link_id: 3
          capacity_ratio: 0.6
        - link_id: 4
          capacity_ratio: 0
```

If the original capacity of an affected link i is **C**, its capacity then will be **r * C** with a reduction ratio of **r** when a special event is present. For an affected link, setting its capacity_ratio to 0 is equivalent to removing it from the entire demand period. You can turn on or off a special event by setting **enable** to true or false.

Note that this functionality is **NOT** available with perform_network_assignment_DTALite(). You would have to manually update the capacity for each affected link in link.csv to replicate a special event if you plan to use the embedded DTALite to conduct traffic assignment (which is about to be introduced in the next section). The updated capacity for each link will be used by DTALite across all demand periods in settings.csv. In other words, capacity update for a specific demand period is not supported under the current implementation of DTALite.

## Conduct Traffic Assignment using DTALite
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
column_gen_num = 20
column_upd_num = 20

pg.perform_network_assignment_DTALite(mode, column_gen_num, column_upd_num)

# no need to call output_columns() and output_link_performance()
# since outputs will be processed within DTALite

print('\npath finding results can be found in route_assignment.csv')
```

(target_to_paragraph)=

[OpenMP Installation](target_to_paragraph)

The OpenMP run-time library must be installed to utilize the built-in parallel computing feature in DTALite (and DTALite would not be able to run if the run-time support is absent). Its installation varies by operating systems.

***Windows Users***

Download and install [Microsoft Visual C++ Redistributable for Visual Studio](https://support.microsoft.com/en-us/topic/the-latest-supported-visual-c-downloads-2647da03-1eea-4433-9aff-95f26a218cc0).

***Linux Users***

No actions are needed as most Linux distributions have GCC installed with OpenMP support.

***macOS Users***

You will need to install libomp using [Homebrew](https://brew.sh/).

```
$ brew install libomp
```

## Execute Origin-Destination Demand Matrix Estimation (ODME)

ODME has been added to Path4GMNS since v0.9.9, which offers the same functionality as DTALite does. It intends to calibrate the UE result using observations (in terms of traffic counts) stated in measurement.csv. Therefore, UE is needed before running ODME.

```python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network)

# path-based UE
column_gen_num = 20
column_upd_num = 20
pg.find_ue(network, column_gen_num, column_upd_num)

# ODME
pg.read_measurements(network)
pg.conduct_odme(network, 20)

# output column information to route_assignment.csv
pg.output_columns(network)
# output link performance to link_performance.csv
pg.output_link_performance(network)
```

You can also load existing UE results and then run ODME.

```python
import path4gmns as pg

network = pg.read_network()
# load existing UE result
pg.load_columns(network)

# ODME
odme_upd_num = 20
pg.read_measurements(network)
pg.conduct_odme(network, odme_upd_num)

# output column information to route_assignment.csv
pg.output_columns(network)
# output link performance to link_performance.csv
pg.output_link_performance(network)
```

## Evaluate Multimodal Accessibility

The current implementation supports accessibility evaluation for any modes defined in settings.yml. Note that you can restrict the allowed uses (modes) on each link by adding a field of "allowed_uses" to link.csv following the example [here](https://github.com/zephyr-data-specs/GMNS/blob/master/Small_Network_Examples/Cambridge_v090/link.csv). Otherwise, links are open to all modes.

In order to perform multimodal accessibility evaluation, the corresponding modes (i.e., agent types) must be presented in [settings.yml](https://github.com/jdlph/Path4GMNS/blob/master/tests/settings.yml). It will be parsed by [pyyaml](https://pypi.org/project/PyYAML/) (5.1 or higher) to the Python engine at run-time. **Note that demand.csv is not necessary for accessibility evaluation**. Starting from v0.8.3, a flag named "use_link_ffs" is added to each agent in settings.yml. If its value is true, the link free flow speed (from link.csv) will be used in evaluating the link travel time and thus the accessibility. Otherwise, the free_speed of each agent will be taken as default.

```yaml
agents:
  - type: a
    name: auto
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 60
    use_link_ffs: true
  - type: w
    name: walk
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 10
    use_link_ffs: false

demand_periods:
  - period: AM
    time_period: 0700-0800

demand_files:
  - file_name: demand.csv
    period: AM
    agent_type: a
```

If pyyaml is not installed or settings.yml is not provided, one demand period (AM) and one agent type (passenger) will be automatically created.

```python
import path4gmns as pg

network = pg.read_network()

print('\nstart accessibility evaluation\n')
st = time()
# no need to load demand file for accessibility evaluation
pg.evaluate_accessibility(network)

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
```

Two formats of accessibility will be output: accessibility between each OD pair in terms of free flow travel time (od_accessibility.csv) and zone accessibility as to the number of accessible zones from each zone for each transportation mode specified in settings.yml given a budget time (up to 240 minutes) (zone_accessibility.csv). The following example is to evaluate accessibility only under the default mode (i.e., mode auto or agent type passenger).

```python
import path4gmns as pg

network = pg.read_network()

print('\nstart accessibility evaluation\n')
st = time()

pg.evaluate_accessibility(network, single_mode=True)
# the default is under mode auto (i.e., a)
# if you would like to evaluate accessibility under a target mode, say walk, then
# pg.evaluate_accessibility(network, single_mode=True, mode='w')
# or equivalently pg.evaluate_accessibility(network, single_mode=True, mode='walk')

print('complete accessibility evaluation.\n')
print(f'processing time of accessibility evaluation: {time()-st:.2f} s')
```

You can also get the accessible nodes and links within a time budget given a mode. Similar to the accessibility evaluation, the selected mode must come from settings.yml.

```python
import path4gmns as pg

network = pg.read_network()

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'a')
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

network = pg.read_network()

print('\nstart accessibility evaluation\n')
st = time()

# time-dependent accessibility under the default mode auto (i.e., p)
# for demand period 0 (i.e., VDF_fftt1 in link.csv will be used in the evaluation)
pg.evaluate_accessibility(network, single_mode=True, time_dependent=True)

# if you would like to evaluate accessibility under a different demand period
# (say 1, which must be defined in settings.yml along with VDF_fftt2 in link.csv), then
pg.evaluate_accessibility(network, single_mode=True, time_dependent=True, demand_period_id=1)

# if you would like to evaluate accessibility under a target mode, say walk, then
pg.evaluate_accessibility(network, single_mode=True, mode='w', time_dependent=True)
```

While VDF_fftt begins with 1 (i.e., VDF_fftt1), the argument demand_period_id, corresponding to the sequence number of demand period appeared in demand_periods in settings.yml, starts from 0. So "demand_period_id=0" indicates that VDF_fftt1 will be used (and so on and so forth).

**As VDF_fftt in link.csv can only accommodate one mode, time-dependent accessibility evaluation will require the user to prepare a mode-specific link.csv with dedicated VDF_fftt and allowed_uses**. That's the reason that "single_model=True" is always enforced in these examples.

Retrieve the time-dependent accessible nodes and links is similar to evaluate time-dependent accessibility by simply passing time_dependent and demand_period_id to get_accessible_nodes() and get_accessible_links().

```python
import path4gmns as pg

network = pg.read_network()

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'a') for demand period 0
network.get_accessible_nodes(1, 5, time_dependent=True)

# get accessible nodes and links starting from node 1 with a 5-minute
# time window for the default mode auto (i.e., 'a') for demand period 1 if it is defined
network.get_accessible_links(1, 5, time_dependent=True, demand_period_id=1)

# get accessible nodes and links starting from node 1 with a 15-minute
# time window for mode walk (i.e., 'w') for demand periods 0 and 1 respectively
network.get_accessible_nodes(1, 15, 'w', time_dependent=True)
network.get_accessible_links(1, 15, 'w', time_dependent=True, demand_period_id=1)
```
## Evaluate Multimodal Equity

Transportation equity is accessibility with respect to different demographics. Path4GMNS provides the following simple info and statistics on equity given a time budget and a segmentation of zones (e.g., zones can be grouped into a set of bins according to income level and each zone will have a unique bin index). The current implementation takes bin index of each zone from node.csv under column "bin_index" (via node-to-zone mapping), which is error prone. As a zone might have more than one node, it may encounter inconsistent bin indices over a set of nodes corresponding to the same zone. In case of that, the first bin index encountered for each zone in loading node.csv is always used for evaluation. 0 is taken as default if column "bin_index" or the value of an entry is missing.

1. **accessible zones**.
2. **min accessibility**. Each zone has a list of accessible zones given a time budget and a transportation mode. This metric refers to the zone with the minimum number of accessible zones. This number and the zone ID will both be output. Note that there could be multiple zones with the same minimum number of accessible zones and only the first zone will be in the output.
3. **max accessibility**.
4. **mean accessibility**. The average number of accessible zones over a bin of zones (corresponding to a specific demographic) given a time budget and a transportation mode.

They can be obtained via Path4GMNS of v0.8.3 or higher in a way very similar to the process of evaluating accessibility.

```python
import path4gmns as pg

network = pg.read_network()

print('\nstart equity evaluation\n')
st = time()
# multimodal equity evaluation under default time budget (60 min)
pg.evaluate_equity(network)
# equity evaluation for a target mode with time budget as 30 min
# pg.evaluate_equity(network, single_mode=True, mode='a', time_budget=30)

print('complete equity evaluation.\n')
print(f'processing time of equity evaluation: {time()-st:.2f} s')
```

## Conduct Dynamic Traffic Simulation

Traffic simulation is to capture/mimic the traffic evolution over time through some representation of traffic dynamics. The choice of representation varies (including car following models, queueing models, kinematic wave models, etc.) and leads to three types of traffic simulation, which are microscopic, mesoscopic, and macroscopic.

The traffic simulation module in Path4GMNS is a mesoscopic simulator using the point queue model and the routing decision of each individual agent (as disaggregated demand). The routing decisions are from the UE traffic assignment.

The demand loading profile with respect to the departure times of all agents is either constant (start time of the selected demand period) or random (within the selected demand period). The future release will introduce a linear or piece-wise linear loading profile. Path4GMNS only supports one demand period, which must be specified in settings.yml and be corresponding to one from the list of demand_periods. If you need the multi-demand-period support, please use DTALite or [TransOMS](https://github.com/jdlph/TransOMS). The default simulation resolution is 6 seconds. In other words, a simulation interval is 6 seconds.

```yaml
agents:
  - type: a
    name: auto
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 60
    use_link_ffs: true
  - type: w
    name: walk
    vot: 10
    flow_type: 0
    pce: 1
    free_speed: 10
    use_link_ffs: false

demand_periods:
  - period: AM
    time_period: 0700-0800

demand_files:
  - file_name: demand.csv
    period: AM
    agent_type: a

simulation:
  period: AM
  # number of seconds per simulation interval
  resolution: 6
```

find_ue() shall be called in the first place to set up path for each agent before simulation.

```Python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network)

# UE + DTA
column_gen_num = 20
column_upd_num = 20
pg.find_ue(network, column_gen_num, column_upd_num)
pg.perform_simple_simulation(network)
print('complete dynamic simulation.\n')

print('writing agent trajectories')
pg.output_agent_trajectory(network)
```

If you have route_assignment.csv (i.e.columns) from a previous run or DTALite, you can bypass find_ue() and directly load it to conduct simulation.

```python
import path4gmns as pg

# no need to load demand file as we will infer the demand from columns
network = pg.read_network()

# load existing UE result
pg.load_columns(network)

# DTA
pg.perform_simple_simulation(network)
print('complete dynamic simulation.\n')

print('writing agent trajectories')
pg.output_agent_trajectory(network)
```

The original implementation introduced in v0.9.0 (that each agent follows the shortest path from origin to destination) has been disabled. If you are still interested in traffic simulation using shortest paths, it can be achieved by setting column_gen_num as 1 and column_upd_num as 0 illustrated below.

```Python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network)

# the following setting will set up the shortest path for each agent
column_gen_num = 1
column_upd_num = 0
pg.find_ue(network, column_gen_num, column_upd_num)
pg.perform_simple_simulation(network)
print('complete dynamic simulation.\n')

print('writing agent trajectories')
pg.output_agent_trajectory(network)
```

## Synthesize Zones and OD Demand

Zone information is crucial in conducting traffic assignment, evaluating accessibility and equity. When no zone information is provided along node.csv, Path4GMNS can automatically synthesize a total number of {math}`d * d` grids (rectangles) as zones given the dimension {math}`d`.

Activity nodes are randomly sampled for each zone according to a hardcoded sample rate {math}`r`, where {math}`r = max(10, N / 100)` and {math}`N` is the total number of nodes in the network. The total demand, as an input argument, will be allocated to each zone proportionally with respect to the number of its activity nodes, as its synthesized production volume and also attraction volume.

$$prod_i = attr_i = demand \times \frac{N_i^a}{N^a}$$

Where, {math}`prod_i` is the production volume of zone {math}`i`, {math}`attr_i` is the production volume of zone {math}`j`, $demand$ is the total demand, {math}`N^a` is the total number of activity nodes, {math}`N_i^a` is the number of activity nodes in zone {math}`i`.

Denote the minimum travel time from zone {math}`i` to zone {math}`j` under a specific mode as {math}`mintt_{ij}` and introduce the following definition on the set of connected zones from zone {math}`i`, which is cut off by a predefined time budget {math}`b`.

$$ D(i) = \lbrace j: mintt_{ij}\leq b \rbrace $$

With {math}`D(i)`, the allocated demand between zone $i$ and one of its connected zones, {math}`j`, is then defined as follows.

$$ vol_{ij} = prod_i \times \frac{attr_j }{\sum_{\substack{k\in D(i)}}attr_k}$$

Note that we use this forgoing simple procedure to proportionally distribute demand for each OD pair rather than the gravity model and {math}`\sum_{\substack{i,j}} vol_{ij}` might be slightly different from {math}`demand` as a result of rounding errors in the distribution process.

The following code snippet demonstrates how to explicitly synthesize zones and demand.

```Python
import path4gmns as pg

network = pg.read_network()

print('\nstart zone synthesis')
st = time()
# by default, grid_dimension is 8, total_demand is 100,000,
# time_budget is 120 min, mode is 'a'
pg.network_to_zones(network)
pg.output_synthetic_zones(network)
pg.output_synthetic_demand(network)

print('complete zone and demand synthesis.\n')
print(f'processing time of zone and demand synthesis: {time()-st:.2f} s')
```
The synthesized zones and OD demand matrix will be output as syn_zone.csv and syn_demand.csv respectively. They can be loaded as offline files to perform some other functionalities from Path4GMNS (e.g., traffic assignment). The existing zone information, if there is any (e.g., derived from node.csv), will be REWRITTEN upon the following reloading.

```Python
import path4gmns as pg

network = pg.read_network()
pg.read_demand(network, use_synthetic_data=True)

# perform some other functionalities from Path4GMNS, e.g., traffic assignment
column_gen_num = 20
column_upd_num = 20
pg.find_ue(network, column_gen_num, column_upd_num)

pg.output_columns(network)
pg.output_link_performance(network)
```
