.. _tutorial-modify-grid:

Modify the grid
===============

Change the grid type, model dimensions, and spatial refinement, then inspect
the generated deck before running an expensive simulation.

Configure a Cartesian grid
--------------------------

Copy the SPE11B configuration and modify these variables:

.. code-block:: toml

   grid = "cartesian"
   dims = [8400.0, 1.0, 1200.0]
   x_n = [420]
   y_n = [1]
   z_n = [60]

``cartesian``
   Uses one cell count in each direction.

``tensor``
   Uses refinement arrays to divide each direction into regions.

``corner-point``
   Uses lateral refinement arrays and an 11-entry or 18-entry ``z_n`` array
   for the geological levels.

Generate and inspect the deck
-----------------------------

.. code-block:: console

   pyopmspe11 -i modified_grid.toml -o modified_grid -m deck

Inspect the generated grid before running Flow. When ready, reuse the existing
deck and generate benchmark data:

.. code-block:: console

   pyopmspe11 -i modified_grid.toml -o modified_grid -m flow_data

Result
------

.. figure:: ../figs/satnum.png
   :alt: Facies in a generated SPE11 corner-point grid
   :align: center

   Facies generated for an SPE11 corner-point grid.

Next
----

Continue with :doc:`compare-results`. See :doc:`../examples/cp-grids` for a
comparison of 11-level and 18-level corner-point grids, and use
:doc:`../configuration_file` for exact variable definitions.
