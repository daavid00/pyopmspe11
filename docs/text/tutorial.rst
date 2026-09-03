.. _tutorial:

Tutorial
========

Learn **pyopmspe11** by creating and modifying an SPE11B case. Start by
generating an OPM Flow deck, then run the simulation, write benchmark data,
create standard figures, change the physical model and grid, and compare
results.

Before starting, complete the :doc:`installation`. OPM Flow is required from
Lesson 2 onward; see :ref:`opm-flow-installation`.

.. tip::

   Lessons 1 through 4 can be run as one workflow with ``-m all``:

   .. code-block:: console

      pyopmspe11 -i my_spe11b.toml -o my_spe11b -m all -g all -r 50,1,15 -t 5 -w 1

Reproduce the tutorial
----------------------

Run the complete tutorial from the repository root:

.. code-block:: console

   . ./tests/scripts/docs_tutorial.sh

.. button-link:: https://github.com/OPM/pyopmspe11/blob/main/tests/scripts/docs_tutorial.sh
   :color: primary
   :outline:

   View tutorial script

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item-card:: 1. Generate the first deck
      :link: tutorial-first-deck
      :link-type: ref

      Copy an example configuration and generate OPM Flow input files.

   .. grid-item-card:: 2. Run OPM Flow
      :link: tutorial-run-flow
      :link-type: ref

      Configure the Flow command and run the simulation.

   .. grid-item-card:: 3. Generate benchmark data
      :link: tutorial-benchmark-data
      :link-type: ref

      Write dense, sparse, performance, and spatial-performance CSV files.

   .. grid-item-card:: 4. Create benchmark plots
      :link: tutorial-benchmark-plots
      :link-type: ref

      Generate the standard figures from the benchmark CSV files.

   .. grid-item-card:: 5. Modify the physical model
      :link: tutorial-modify-model
      :link-type: ref

      Compare immiscible, isothermal, convective, and complete models.

   .. grid-item-card:: 6. Modify the grid
      :link: tutorial-modify-grid
      :link-type: ref

      Change the grid type, dimensions, and refinement.

   .. grid-item-card:: 7. Compare results
      :link: tutorial-compare-results
      :link-type: ref

      Compare completed runs and continue to advanced workflows.

.. toctree::
   :hidden:
   :maxdepth: 1

   tutorial/first-deck
   tutorial/run-flow
   tutorial/benchmark-data
   tutorial/benchmark-plots
   tutorial/modify-model
   tutorial/modify-grid
   tutorial/compare-results