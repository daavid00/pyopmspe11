.. _tutorial-modify-model:

Modify the physical model
=========================

Create SPE11B configurations with different physical models and compare their
runtime and benchmark results.

Create the configurations
-------------------------

Copy the example configuration:

.. code-block:: console

   cp examples/spe11b.toml immiscible.toml
   cp examples/spe11b.toml isothermal.toml
   cp examples/spe11b.toml convective.toml

Set ``model`` in each file:

.. code-block:: toml

   model = "immiscible"

Use ``isothermal`` and ``convective`` in the corresponding files. The supplied
SPE11B configuration can be retained as the ``complete`` case.

The supported models are:

``immiscible``
   Supports fast prototyping without component dissolution.

``isothermal``
   Includes component dissolution but omits thermal effects.

``convective``
   Enables the convective-dissolution model.

``complete``
   Includes component dissolution and thermal effects.

Run the cases
-------------

.. code-block:: console

   pyopmspe11 -i immiscible.toml -o immiscible -m deck_flow_data -w 1
   pyopmspe11 -i isothermal.toml -o isothermal -m deck_flow_data -w 1
   pyopmspe11 -i convective.toml -o convective -m deck_flow_data -w 1

Result
------

.. figure:: ../figs/spe11b_sparse_data.png
   :alt: Sparse-data comparison of SPE11B physical models
   :align: center

.. figure:: ../figs/spe11b_performance.png
   :alt: Performance comparison of SPE11B physical models
   :align: center

   Models with fewer degrees of freedom generally run faster.

Next
----

Continue with :doc:`modify-grid`. See the model section in
:doc:`../configuration_file` for the complete definitions and convective-model
settings.
