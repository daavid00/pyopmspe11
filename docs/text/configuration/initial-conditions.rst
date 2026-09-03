.. _configuration-initial-conditions:

Initial conditions and boundaries
=================================

Set temperature, pressure, transport properties, and case-specific boundary
conditions.

.. _config-temperature:

temperature
-----------

**Type:** array of two numbers

**Units:** degrees Celsius

Sets the bottom and top-rig temperatures.

.. code-block:: toml

   temperature = [70.0, 36.12]

.. _config-datum:

datum
-----

**Type:** number

**Units:** m

Sets the depth of the pressure datum.

.. code-block:: toml

   datum = 300

.. _config-pressure:

pressure
--------

**Type:** positive number

**Units:** Pa

Sets pressure at ``datum``.

.. code-block:: toml

   pressure = 3e7

.. _config-diffusion:

diffusion
---------

**Type:** array of two non-negative numbers

**Units:** m²/s

Sets molecular diffusion in the liquid and gas phases, in that order.

.. code-block:: toml

   diffusion = [1e-9, 2e-8]

.. _config-spe11a-bc:

spe11aBC
--------

**Type:** non-negative number

**Units:** m³

**Applies to:** SPE11A

Sets added pore volume on the top boundary. A value of ``0`` uses the free-flow
boundary condition.

.. code-block:: toml

   spe11aBC = 0

.. _config-pv-added:

pvAdded
-------

**Type:** non-negative number

**Units:** m

**Applies to:** SPE11B and SPE11C

Sets extra pore volume per unit area on the lateral boundaries.

.. code-block:: toml

   pvAdded = 5e4

.. _config-width-buffer:

widthBuffer
-----------

**Type:** positive number

**Units:** m

**Applies to:** SPE11B and SPE11C

Sets the width of the lateral buffer cells.

.. code-block:: toml

   widthBuffer = 1
