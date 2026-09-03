pyopmspe11
===========

.. rst-class:: lead

   A Python framework using OPM Flow for the SPE11 benchmark project.

**pyopmspe11** generates simulation decks, runs OPM Flow, writes benchmark
CSV files, and creates figures for SPE11A, SPE11B, and SPE11C.

.. grid:: 1 2 2 4
   :gutter: 3
   :margin: 4 0 4 0

   .. grid-item-card:: :octicon:`rocket;1.2em` Get started
      :link: introduction
      :link-type: doc

      Learn the main workflows and choose where to begin.

   .. grid-item-card:: :octicon:`download;1.2em` Install
      :link: installation
      :link-type: doc

      Install the Python package, OPM Flow, and visualization tools.

   .. grid-item-card:: :octicon:`gear;1.2em` Configure a case
      :link: configuration_file
      :link-type: doc

      Define the model, grid, properties, wells, and injection schedule.

   .. grid-item-card:: :octicon:`book;1.2em` Follow the tutorial
      :link: tutorial
      :link-type: doc

      Progress from deck generation to benchmark data, plots, and comparisons.

Quick installation
------------------

Install the current development version:

.. code-block:: console

   pip install git+https://github.com/OPM/pyopmspe11.git

See :doc:`installation` for virtual environments, OPM Flow, ResInsight,
plopm, optional LaTeX support, and installation from source.

Quick start
-----------

Generate an SPE11B deck, run OPM Flow, and write benchmark data:

.. code-block:: console

   pyopmspe11 -i examples/spe11b.toml -m deck_flow_data

Generate only the OPM Flow input files directly inside the ``spe11b`` folder:

.. code-block:: console

   pyopmspe11 -i examples/spe11b.toml -m deck -o spe11b -f 0

Display the available command-line options:

.. code-block:: console

   pyopmspe11 --help

See :doc:`tutorial` for a guided workflow, :doc:`examples` for focused
applications, and :doc:`command-line` for exact syntax, accepted values,
defaults, and option compatibility.

What can pyopmspe11 do?
-----------------------

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: Generate simulation models

      Create Cartesian, tensor, and corner-point grids for SPE11A, SPE11B,
      and SPE11C.

   .. grid-item-card:: Run configurable workflows

      Generate decks, run OPM Flow, process benchmark data, and create plots
      independently or as one workflow.

   .. grid-item-card:: Write benchmark results

      Export dense, sparse, performance, and spatial-performance CSV data in
      the SPE11 reporting format.

   .. grid-item-card:: Compare simulations

      Create benchmark figures, compare model variants, and assess grid
      refinement and convergence.

.. toctree::
   :hidden:
   :maxdepth: 2

   introduction
   installation
   configuration_file
   tutorial
   examples
   benchmark
   command-line
   convergence
   api
   output_folder
   contributing
   related
