.. _convergence:

Convergence
===========

This section reproduces the numerical experiments presented in:

   Landa-Marbán, D., Lie, K.-A., Lye, K. O., Møyner, O., Rasmussen, A. F.,
   and Sandve, T. H. (2026). *Exploring Convergence and Its Limits in Case B
   of the 11th SPE Comparative Solution Project*. SPE Journal.
   https://doi.org/10.2118/231853-PA.

The study evaluates grid refinement for the complete SPE11B domain and a
localized lower-domain model.

Run the complete workflow
-------------------------

Run the convergence script from the repository:

.. code-block:: console

   cd convergence
   python3 convergence.py

The script generates the configurations, runs the selected simulations,
downloads participant data, and creates comparison figures.

.. note::

   OPM Flow is required to run the simulations. See
   :ref:`opm-flow-installation`.

The default configurations use eight processes. Modify the Flow command in
`spe11b.mako
<https://github.com/OPM/pyopmspe11/blob/main/convergence/spe11b.mako>`_
to change the process count or other simulator options.

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: Full domain
      :link: convergence-full-domain
      :link-type: ref
      :img-top: figs/full_spatial_map_adding_participants.png

      Compare 40, 20, 10, and 5 m grids with selected SPE11 benchmark
      participants.

   .. grid-item-card:: Lower domain
      :link: convergence-lower-domain
      :link-type: ref
      :img-top: figs/lower_spatial_map_all.png

      Study grid sizes from 320 m to 5 m in the localized lower domain.

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item::

      .. button-link:: https://github.com/OPM/pyopmspe11/blob/main/convergence/convergence.py
         :color: primary
         :outline:
         :expand:

         View convergence script

   .. grid-item::

      .. button-link:: https://github.com/OPM/pyopmspe11/blob/main/convergence/spe11b.mako
         :color: secondary
         :outline:
         :expand:

         View configuration template

.. toctree::
   :hidden:
   :maxdepth: 1

   convergence/full-domain
   convergence/lower-domain
