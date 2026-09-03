.. _options-reporting:

Benchmark data and reporting
============================

.. program:: pyopmspe11

-t/--time <TIMES>
-----------------

.. option:: -t <TIMES>, --time <TIMES>
   :no-contents-entry:
   :no-typesetting:

Set one or more non-negative times for spatial maps. Use hours for SPE11A and
years for SPE11B and SPE11C. Separate multiple times with commas.

**Default:** ``5``

-r/--resolution <X,Y,Z>
-----------------------

.. option:: -r <X,Y,Z>, --resolution <X,Y,Z>
   :no-contents-entry:
   :no-typesetting:

Set three positive integers defining the dense reporting-grid resolution.

**Default:** ``8,1,5``

-g/--generate <TYPE>
--------------------

.. option:: -g <TYPE>, --generate <TYPE>
   :no-contents-entry:
   :no-typesetting:

Select the benchmark data to generate. Accepted values are ``dense``,
``sparse``, ``performance``, ``performance-spatial``, ``dense_performance``,
``dense_sparse``, ``performance_sparse``, ``dense_performance-spatial``,
``dense_performance_sparse``, and ``all``.

**Default:** ``performance_sparse``

-w/--write <INTERVAL>
---------------------

.. option:: -w <INTERVAL>, --write <INTERVAL>
   :no-contents-entry:
   :no-typesetting:

Set a positive time interval for sparse and performance data. Use hours for
SPE11A and years for SPE11B and SPE11C.

**Default:** ``0.1``
