.. _benchmark-spe11a:

SPE11A
======

SPE11A is the laboratory-scale benchmark case. These configurations compare
Cartesian and corner-point grids, two capillary-pressure limits, and solver
tolerances.

Configurations
--------------

``r1_Cart_1cm``
   Uniform Cartesian grid with a cell size of 1 cm.

``r2_Cart_1cm_capmax2500Pa``
   Uniform 1 cm Cartesian grid with a maximum capillary pressure of 2500 Pa
   instead of 95000 Pa.

``r3_cp_1cmish_capmax2500Pa``
   Corner-point grid with an approximate cell size of 1 cm and a maximum
   capillary pressure of 2500 Pa.

``r4_Cart_1mm_capmax2500Pa``
   Uniform 1 mm Cartesian grid with a maximum capillary pressure of 2500 Pa.

``r5_Cart_1mm_capmax2500Pa_strictol``
   Uniform 1 mm Cartesian grid with stricter solver tolerances and a maximum
   capillary pressure of 2500 Pa.

Run the cases
-------------

Run these commands from the ``benchmark/spe11a`` directory:

.. code-block:: console

   pyopmspe11 -i r1_Cart_1cm.toml -o r1_Cart_1cm -m all -g all -t 1 -r 280,1,120 -w 0.16666666666666666
   pyopmspe11 -i r2_Cart_1cm_capmax2500Pa.toml -o r2_Cart_1cm_capmax2500Pa -m all -g all -t 1 -r 280,1,120 -w 0.16666666666666666
   pyopmspe11 -i r3_cp_1cmish_capmax2500Pa.toml -o r3_cp_1cmish_capmax2500Pa -m all -g all -t 1 -r 280,1,120 -w 0.16666666666666666
   pyopmspe11 -i r4_Cart_1mm_capmax2500Pa.toml -o r4_Cart_1mm_capmax2500Pa -m all -g all -t 1 -r 280,1,120 -w 0.16666666666666666
   pyopmspe11 -i r5_Cart_1mm_capmax2500Pa_strictol.toml -o r5_Cart_1mm_capmax2500Pa_strictol -m all -g all -t 1 -r 280,1,120 -w 0.16666666666666666

These commands generate decks, run OPM Flow, write all benchmark data, and
create the standard figures. See :option:`pyopmspe11 -m`,
:option:`pyopmspe11 -g`, :option:`pyopmspe11 -t`,
:option:`pyopmspe11 -r`, and :option:`pyopmspe11 -w`.

Key observations
----------------

* Reducing the maximum capillary pressure from 95000 Pa to 2500 Pa has little
  effect on the reported results when comparing ``r1`` and ``r2``, while
  reducing simulation time.
* The approximate 1 cm corner-point grid in ``r3`` compares well with the fine
  1 mm Cartesian case in ``r4``.
* The stricter tolerances in ``r5`` improve mass-balance behavior compared with
  ``r4``, but increase runtime.
* This illustrates the trade-off between simulation cost and accuracy,
  particularly for optimization studies requiring many runs.

See the `SPE11 CSP description
<https://onepetro.org/SJ/article/29/05/2507/540636/The-11th-Society-of-Petroleum-Engineers>`_
for the benchmark context.

Results
-------

Performance data
++++++++++++++++

.. figure:: ../figs/benchmark_spe11a_performance.png
   :alt: SPE11A performance benchmark results
   :align: center

Sparse data
+++++++++++

.. figure:: ../figs/benchmark_spe11a_sparse_data.png
   :alt: SPE11A sparse benchmark results
   :align: center

Spatial maps
++++++++++++

.. figure:: ../figs/massfracta.png
   :alt: SPE11A liquid-phase CO2 mass-fraction maps
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
