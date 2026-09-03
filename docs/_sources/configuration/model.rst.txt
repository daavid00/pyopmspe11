.. _configuration-model:

Model selection
===============

Select the SPE11 case, OPM Flow compatibility, and physical model.

.. _config-spe11:

spe11
-----

**Type:** string

**Accepted values:** ``spe11a``, ``spe11b``, ``spe11c``

Selects the benchmark case. This controls case-dependent dimensions, time
units, reporting regions, sensor locations, and generated keywords.

.. code-block:: toml

   spe11 = "spe11b"

.. _config-version:

version
-------

**Type:** string

**Accepted values:** ``release``, ``master``

Selects compatibility with the supported OPM Flow stable release or current
master branches. Use ``release`` with OPM Flow Release 2026.04.

.. code-block:: toml

   version = "release"

See :ref:`opm-flow-installation` for installation guidance.

.. _config-model:

model
-----

**Type:** string

**Accepted values:** ``immiscible``, ``isothermal``, ``convective``,
``complete``

Selects the physical model used to generate the deck.

``immiscible``
   Supports faster prototyping without component dissolution.

``isothermal``
   Includes component dissolution but omits thermal effects.

``convective``
   Enables the convective-dissolution model described by ``drsdtcon``.

``complete``
   Includes component dissolution and thermal effects.

.. code-block:: toml

   model = "complete"

See :doc:`convective` for convective-dissolution settings and
:doc:`../tutorial/modify-model` for a comparison workflow.
