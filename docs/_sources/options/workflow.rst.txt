.. _options-workflow:

Input and workflow
==================

.. program:: pyopmspe11

-i/--input <FILE>
-----------------

.. option:: -i <FILE>, --input <FILE>
   :no-contents-entry:
   :no-typesetting:

Set the TOML or legacy TXT configuration file. The file cannot be empty and
must end in ``.toml`` or ``.txt``.

**Default:** ``input.toml``

-m/--mode <MODE>
----------------

.. option:: -m <MODE>, --mode <MODE>
   :no-contents-entry:
   :no-typesetting:

Select the workflow stages. Accepted values are ``deck``, ``flow``, ``data``,
``plot``, ``deck_flow``, ``flow_data``, ``data_plot``, ``deck_flow_data``,
``flow_data_plot``, and ``all``.

The reporting options ``-g``, ``-r``, ``-t``, and ``-w`` can only be changed
when the selected mode writes benchmark data or figures.

**Default:** ``deck_flow``

-c/--compare <CASE>
-------------------

.. option:: -c <CASE>, --compare <CASE>
   :no-contents-entry:
   :no-typesetting:

Generate common plots for the current ``spe11a``, ``spe11b``, or ``spe11c``
folders. This is a standalone workflow and cannot be combined with non-default
values of ``-i``, ``-m``, ``-o``, ``-t``, ``-r``, ``-g``, ``-w``, ``-f``, or
``-n``.

**Default:** empty

-o/--output <FOLDER>
--------------------

.. option:: -o <FOLDER>, --output <FOLDER>
   :no-contents-entry:
   :no-typesetting:

Set the output folder. The value cannot be empty.

**Default:** ``output``
