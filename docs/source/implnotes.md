# Implementation Notes

The column generation scheme in Path4GMNS is an equivalent **single-processing implementation** as its [DTALite](https://github.com/jdlph/DTALite/tree/main/src_cpp) multiprocessing counterpart. **Note that** the results (i.e., column pool and trajectory for each agent) from Path4GMNS and DTALite are comparable but likely not identical as the shortest paths are usually not unique and subjected to implementations. This difference shall be subtle and the link performances shall be consistent if the iterations of column generation and column update are both large enough. You can always compare the results (i.e., link_performance.csv) from Path4GMNS and DTALite given the same network and demand.

The whole package is implemented towards **high performance**. The core shortest-path engine is implemented in C++ (deque implementation of the modified label correcting algorithm) along with the equivalent Python implementations for demonstration. To achieve the maximum efficiency, we use a fixed-length array as the deque (rather than the STL deque) and combine the scan eligible list (represented as deque) with the node presence status. Along with the minimum and fast argument interfacing between the underlying C++ path engine and the upper Python modules, its running time is comparable to the pure C++-based DTALite for small- and medium-size networks (e.g., the Chicago Sketch Network) without multiprocessing. If you have an extremely large network and/or have requirement on CPU time, we recommend using DTALite to fully utilize its parallel computing feature.

An easy and smooth installation process by **low dependency** is one of our major design goals. The core Python modules in Path4GMNS only require a handful of components from the Python standard library (e.g., csv, ctypes, and so on) with no any third-party libraries/packages. On the C++ side, the precompiled path engines as shared libraries are embedded to make this package portable across three major desktop environments (i.e., Windows, macOS, and Linux) and its source is implemented in C++11 with no dependency. Users can easily build the path engine from the source code towards their target system if it is not listed above as one of the three.

### More on the Column-Generation Module
**The column generation module first identifies new columns (i.e., paths) between each OD pair at each iteration and adds them into the column pool before optimizing (i.e., shifting flows among columns to achieve the equilibrium state)**. The original implementations in both DTALite and Path4GMNS (prior to v0.8.0) rely on node sum as the unique key (or hash index) to differentiate columns, which is simply the summation of node sequence numbers along a column. However, it cannot guarantee that a non-existing column will always be added to the column pool as different columns may share the same node sum (and we presume a one-to-one mapping from node sum to column rather than an array of slots for different columns with the same node sum). An example would be 0->1->4->5 and 0->2->3->5, where 0 to 5 are node sequence numbers. One of the columns will be precluded from the column pool.

In order to resolve this issue, we have deprecated node sum and introduced a side-by-side column comparison in Path4GMNS only. As columns between an OD pair are largely different in number of nodes, this comparison can be very efficiently. Slight improvements are actually observed in both running time and convergence gap over the original implementation.

DTALite uses arrays rather than STL containers to store columns. These arrays are fixed in size (1,000), which prevents a fast filtering using the number of nodes as described above. For two (long) columns only different in the last few nodes, this side-by-side comparison has to be continued until the very end and ruins the performance. Thus, we decide **NOT TO ADOPT** this updated implementation to DTALite and leave it to **[TransOMS](https://github.com/jdlph/TransOMS)**.