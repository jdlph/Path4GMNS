# Path4GMNS
[![platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)
 [![Downloads](https://pepy.tech/badge/path4gmns)](https://pepy.tech/project/path4gmns) [![GitHub release](https://img.shields.io/badge/release-v0.9.0-brightgreen)](https://img.shields.io/badge/release-v0.8.2-brightgreen)

Path4GMNS is an open-source, cross-platform, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides finding static shortest paths for simple analyses, its main functionality is to provide an efficient and flexible framework for column-based (path-based) modeling and applications in transportation (e.g., activity-based demand modeling). Path4GMNS supports, in short,

1. finding (static) shortest path between two nodes,
2. constructing shortest paths for all individual agents,
3. performing path-based User-Equilibrium (UE) traffic assignment,
4. evaluating multimodal accessibility and equity,
5. synthesizing zones and Origin-Destination (OD) demand for a given network.

Path4GMNS also serves as an API to the C++-based [DTALite](https://github.com/jdlph/DTALite) to conduct various multimodal traffic assignments including,
   * Link-based UE,
   * Path-based UE,
   * UE + Dynamic Traffic Assignment (DTA),
   * OD Matrix Estimation (ODME).

![Architecture](/docs/source/imgs/architecture.png)

## Installation
Path4GMNS has been published on [PyPI](https://pypi.org/project/path4gmns/0.9.0/), and can be installed using
```
$ pip install path4gmns
```
If you need a specific version of Path4GMNS, say, 0.9.0,
```
$ pip install path4gmns==0.9.0
```

v0.9.0 introduces mesoscopic traffic simulation using the point queue model. Please **update to or install the latest version** and **discard all old versions**, which could lead to wrong assignment results under certain conditions.

### Dependency
The Python modules are written in **Python 3.x**, which is the minimum requirement to explore the most of Path4GMNS. Some of its functions require further run-time support, which we will go through along with the corresponding [use cases](https://path4gmns.readthedocs.io/en/latest/).

## Quick Start

 We highly recommend that you go through [this tutorial](https://github.com/jdlph/Path4GMNS/tree/dev/tests/tutorial.ipynb) written in Jupyter notebook with step-by-step demonstration using the latest version, no matter you are one of the existing users or new to Path4GMNS.

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
8. Calculate and show up multimodal accessibility (v0.7.0a1)
9. Apply lightweight and faster implementation on accessibility evaluation using virtual centroids and connectors (v0.7.0)
10. Get accessible nodes and links given mode and time budget (v0.7.0)
11. Retrieve shortest paths under multimodal allowed uses (v0.7.2)
12. Time-dependent accessibility evaluation (v0.7.3)
13. Fix crucial bug in accessibility evaluation (v0.7.5)
14. Deprecate node_sum as hash index in column generation (v0.8.0)
15. Optimize class ColumnVec, setup_agents() in class Network, and column generation module (i.e., colgen.py) (v0.8.1)
16. Deep code optimization in column generation module with significant performance improvement (v0.8.2)
17. Let users choose which speed to use in accessibility evaluation (either the free speed of an agent specified in settings.yml or the link free flow speed defined in link.csv) (v0.8.3)
18. Transportation equity evaluation (v0.8.3)
19. Introduce special events with affected links and capacity reductions (v0.8.4)
20. Synthesize zones and demands (v0.8.5)
21. Add support for Apple Silicon (v0.8.5)
22. More robust parsing functions (v0.8.6)
23. Fix crucial bug in column generation module which will lead to wrong results if a zone has multiple nodes (v0.8.6)
24. Fix crucial bug in setting up the capacity of each VDFPeriod instance if the input is missing from link.csv (v0.8.6)
25. Add backwards compatibility on deprecated default agent type of p or passenger (v0.8.7a1)
26. Fix potential issue in setup_spnetwork() which requires zone id's are in ascending order (v0.8.7a1)
27. Fix potential issue that bin_index might not start from zero along with potential zero division issue when all zones have the same number of nodes in _synthesize_bin_index() (v0.8.7a1)
28. Enhance the tutorial with elaboration on the legacy way of loading demand and zone information and some caveats. (v0.8.7a1)
29. Calculate and print out relative gap of UE as convergency measure (v0.8.7)
30. Support the most common length and speed units. See [tutorial](https://github.com/jdlph/Path4GMNS/tree/dev/tests/tutorial.ipynb) for details (v0.8.7)
31. Introduce the simulation module along with a simple traffic simulator using the point queue model and shortest paths (v0.9.0).

Detailed update information can be found in [Releases](https://github.com/jdlph/Path4GMNS/releases).

## Please Contribute

Any contributions are welcomed including advise new applications of Path4GMNS, enhance documentation (this guideline and [docstrings](https://docs.python-guide.org/writing/documentation/#writing-docstrings) in the source code), refactor and/or optimize the source code, report and/or resolve potential issues/bugs, suggest and/or add new functionalities, etc.

Path4GMNS has a very simple workflow setup, i.e., **master for release (on both GitHub and PyPI)** and **dev for development**. If you would like to work directly on the source code (and probably the documentation), please make sure that **the destination branch of your pull request is dev**, i.e., all potential changes/updates shall go to the dev branch before merging into master for release.

You are encouraged to join our [Discord Channel](https://discord.gg/JGFMta7kxZ) and [Gmail group](https://groups.google.com/g/path4gmns) to get the latest update and other information.

## How to Cite

Li, P. and Zhou, X. (2022, October 15). *Path4GMNS*. Retrieved from https://github.com/jdlph/Path4GMNS

## References
Lu, C. C., Mahmassani, H. S., Zhou, X. (2009). Equivalent gap function-based reformulation and solution algorithm for the dynamic user equilibrium problem. Transportation Research Part B: Methodological, 43, 345-364.

Jayakrishnan, R., Tsai, W. K., Prashker, J. N., Rajadyaksha, S. (1994). [A Faster Path-Based Algorithm for Traffic Assignment](https://escholarship.org/uc/item/2hf4541x) (Working Paper UCTC No. 191). The University of California Transportation Center.