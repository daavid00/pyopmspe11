.. _example-lower-domain:

Localized lower domain
======================

Use :option:`pyopmspe11 -n` with ``lower`` to generate the lower region of an
SPE11 model, excluding the sealing facies.

.. code-block:: console

   pyopmspe11 -i spe11c.toml -o lower_domain -f 0 -n lower

Visualize the generated SPE11C model with plopm:

.. code-block:: console

   plopm -i lower_domain/LOWER_DOMAIN -s ,14, -y '[1200,700]' -asp 0 -ge 'black,1e-2' -t 'SPE11C Cartesian lower domain (y = 2500 m)' -cbl 'Facies' -c '161;163;160 101;64;147 81;124;66 181;73;57 193;127;97 127;148;191 193;147;56' -cbt '[7, 6, 5, 4, 3, 2, 1]' -v 'pvtnum - 1 - satnum'

.. image:: ../figs/lower_domain_pvtnum-1-satnum_i,14,k_t5.png
   :alt: Localized lower SPE11C domain

See :doc:`../convergence` for the localized SPE11B convergence cases.

Reproduce this example
----------------------

.. code-block:: console

   . ./tests/scripts/docs_localized_lower_domain.sh

.. button-link:: https://github.com/OPM/pyopmspe11/blob/main/tests/scripts/docs_localized_lower_domain.sh
   :color: primary
   :outline:

   View script
