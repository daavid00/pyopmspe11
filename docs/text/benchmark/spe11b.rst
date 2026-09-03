.. _benchmark-spe11b:

SPE11B
======

SPE11B is a two-dimensional field-scale case. The configurations compare
Cartesian and corner-point grids, a convective-dissolution model, and a fine
1 m reference simulation.

Configurations
--------------

``r1_Cart_10m``
   Uniform 10 m Cartesian grid with 1 m cells at the left and right boundaries.

``r2_cp_10mish``
   Corner-point grid with an approximate cell size of 10 m and 1 m boundary
   cells.

``r3_cp_10mish_convective``
   Approximate 10 m corner-point grid using the convective-dissolution model
   for facies 2 and 5.

``r4_Cart_1m``
   Uniform 1 m Cartesian grid.

Run the cases
-------------

Run these commands from the ``benchmark/spe11b`` directory:

.. code-block:: console

   pyopmspe11 -i r1_Cart_10m.toml -o r1_Cart_10m -m all -g all -r 840,1,120 -t 5 -w 0.1
   pyopmspe11 -i r2_cp_10mish.toml -o r2_cp_10mish -m all -g all -r 840,1,120 -t 5 -w 0.1
   pyopmspe11 -i r3_cp_10mish_convective.toml -o r3_cp_10mish_convective -m all -g all -r 840,1,120 -t 5 -w 0.1
   pyopmspe11 -i r4_Cart_1m.toml -o r4_Cart_1m -m all -g all -r 840,1,120 -t 5 -w 0.1

See :option:`pyopmspe11 -m`, :option:`pyopmspe11 -g`,
:option:`pyopmspe11 -r`, :option:`pyopmspe11 -t`, and
:option:`pyopmspe11 -w`.

Key observations
----------------

For quantities reported in box A, the convective model in ``r3`` compares well
with the fine-scale ``r4`` simulation while running approximately 500 times
faster.

The convective implementation continues to be improved for regions where
dissolved CO2 accumulates. See `Mykkeltvedt et al. (2025)
<https://link.springer.com/article/10.1007/s11242-024-02141-5>`_ for the model
description.

Results
-------

Performance data
++++++++++++++++

.. figure:: ../figs/benchmark_spe11b_performance.png
   :alt: SPE11B performance benchmark results
   :align: center

Sparse data
+++++++++++

.. figure:: ../figs/benchmark_spe11b_sparse_data.png
   :alt: SPE11B sparse benchmark results
   :align: center

Spatial maps
++++++++++++

.. figure:: ../figs/massfractb.png
   :alt: SPE11B liquid-phase CO2 mass-fraction maps
   :align: center

Continue
--------

* See :doc:`../configuration_file` for configuration-variable definitions.
* Follow the :doc:`../tutorial` for a guided introductory workflow.
* Use :doc:`plopm-visualization` to reproduce the simulation-grid maps.
* See :doc:`../convergence` for the SPE11B grid-refinement study.

.. button-ref:: benchmark
   :ref-type: ref
   :color: primary
   :outline:

   Back to the benchmark gallery
