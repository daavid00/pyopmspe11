.. _tutorial-first-deck:

Generate the first deck
=======================

Copy an existing TOML configuration and generate OPM Flow input files without
running a simulation.

Prepare the configuration
-------------------------

Run the tutorial from the repository root. Copy the supplied SPE11B example so
the original file remains unchanged:

.. code-block:: console

   cp examples/spe11b.toml my_spe11b.toml

Generate the deck
-----------------

.. code-block:: console

   pyopmspe11 -i my_spe11b.toml -o my_spe11b -m deck

How it works
------------

:option:`pyopmspe11 -i`
   Selects a TOML or legacy TXT configuration file.

:option:`pyopmspe11 -o`
   Sets the output folder.

:option:`pyopmspe11 -m`
   Selects the workflow. ``deck`` generates OPM Flow input without running the
   simulator.

The command-line options select what **pyopmspe11** does. The TOML variables
define the SPE11 case, physical model, grid, properties, wells, and schedule.

Result
------

With subfolders enabled, the generated input files are written under:

.. code-block:: text

   my_spe11b/
   └── deck/
       ├── MY_SPE11B.DATA
       └── FIPNUM.INC
       └── FLUXNUM.INC
       ├── GRID.INC
       └── PVBOUNDARIES.INC
       └── TABLES.INC

The exact filenames depend on the configuration and generated model.

Next
----

Continue with :doc:`run-flow`. See :doc:`../configuration_file` for TOML
variables and :doc:`../output_folder` for the generated folder structure.
