.. _installation:

Installation
============

The following instructions cover dependency installation on Linux with
``apt-get`` and on macOS with Homebrew or MacPorts. Package managers such as
Anaconda, Miniforge, and Mamba might work, but they are not tested.

**pyopmspe11** supports Python 3.12 to 3.14.

`ResInsight <https://resinsight.org/>`_ and
`plopm <https://github.com/cssr-tools/plopm>`_ can be used to visualize the
simulation results.

Visualization tools
-------------------

ResInsight
++++++++++

Binary ResInsight packages are available for Linux and Windows. See the
`ResInsight releases <https://resinsight.org/releases/>`_ for installation
instructions.

On macOS, install ResInsight with Homebrew:

.. code-block:: console

   brew tap cssr-tools/opm
   brew trust cssr-tools/opm
   brew install cssr-tools/opm/resinsight -y

Verify the installation:

.. code-block:: console

   resinsight

plopm
+++++

Install **plopm** to create additional maps, summary plots, GIF animations,
CSV exports, and VTK files:

.. code-block:: console

   pip install git+https://github.com/cssr-tools/plopm.git

.. _vpyopmspe11:

Python package
--------------

Install the development version of **pyopmspe11** in an existing Python
environment:

.. code-block:: console

   pip install git+https://github.com/OPM/pyopmspe11.git

To install a specific version, modify the source code, or contribute to the
project, clone the repository and create a virtual environment:

.. code-block:: console

   # Clone the repository
   git clone https://github.com/OPM/pyopmspe11.git

   # Enter the repository
   cd pyopmspe11

   # Optional: select a release, or skip this step to use the development version
   git checkout v2026.04

   # Create a virtual environment
   # To select a Python executable, use for example: python3.13 -m venv vpyopmspe11
   python3 -m venv vpyopmspe11

   # Activate the virtual environment
   source vpyopmspe11/bin/activate

   # Upgrade the packaging tools
   pip install --upgrade pip setuptools wheel

   # Install pyopmspe11 in editable mode
   pip install -e .

   # Optional: install requirements for contributions, testing, and linting
   pip install -r dev-requirements.txt

.. tip::

   Run ``git tag -l`` to list the available releases.

Optional LaTeX formatting
-------------------------

LaTeX support is optional but recommended for figure formatting.

On Linux distributions using ``apt-get``, install:

.. code-block:: console

   sudo apt-get install texlive-fonts-recommended texlive-fonts-extra dvipng cm-super

On macOS, install `MacTeX <https://www.tug.org/mactex/>`_.

.. _opm-flow-installation:

OPM Flow
--------

OPM Flow is required to run simulations and generate benchmark data from the
simulation results. Deck-only workflows, such as ``-m deck``, do not require
OPM Flow.

Use OPM Flow Release 2026.04 or the current master branches. See the
`OPM project website <https://opm-project.org/>`_ for general information.

Binary packages
+++++++++++++++

See the OPM Flow `download and installation instructions
<https://opm-project.org/?page_id=36>`_ for binary packages on Ubuntu and Red
Hat Enterprise Linux. The same page describes other supported platforms,
including source builds and virtual-machine-based installations.

.. tip::

   The pyopmspe11 `Ubuntu CI workflow
   <https://github.com/OPM/pyopmspe11/blob/main/.github/workflows/ci_pyopmspe11_ubuntu.yml>`_
   shows the installation of OPM Flow binary packages, optional LaTeX
   libraries, and **pyopmspe11**.

Source build on Linux
+++++++++++++++++++++

After installing the OPM `prerequisites
<https://opm-project.org/?page_id=239>`_, build Flow from the current master
branches. The following commands create the executable at
``./build/opm-simulators/bin/flow``:

.. code-block:: bash

   CURRENT_DIRECTORY="$PWD"

   mkdir build

   for repo in common grid simulators
   do
       git clone https://github.com/OPM/opm-$repo.git
       mkdir build/opm-$repo
       cd build/opm-$repo
       cmake -DWITH_NDEBUG=1 -DCMAKE_BUILD_TYPE=Release $CURRENT_DIRECTORY/opm-$repo
       if [[ $repo == simulators ]]; then
           make -j5 flow
       else
           make -j5 opm$repo
       fi
       cd ../..
   done

To build with MPI support, add ``-DUSE_MPI=1`` to the ``cmake`` command.

.. tip::

   Save the commands in a shell script, for example ``build_opm_mpi.sh``, and
   run it with:

   .. code-block:: console

      . ./build_opm_mpi.sh

Set the ``flow`` value in the TOML configuration to the resulting executable
and any required simulator options:

.. code-block:: toml

   flow = "/path/to/build/opm-simulators/bin/flow --enable-opm-rst-file=true --output-extra-convergence-info=steps,iterations"

See :doc:`configuration_file` for the complete configuration format.

.. _macOS:

Homebrew formula for macOS
++++++++++++++++++++++++++

Binary OPM Flow packages are not available for macOS, so Flow must be built
from source. The `cssr-tools/homebrew-opm
<https://github.com/cssr-tools/homebrew-opm>`_ repository provides a Homebrew
formula for this purpose.

Install the OPM Flow v2026.07 interim release with:

.. code-block:: console

   brew tap cssr-tools/opm
   brew trust cssr-tools/opm
   brew install cssr-tools/opm/opm-simulators -y

Verify the installation:

.. code-block:: console

   flow --help

.. tip::

   See the `homebrew-opm workflow results
   <https://github.com/cssr-tools/homebrew-opm/actions>`_ for tested builds.

Source build on macOS
+++++++++++++++++++++

See the `OPM-Flow_macOS repository
<https://github.com/daavid00/OPM-Flow_macOS>`_ for a source-build workflow for
OPM Flow on macOS 26. The workflow runs with GitHub Actions and is tested with
**pycopm**, another project in the ``cssr-tools`` organization.

Windows deck generation
-----------------------

On Windows, **pyopmspe11** supports deck generation with ``-m deck``. Running
OPM Flow and the data or plotting workflows requires a supported OPM Flow
environment. If another mode is selected on Windows, **pyopmspe11** continues
with deck generation only.

Verify the installation
-----------------------

Display the command-line help:

.. code-block:: console

   pyopmspe11 --help

Generate an input deck without running OPM Flow:

.. code-block:: console

   pyopmspe11 -i examples/spe11b.toml -o spe11b -m deck

Next steps
----------

* Review the :doc:`configuration_file` reference to define a simulation case.
* Run the :doc:`examples` for complete, reproducible workflows.
* Use the :doc:`command-line` for exact syntax, defaults, and option
  compatibility.
* See :doc:`output_folder` for the generated folder structure.
