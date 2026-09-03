.. _options-layout:

Folders and model region
========================

.. program:: pyopmspe11

-f/--subfolders <0|1>
---------------------

.. option:: -f <0|1>, --subfolders <0|1>
   :no-contents-entry:
   :no-typesetting:

Use ``1`` to create ``deck``, ``flow``, ``data``, and ``figures`` subfolders.
Use ``0`` to write generated files directly in the output folder.

**Default:** ``1``

-n/--neighbourhood <REGION>
---------------------------

.. option:: -n <REGION>, --neighbourhood <REGION>
   :no-contents-entry:
   :no-typesetting:

Set ``lower`` to model the localized lower region. An empty value models the
whole system.

**Default:** empty
