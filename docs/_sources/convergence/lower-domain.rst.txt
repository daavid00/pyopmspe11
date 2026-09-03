.. _convergence-lower-domain:

Lower domain
============

The localized lower-domain study uses nominal grid sizes of 320, 160, 80, 40,
20, 10, and 5 m.

This model isolates the lower part of SPE11B and removes the sealing facies. It
supports additional grid refinements at lower computational cost than the
complete-domain model.

Results
-------

.. figure:: ../figs/lower_spatial_map_all.png
   :alt: Spatial results for all lower-domain refinements
   :align: center

   Spatial maps for the localized lower-domain grid refinements.

Visualization settings
----------------------

The generated figure uses the Colorcet ``cet_CET_L19`` colormap. This differs
from the ``cet_CET_CBTL1_r`` colormap used in the paper.

The setting is defined in ``convergence.py`` and can be changed by modifying
the corresponding plopm ``-c`` option.

Generate a localized domain
---------------------------

The localized domain can also be selected directly with
:option:`pyopmspe11 -n`:

.. code-block:: console

   pyopmspe11 -i configuration.toml -o lower_domain -n lower

See :doc:`../examples/lower-domain` for an introductory localized-domain
workflow.

Continue
--------

* See :doc:`full-domain` for the complete-domain convergence study.
* Use :doc:`../configuration_file` for configuration-variable definitions.
* See :doc:`../benchmark/spe11b` for the SPE11B benchmark configurations.

.. button-ref:: convergence
   :ref-type: ref
   :color: primary
   :outline:

   Back to the convergence overview
