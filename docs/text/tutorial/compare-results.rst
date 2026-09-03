.. _tutorial-compare-results:

Compare results
===============

Compare completed SPE11B result folders with the standalone comparison
workflow.

Command
-------

Run the command from the directory containing the result folders:

.. code-block:: console

   pyopmspe11 -c spe11b

How it works
------------

:option:`pyopmspe11 -c`
   Searches the current folders for results from ``spe11a``, ``spe11b``, or
   ``spe11c`` and writes common comparison figures.

Comparison mode is standalone. It cannot be combined with non-default values
for the normal input, output, mode, reporting, subfolder, or neighbourhood
options.

Result
------

Comparison figures are written under:

.. code-block:: text

   compare/

.. figure:: ../figs/spe11b_sparse_data.png
   :alt: Comparison of SPE11B sparse-data results
   :align: center

.. figure:: ../figs/spe11b_performance.png
   :alt: Comparison of SPE11B performance results
   :align: center

Next steps
----------

* Browse :doc:`../examples` for corner-point-grid and localized-domain
  workflows.
* Use :doc:`../benchmark` to reproduce the SPE11 benchmark cases.
* See :doc:`../convergence` for grid-refinement and participant comparisons.
* Use :doc:`../configuration_file` to look up TOML variables.
* See :doc:`../output_folder` for the generated file structure.
