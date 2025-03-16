# Path4GMNS
[![platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-red)
[![Downloads](https://static.pepy.tech/badge/path4gmns)](https://pepy.tech/project/path4gmns) [![GitHub release](https://img.shields.io/badge/release-v0.9.10-brightgreen)](https://img.shields.io/badge/release-v0.8.2-brightgreen) ![Read the Docs](https://img.shields.io/readthedocs/path4gmns)
[![](https://dcbadge.vercel.app/api/server/JGFMta7kxZ?style=flast)](https://discord.gg/JGFMta7kxZ)

Path4GMNS is an open-source, cross-platform, lightweight, and fast Python path engine for networks encoded in [GMNS](https://github.com/zephyr-data-specs/GMNS). Besides finding static shortest paths for simple analyses, its main functionality is to provide an efficient and flexible framework for column-based (path-based) modeling and applications in transportation (e.g., activity-based demand modeling). Path4GMNS supports, in short,

1. finding (static) shortest path between two nodes,
2. performing path-based User-Equilibrium (UE) traffic assignment,
3. conducting dynamic traffic assignment (DTA) after UE.
4. evaluating multimodal accessibility and equity,
5. making the Origin-Destination (OD) demand matrix estimation (ODME),
6. synthesizing zones and Origin-Destination (OD) demand.

Path4GMNS also serves as an API to the C++-based [DTALite](https://github.com/jdlph/DTALite) to conduct various multimodal traffic assignments including,
   * Link-based UE,
   * Path-based UE,
   * UE + DTA,
   * ODME.

![Architecture](/docs/source/imgs/architecture.png)

## Quick Start

1. **[Tutorial](https://github.com/jdlph/Path4GMNS/blob/master/tutorial/tutorial.ipynb)** written in Jupyter notebook with step-by-step demonstration.
2. **[Documentation](https://path4gmns.readthedocs.io/en/stable/)** on Installation, Use Cases, Public API, and more.
3. **[TransOMS](https://github.com/jdlph/TransOMS)** on the C++ equivalent.

We highly recommend that you go through the above [Tutorial](https://github.com/jdlph/Path4GMNS/blob/master/tutorial/tutorial.ipynb), no matter you are one of the existing users or new to Path4GMNS.

## Installation
Path4GMNS has been published on [PyPI](https://pypi.org/project/path4gmns/0.9.10/), and can be installed using
```
$ pip install path4gmns
```

> [!IMPORTANT]
> v0.9.10 comes with bug fix on [find_shortest_path()](https://github.com/jdlph/Path4GMNS/issues/58), new functionality on obtaining the shortest path tree, and performance improvement on the UE module. Please **discard all old versions**.

> [!WARNING]
> find_shortest_path() computes the shortest path per travel time rather than distance for v0.9.9.post1 and any earlier versions. See [Issue #58](https://github.com/jdlph/Path4GMNS/issues/58) for details. v0.9.10 offers the correct implementation with the flexibility to switch between time and distance.

> [!WARNING]
> Invoking find_shortest_path() and find_ue() in the same code snippet will lead to [OSError: exception: access violation reading ...](https://github.com/jdlph/Path4GMNS/issues/51#issue-2601430024) for v0.9.9 and any version before.

> [!CAUTION]
> Any version prior to v0.9.4 will generate INCORRECT simulation results.

> [!CAUTION]
> Calling DTALite and synthesizing zones and OD demand are not functioning for [v0.9.5 and v0.9.6](https://github.com/jdlph/Path4GMNS/issues/41).

> [!CAUTION]
> Zone and demand synthesis is PROBLEMATIC for any version before v0.9.9.

> [!NOTE]
> ODME is available with v0.9.9 and higher.

### Dependency
The Python modules are written in **Python 3.x**, which is the minimum requirement to explore the most of Path4GMNS. Some of its functions require further run-time support, which we will go through along with the corresponding **[Use Cases](https://path4gmns.readthedocs.io/en/stable/)**.

## How to Cite

Li, P. and Zhou, X. (2025, March 16). *Path4GMNS*. Retrieved from https://github.com/jdlph/Path4GMNS

## Please Contribute

Any contributions are welcomed including advise new applications of Path4GMNS, enhance documentation and [docstrings](https://docs.python-guide.org/writing/documentation/#writing-docstrings) in the source code, refactor and/or optimize the source code, report and/or resolve potential issues/bugs, suggest and/or add new functionalities, etc.

Path4GMNS has a very simple workflow setup, i.e., **master for release (on both GitHub and PyPI)** and **dev for development**. If you would like to work directly on the source code (and probably the documentation), please make sure that **the destination branch of your pull request is dev**, i.e., all potential changes/updates shall go to the dev branch before merging into master for release.

You are encouraged to join our **[Discord Channel](https://discord.gg/JGFMta7kxZ)** for the latest update and more discussions.

## References
Lu, C. C., Mahmassani, H. S., Zhou, X. (2009). [Equivalent gap function-based reformulation and solution algorithm for the dynamic user equilibrium problem](https://www.sciencedirect.com/science/article/abs/pii/S0191261508000829). Transportation Research Part B: Methodological, 43, 345-364.

Jayakrishnan, R., Tsai, W. K., Prashker, J. N., Rajadyaksha, S. (1994). [A Faster Path-Based Algorithm for Traffic Assignment](https://escholarship.org/uc/item/2hf4541x) (Working Paper UCTC No. 191). The University of California Transportation Center.

Bertsekas, D., Gafni, E. (1983). [Projected Newton methods and optimization of multicommodity flows](https://web.mit.edu/dimitrib/www/Gafni_Newton.pdf). IEEE Transactions on Automatic Control, 28(12), 1090–1096.