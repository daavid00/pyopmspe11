.. _example-hello-world:

Hello world
===========

The repository ``examples`` folder contains low-resolution configurations for
quick testing. Generate and run SPE11B, then write all benchmark data and
figures:

.. code-block:: console

   pyopmspe11 -i spe11b.toml -o spe11b -m all -g all -t 5 -r 50,1,15 -w 1

.. figure:: ../figs/spe11b_tco2_2Dmaps.png
   :alt: SPE11B total CO2 mass over time
   :align: center

   CO2 mass mapped from the corner-point simulation grid to a 50 by 15
   reporting grid.

This deliberately coarse grid runs quickly. See :doc:`../benchmark` for finer
benchmark configurations.

Generate only the OPM input files without running Flow:

.. code-block:: console

   pyopmspe11 -i spe11b.toml -o spe11b -m deck

Change the ``model`` value in the TOML file to create immiscible, isothermal,
and convective cases, then run:

.. code-block:: console

   pyopmspe11 -i immiscible.toml -o immiscible -m deck_flow_data -w 1
   pyopmspe11 -i isothermal.toml -o isothermal -m deck_flow_data -w 1
   pyopmspe11 -i convective.toml -o convective -m deck_flow_data -w 1

Compare the current result folders:

.. code-block:: console

   pyopmspe11 -c spe11b

.. figure:: ../figs/spe11b_sparse_data.png
   :alt: SPE11B sparse-data comparison
   :align: center

.. figure:: ../figs/spe11b_performance.png
   :alt: SPE11B performance comparison
   :align: center

   Immiscible and isothermal simulations run faster because they have fewer
   degrees of freedom.

Use `plopm <https://github.com/cssr-tools/plopm>`_ for additional result
visualization:

.. code-block:: console

   pip install git+https://github.com/cssr-tools/plopm.git
   plopm -i isothermal/flow/ISOTHERMAL -v sgas -t 'Isothermal simulation (end of simulation)'
   plopm -i "immiscible/data/spe11b_time_series convective/data/spe11b_time_series" -csv 1,4 -labels "Immiscible  Convective" -tunits y -ylabel 'mobA [kg]' -xformat .0f -x '[0,25]' -xlnum 6 -f 20 -d 10,5 -yformat .1e -e 'solid,solid' -lw 4 -step 1

.. figure:: ../figs/plopm_hello_world.png
   :alt: Results visualized with plopm
   :align: center

Reproduce this example
----------------------

.. code-block:: console

   . ./tests/scripts/docs_hello_world.sh

.. button-link:: https://github.com/OPM/pyopmspe11/blob/main/tests/scripts/docs_hello_world.sh
   :color: primary
   :outline:

   View script

.. button-ref:: examples
   :ref-type: ref
   :color: secondary
   :outline:

   Back to examples
