.. _introduction:

Introduction
============

.. image:: figs/animationspe11a.gif
   :alt: SPE11A simulation generated with pyopmspe11
   :align: center

**pyopmspe11** is a flexible tool for the three cases in the `SPE Comparative
Solution Project <https://www.spe.org/en/csp/>`_. It uses a
:doc:`configuration file <configuration_file>` to generate OPM Flow input, run
simulations, write benchmark data, and create figures.

Core workflows
--------------

* Generate Cartesian, tensor, or corner-point grids.
* Set rock, fluid, well, source, and injection-schedule properties.
* Generate decks without running OPM Flow.
* Run complete SPE11 simulations with OPM Flow.
* Write dense, sparse, performance, and spatial-performance data in benchmark
  format.
* Create standard benchmark figures and compare simulation runs.

Basic usage
-----------

Generate an SPE11B deck and run OPM Flow:

.. code-block:: console

   pyopmspe11 -i examples/spe11b.toml -o spe11b

Use :doc:`command-line` for exact option syntax and :doc:`examples` for
complete workflows.

About the project
-----------------

.. image:: figs/about.png
   :alt: Projects supporting pyopmspe11
   :align: center
   :width: 65%

**pyopmspe11** is funded by the `HPC Simulation Software for the Gigatonne
Storage Challenge project
<https://www.norceresearch.no/en/projects/hpc-simulation-software-for-the-gigatonne-storage-challenge>`_
(project number 622059) and the `Center for Sustainable Subsurface Resources
<https://cssr.no/>`_ (project number 331841).

See the `SPE11 benchmark paper
<https://www.sciencedirect.com/science/article/pii/S1750583625002178>`_ and the
`pyopmspe11 JOSS paper <https://doi.org/10.21105/joss.07357>`_.

Citation
--------

Landa-Marbán, D. and Sandve, T. H. (2025). pyopmspe11: A Python framework
using OPM Flow for the SPE11 benchmark project. *Journal of Open Source
Software*, 10(105), 7357. https://doi.org/10.21105/joss.07357.

Where to continue
-----------------

* Complete the :doc:`installation` and verify the Python package and OPM Flow
  setup.
* Use the :doc:`configuration_file` reference to understand and modify TOML
  variables.
* Follow the :doc:`tutorial` to progress from deck generation to benchmark
  data, plots, and result comparisons.
* Browse :doc:`examples` for corner-point grids, localized domains, and other
  reproducible workflows.
* Explore :doc:`benchmark` to reproduce the OPM team results for SPE11A,
  SPE11B, and SPE11C.
* See :doc:`convergence` for the SPE11B full-domain and lower-domain grid
  refinement studies.
* Review :doc:`output_folder` to understand the generated files and folder
  structure.
* Use :doc:`command-line` for exact CLI syntax, defaults, accepted values, and
  option compatibility.
* Browse :doc:`api` for the public Python modules, classes, and functions.
* See :doc:`contributing` to report issues, request features, or contribute to
  **pyopmspe11**.
* Explore :doc:`related` for complementary open-source tools.
