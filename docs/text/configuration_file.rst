.. _configuration-file:

Configuration reference
=======================

A configuration file defines the SPE11 case, physical model, grid, initial
conditions, rock and fluid properties, wells, injection schedule, and OPM Flow
command.

Use TOML for new cases. The legacy TXT format remains supported for existing
configurations, but new configuration features are added only to TOML.

Start from a configuration in the `examples
<https://github.com/OPM/pyopmspe11/tree/main/examples>`_ or `benchmark
<https://github.com/OPM/pyopmspe11/tree/main/benchmark>`_ directory. Follow the
:doc:`tutorial` for a guided workflow, and use this section to look up exact
variable meanings, units, accepted values, and restrictions.

Validation
----------

**pyopmspe11** validates the configuration before generating files. Validation
covers required values, types, numeric ranges, array and matrix dimensions,
well coordinates, expressions, saturation and rock properties, injection
schedules, convective-dissolution settings, and case-specific requirements.

.. toctree::
   :maxdepth: 1

   configuration/model
   configuration/grid
   configuration/initial-conditions
   configuration/rock-fluid
   configuration/wells-schedule
   configuration/convective
   configuration/flow
   configuration/complete-example
   configuration/legacy-txt
