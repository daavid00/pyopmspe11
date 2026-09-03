.. _tutorial-benchmark-data:

Generate benchmark data
=======================

Process the SPE11B simulation results and write dense, sparse, performance, and
spatial-performance data in the benchmark CSV format.

Command
-------

Use the same reporting settings that will be used to create the figures in the
next lesson:

.. code-block:: console

   pyopmspe11 -i my_spe11b.toml -o my_spe11b -m data -g all -r 50,1,15 -t 5 -w 1

How it works
------------

:option:`pyopmspe11 -m`
   Selects the workflow. ``data`` reads the existing OPM Flow results and
   writes benchmark CSV files without rerunning the simulation.

:option:`pyopmspe11 -g`
   Selects the benchmark data to generate. ``all`` requests every supported
   category.

:option:`pyopmspe11 -r`
   Sets the dense reporting grid to 50 cells in x, 1 in y, and 15 in z.

:option:`pyopmspe11 -t`
   Selects the time used for spatial maps. SPE11A uses hours; SPE11B and
   SPE11C use years.

:option:`pyopmspe11 -w`
   Sets the interval for sparse and performance data.

Simulation and reporting grids
------------------------------

The simulation runs on the grid defined by ``grid``, ``dims``, ``x_n``,
``y_n``, and ``z_n`` in the TOML file. The ``-r`` option defines the regular
grid used for dense benchmark output.

Result
------

With subfolders enabled, simulation output is written under:

.. code-block:: text

   my_spe11b/
   └── deck
   └── flow
   └── data/
       ├── spe11b_performance_spatial_map_0y.csv
       ├── spe11b_performance_spatial_map_5y.csv
       ├── spe11b_performance_spatial_map_10y.csv
       ├── spe11b_performance_spatial_map_15y.csv
       ├── spe11b_performance_spatial_map_20y.csv
       ├── spe11b_performance_spatial_map_25y.csv
       ├── spe11b_performance_time_series_detailed.csv
       ├── spe11b_performance_time_series.csv
       ├── spe11b_spatial_map_0y.csv
       ├── spe11b_spatial_map_5y.csv
       ├── spe11b_spatial_map_10y.csv
       ├── spe11b_spatial_map_15y.csv
       ├── spe11b_spatial_map_20y.csv
       ├── spe11b_spatial_map_25y.csv
       ├── spe11b_time_series.csv

The exact files depend on :option:`pyopmspe11 -g`. They provide the input for
the standard plots created in the next lesson and can also be analyzed with
other applications.

Next
----

Continue with :doc:`benchmark-plots`. See :doc:`../output_folder` for the
output layout and :doc:`../options/reporting` for all reporting options.
