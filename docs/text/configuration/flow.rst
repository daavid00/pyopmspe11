.. _configuration-flow:

OPM Flow settings
=================

The ``flow`` variable defines the simulator command and its command-line
options.

.. _config-flow:

flow
----

**Type:** non-empty string

The value may include the executable name or full path, an MPI launcher, the
number of processes, and any OPM Flow options.

Executable on ``PATH``:

.. code-block:: toml

   flow = "flow --enable-opm-rst-file=true"

Full executable path:

.. code-block:: toml

   flow = "/path/to/flow --enable-opm-rst-file=true"

MPI execution:

.. code-block:: toml

   flow = "mpirun -np 32 flow --partition-method=metis --enable-opm-rst-file=true"

Use :ref:`config-version` to select compatibility with the stable release or
master branch. **pyopmspe11** checks that the configured OPM Flow release is
supported before running the simulation.

.. note::

   OPM Flow is not required for ``pyopmspe11 -m deck``. It is required for
   simulation, data-processing, and plotting workflows.

See :ref:`opm-flow-installation` and the `OPM Flow manual
<https://opm-project.org/?page_id=955>`_.
