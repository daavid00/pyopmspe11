.. _example-cp-grids:

Corner-point grids with 11 and 18 levels
========================================

**pyopmspe11** supports the 18-level SPE11 corner-point grid and the more
regular 11-level grid used in recent FluidFlower history-matching work.

Prepare the configurations
--------------------------

Use ``examples/spe11b.toml`` for the 18-level grid. Its ``z_n`` array contains
one refinement value for each of the 18 geological levels.

Create ``spe11b_11-levels.toml`` from the same file and replace ``z_n`` with
the following 11-entry array:

.. code-block:: toml

   z_n = [2, 2, 2, 3, 2, 2, 8, 4, 8, 8, 1]

Each entry sets the vertical refinement within one geological level. The
number of entries selects the bundled corner-point geometry: 11 entries use
the 11-level reference mesh, while 18 entries use the standard 18-level SPE11
reference mesh.

Run the cases
-------------

Set :option:`pyopmspe11 -f` to ``0`` to write the generated deck and
simulation files directly in each output folder:

.. code-block:: console

   pyopmspe11 -i spe11b.toml -o 18_levels -f 0
   pyopmspe11 -i spe11b_11-levels.toml -o 11_levels -f 0

Compare cell thickness
----------------------

Use plopm to compare ``dz`` for both grids:

.. code-block:: console

   plopm -i '18_levels/18_LEVELS 11_levels/11_LEVELS' -v dz -sg 2,1 -rdl 1 -asp 0 -st 0 -ge 'black,1e-2' -cbp 0.35,0.97,0.3,0.02

.. image:: ../figs/11_levels_dz_i,1,k_t5.png
   :alt: SPE11B corner-point grids with 11 and 18 geological levels
   :align: center

The figure compares the cell thicknesses generated with the standard 18-level
grid and the more regular 11-level grid.

See :ref:`config-z-n` for the ``z_n`` definition and
:doc:`../configuration/grid` for all grid and refinement variables.

Reproduce this example
----------------------

Run the maintained script from the repository root:

.. code-block:: console

   . ./tests/scripts/docs_cp_grids.sh

.. button-link:: https://github.com/OPM/pyopmspe11/blob/main/tests/scripts/docs_cp_grids.sh
   :color: primary
   :outline:

   View script

.. button-ref:: examples
   :ref-type: ref
   :color: secondary
   :outline:

   Back to examples
