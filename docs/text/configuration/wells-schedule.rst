.. _configuration-wells-schedule:

Wells and injection schedule
============================

Define source or well geometry and the time-dependent injection schedule.

.. _config-radius:

radius
------

**Type:** array with two non-negative numbers

**Units:** m

Sets the radius for wells 1 and 2. A value of ``0`` uses the OPM ``SOURCE``
keyword instead of well keywords.

.. code-block:: toml

   radius = [0.15, 0.15]

.. _config-well-coord:

wellCoord
---------

**Type:** matrix with two rows and three columns

**Units:** m

Sets the initial ``x``, ``y``, and ``z`` coordinates for wells 1 and 2. The
coordinates must lie inside ``dims``.

.. code-block:: toml

   wellCoord = [
       [2700.0, 1000.0, 300.0],
       [5100.0, 1000.0, 700.0],
   ]

.. _config-well-coord-final:

wellCoordF
----------

**Type:** matrix with two rows and three columns

**Units:** m

**Applies to:** SPE11C

Sets final ``x``, ``y``, and ``z`` coordinates for the well trajectories. Rows
correspond to the same wells as ``wellCoord``.

.. code-block:: toml

   wellCoordF = [
       [2700.0, 4000.0, 300.0],
       [5100.0, 4000.0, 700.0],
   ]

.. _config-inj:

inj
---

**Type:** matrix with at least eight columns

Defines the injection schedule. Time is in hours for SPE11A and years for
SPE11B and SPE11C. Each row contains:

1. Duration.
2. Time-step interval for writing results.
3. Injected fluid for well 1: ``0`` for water or ``1`` for CO2.
4. Injection rate for well 1, kg/s.
5. Injection temperature for well 1, degrees Celsius.
6. Injected fluid for well 2: ``0`` for water or ``1`` for CO2.
7. Injection rate for well 2, kg/s.
8. Injection temperature for well 2, degrees Celsius.
9. Optional OPM ``TUNING`` values as a string.

.. code-block:: toml

   inj = [
       [999.9, 999.9, 1, 0, 10, 1, 0, 10],
       [0.1, 0.1, 1, 0, 10, 1, 0, 10],
       [25, 5, 1, 0.035, 10, 1, 0, 10],
       [25, 5, 1, 0.035, 10, 1, 0.035, 10],
       [950, 5, 1, 0, 10, 1, 0, 10],
   ]

TUNING values
-------------

When ``--enable-tuning=true`` is present in ``flow``, append TUNING values to
a schedule row. For example, set a maximum time step of 10 days with:

.. code-block:: toml

   inj = [
       [25, 5, 1, 50, 10, 1, 0, 10, "1* 10"],
   ]

The first value is defaulted with ``1*`` and the second corresponds to
``TSMAXZ``. OPM TUNING time quantities are in days for all three SPE cases.
See the `OPM Flow manual <https://opm-project.org/?page_id=955>`_ for the 34
TUNING options and their defaults.
