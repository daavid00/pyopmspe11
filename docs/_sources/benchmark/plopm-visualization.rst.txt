.. _benchmark-plopm-visualization:

Visualizing benchmark results with plopm
========================================

The benchmark pages show spatial maps on the simulation grids rather than on
the regular benchmark reporting grids. The commands below reproduce those
figures with `plopm <https://github.com/cssr-tools/plopm>`_.

Install plopm
-------------

.. code-block:: console

   pip install git+https://github.com/cssr-tools/plopm.git

SPE11A
------

Run from ``benchmark/spe11a`` after completing the simulations:

.. code-block:: console

   plopm -v xco2l -i 'r1_Cart_1cm/flow/R1_CART_1CM r2_Cart_1cm_capmax2500Pa/flow/R2_CART_1CM_CAPMAX2500PA r3_cp_1cmish_capmax2500Pa/flow/R3_CP_1CMISH_CAPMAX2500PA r4_Cart_1mm_capmax2500Pa/flow/R4_CART_1MM_CAPMAX2500PA' -dpi 300 -c cet_diverging_protanopic_deuteranopic_bwy_60_95_c32 -cbn 3 -xnt 8 -cbl 'SPE11A: CO$_2$ mass fraction (liquid phase) after 1 day' -fs 16,6.5 -t 'r1 Cart 1cm  r2 Cart 1cm capmax 2500 Pa  r3 cp 1cmish capmax 2500 Pa  r4 Cart 1mm capmax 2500 Pa' -yu cm -xu cm -yf .0f -xf .0f -r 29 -fn massfracta -cbf .2e -mv satnum -mt 7e-5 -st 0 -sg 2,2 -cbp 0.35,0.97,0.3,0.02 -rdl 1

.. figure:: ../figs/massfracta.png
   :alt: SPE11A simulation-grid spatial maps
   :align: center

SPE11B
------

Run from ``benchmark/spe11b``:

.. code-block:: console

   plopm -v xco2l -i 'r1_Cart_10m/flow/R1_CART_10M r2_cp_10mish/flow/R2_CP_10MISH r3_cp_10mish_convective/flow/R3_CP_10MISH_CONVECTIVE r4_Cart_1m/flow/R4_CART_1M' -dpi 300 -c cet_diverging_protanopic_deuteranopic_bwy_60_95_c32 -cbn 3 -xnt 8 -cbl 'SPE11B: CO$_2$ mass fraction (liquid phase) after 500 years' -fs 16,3 -t 'r1 Cart 10m  r2 cp 10mish  r3 cp 10mish convective  r4 Cart 1m' -yu km -xu km -yf .1f -xf .1f -r 98 -fn massfractb -cbf .2e -mv satnum -mt 5e-3 -st 0 -sg 2,2 -cbp 0.35,0.97,0.3,0.02 -rdl 1

.. figure:: ../figs/massfractb.png
   :alt: SPE11B simulation-grid spatial maps
   :align: center

SPE11C
------

Run from ``benchmark/spe11c``:

.. code-block:: console

   plopm -v xco2l -i 'r1_Cart_50m-50m-10m/flow/R1_CART_50M-50M-10M r2_cp_50m-50m-8mish/flow/R2_CP_50M-50M-8MISH r3_cp_50m-50m-8mish_convective/flow/R3_CP_50M-50M-8MISH_CONVECTIVE r4_cp_8m-8mish-8mish/flow/R4_CP_8M-8MISH-8MISH' -dpi 300 -c cet_diverging_protanopic_deuteranopic_bwy_60_95_c32 -cbn 3 -xnt 8 -cbl 'SPE11C: CO$_2$ mass fraction (liquid phase) after 1000 years (y=2.5 km)' -fs 16,3 -t 'r1 Cart [50m,50m,10m]  r2 cp [50m,50m,8mish]  r3 cp [50m,50m,8mish] convective  r4 cp [8m,8mish,8mish]' -yu km -xu km -yf .1f -xf .1f -r 27 -fn massfractc -cbf .2e -mv satnum -mt 1e-4 -st 0 -sg 2,2 -cbp 0.30,0.97,0.4,0.02 -rdl 1 -s ',51, ,51, ,51, ,304,'

.. figure:: ../figs/massfractc.png
   :alt: SPE11C simulation-grid spatial maps
   :align: center

See the `plopm documentation <https://cssr-tools.github.io/plopm/>`_ for the
complete option reference and additional visualization examples.

.. button-ref:: benchmark
   :ref-type: ref
   :color: primary
   :outline:

   Back to the benchmark gallery
