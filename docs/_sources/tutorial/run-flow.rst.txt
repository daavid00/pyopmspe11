.. _tutorial-run-flow:

Run OPM Flow
============

Set the OPM Flow command in the TOML file, then generate and run the simulation.

Configure Flow
--------------

Open ``my_spe11b.toml`` and check these variables:

.. code-block:: toml

   flow = "flow --enable-opm-rst-file=true"
   version = "release"

If Flow is not available on ``PATH``, use its full path. For an MPI build, the
command can also include the launcher and process count:

.. code-block:: toml

   flow = "mpirun -np 8 /path/to/flow --enable-opm-rst-file=true"

Run the simulation
------------------

.. code-block:: console

   pyopmspe11 -i my_spe11b.toml -o my_spe11b -m flow

How it works
------------

``flow``
   Sets the executable, optional MPI launcher, and OPM Flow arguments.

``version``
   Selects compatibility with the supported stable release or the current
   master branch.

``-m flow``
   Runs OPM Flow.

Result
------

With subfolders enabled, simulation output is written under:

.. code-block:: text

   my_spe11b/
   └── deck
   └── flow/
       ├── MY_SPE11B.DBG
       ├── MY_SPE11B.EGRID
       ├── MY_SPE11B.ESMRY
       ├── MY_SPE11B.INFOITER
       ├── MY_SPE11B.INFOSTEP
       ├── MY_SPE11B.INIT
       ├── MY_SPE11B.PRT
       ├── MY_SPE11B.SMSPEC
       ├── MY_SPE11B.UNRST
       ├── MY_SPE11B.UNSMRY


Use `ResInsight <https://resinsight.org/>`_ or
`plopm <https://github.com/cssr-tools/plopm>`_ to inspect the output.

Next
----

Continue with :doc:`benchmark-data`. See :ref:`opm-flow-installation` for Flow
installation and :doc:`../output_folder` for generated files.
