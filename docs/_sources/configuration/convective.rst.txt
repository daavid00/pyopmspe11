.. _configuration-convective:

Convective dissolution
======================

The ``convective`` model uses ``drsdtcon`` to generate the OPM ``DRSDTCON``
keyword.

.. _config-drsdtcon:

drsdtcon
---------

**Type:** matrix with seven rows

Each row corresponds to one facies. Use ``[-1.0]`` for default behavior, or set:

1. ``CHI``, dimensionless.
2. ``PSI``, dimensionless.
3. ``OMEGA``, 1/s.
4. ``OPTION``.

.. code-block:: toml

   drsdtcon = [
       [-1.0],
       [0.04, 0.34, 3.0e-09, "ALL"],
       [-1.0],
       [-1.0],
       [0.04, 0.34, 3.0e-09, "ALL"],
       [-1.0],
       [-1.0],
   ]

The example above generates:

.. code-block:: text

   DRSDTCON
   -1.0 /
   0.04 0.34 3.0e-09 ALL /
   -1.0 /
   -1.0 /
   0.04 0.34 3.0e-09 ALL /
   -1.0 /
   -1.0 /
   /

See ``examples/spe11b_convective.toml`` for a complete configuration and
:doc:`../tutorial/modify-model` for a guided comparison.
