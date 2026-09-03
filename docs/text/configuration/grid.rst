.. _configuration-grid:

Grid and geometry
=================

Define the model dimensions, grid type, refinement, and SPE11C geometry.

.. _config-grid:

grid
----

**Type:** string

**Accepted values:** ``cartesian``, ``tensor``, ``corner-point``

Selects the grid geometry.

``cartesian``
   Uses one cell count in each direction.

``tensor``
   Uses refinement arrays to divide each direction into regions.

``corner-point``
   Uses lateral refinement arrays and either 11 or 18 geological levels in
   ``z_n``. The layer geometry is taken from the bundled reference meshes.

.. code-block:: toml

   grid = "corner-point"

.. _config-dims:

dims
----

**Type:** array of three positive numbers

**Units:** m

Sets model length, width, and depth in ``x``, ``y``, and ``z`` order.

.. code-block:: toml

   dims = [8400.0, 5000.0, 1200.0]

.. _config-x-n:

x_n
---

**Type:** non-empty array of positive integers

Sets x-direction cell counts or regional refinement, depending on ``grid``.

.. code-block:: toml

   x_n = [420]

.. _config-y-n:

y_n
---

**Type:** non-empty array of positive integers

Sets y-direction cell counts or regional refinement. SPE11C commonly uses one
value for each lateral region.

.. code-block:: toml

   y_n = [30, 40, 50, 40, 30]

.. _config-z-n:

z_n
---

**Type:** non-empty array of positive integers

Sets z-direction cell counts or refinement. For corner-point grids, use an
array with 11 or 18 entries. Each entry sets refinement within one geological
level.

.. code-block:: toml

   z_n = [5, 3, 1, 2, 3, 2, 4, 4, 10, 4, 6, 6, 4, 8, 4, 15, 30, 9]

.. _config-elevation:

elevation
---------

**Type:** non-negative number

**Units:** m

**Applies to:** SPE11C

Sets the maximum elevation difference of the arch in the y direction relative
to the baseline gradient.

.. code-block:: toml

   elevation = 150

.. _config-back-elevation:

backElevation
-------------

**Type:** number

**Units:** m

**Applies to:** SPE11C

Sets the back-boundary elevation relative to the front boundary.

.. code-block:: toml

   backElevation = 10

Generated regions
-----------------

.. figure:: ../figs/satnum.png
   :alt: Facies in a generated SPE11 corner-point grid
   :align: center

.. figure:: ../figs/fipnum.png
   :alt: Reporting regions in a generated SPE11 corner-point grid
   :align: center

   The facies and FIP regions identify geological units, benchmark boxes,
   sensors, wells, and reporting regions.

See :doc:`../tutorial/modify-grid` for a guided workflow and
:doc:`../examples/cp-grids` for 11-level and 18-level grids.
