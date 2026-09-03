.. _benchmark:

Benchmark
=========

The benchmark configurations reproduce the OPM team results for SPE11A,
SPE11B, and SPE11C. They cover Cartesian and corner-point grids, several
physical models, and spatial resolutions ranging from laboratory scale to a
three-dimensional model with more than 100 million cells.

.. note::

   OPM Flow is required to run these cases. See
   :ref:`opm-flow-installation`.

.. warning::

   Fine-grid benchmark cases require substantial memory, processing time, and
   parallel computing resources. Start with a coarser configuration unless
   suitable hardware is available.

.. grid:: 1 1 3 3
   :gutter: 3

   .. grid-item-card:: SPE11A
      :link: benchmark-spe11a
      :link-type: ref
      :img-top: figs/massfracta.png

      Laboratory-scale Cartesian and corner-point cases with grid sizes from
      1 cm to 1 mm.

   .. grid-item-card:: SPE11B
      :link: benchmark-spe11b
      :link-type: ref
      :img-top: figs/massfractb.png

      Two-dimensional field-scale cases, including convective dissolution and
      a fine 1 m grid.

   .. grid-item-card:: SPE11C
      :link: benchmark-spe11c
      :link-type: ref
      :img-top: figs/massfractc.png

      Three-dimensional field-scale cases, including a corner-point model with
      more than 100 million cells.

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item::

      .. button-link:: https://github.com/OPM/pyopmspe11/tree/main/benchmark
         :color: primary
         :outline:
         :expand:

         View benchmark configurations

   .. grid-item::

      .. button-link:: https://www.sciencedirect.com/science/article/pii/S1750583625002178
         :color: secondary
         :outline:
         :expand:

         Read the benchmark paper

.. toctree::
   :hidden:
   :maxdepth: 1

   benchmark/spe11a
   benchmark/spe11b
   benchmark/spe11c
   benchmark/plopm-visualization
