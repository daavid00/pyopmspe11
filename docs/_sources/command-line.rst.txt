.. _command-line-reference:

Command-line reference
======================

A **pyopmspe11** command selects a configuration file and one or more workflow
stages:

.. code-block:: console

   pyopmspe11 -i CONFIGURATION [OPTIONS]

For example:

.. code-block:: console

   pyopmspe11 -i examples/spe11b.toml -o spe11b -m deck_flow_data

Use ``pyopmspe11 --help`` for the options supported by the installed version.

.. toctree::
   :maxdepth: 1

   options/workflow
   options/reporting
   options/layout
