.. _configuration-legacy-txt:

Legacy TXT format
=================

.. warning::

   The TXT format remains supported for existing configurations. Use TOML for
   new cases because new configuration features are added only to TOML.

The TXT reader expects ordered sections and uses blank lines to separate them.
Do not remove the line breaks between sections.

Flow command
------------

The first entry defines the Flow executable and its command-line options. Use
the full executable path when ``flow`` is not available on ``PATH``. MPI can be
included in the same line.

.. code-block:: text

   """Set the full path to the flow executable and flags"""
   flow --relaxed-max-pv-fraction=0 --enable-tuning=true --enable-opm-rst-file=true --output-extra-convergence-info=steps,iterations

For an MPI build, prepend the launcher and number of processes, for example
``mpirun -np 8 flow ...``.

Reservoir parameters
--------------------

The model section defines the benchmark case, OPM Flow version, physical model,
grid, dimensions, refinement, initial conditions, boundary settings, and
case-specific geometry. Keep the comments when creating or modifying a legacy
configuration because they identify the meaning and units of every entry.

.. code-block:: text

   """Set the model parameters"""
   spe11c master     # Name of the SPE case (spe11a, spe11b, or spe11c) and OPM Flow version (master or release)
   complete          # CO2 model (immiscible, isothermal, convective, or complete)
   corner-point      # Grid type (cartesian, tensor, or corner-point)
   8400 5000 1200    # Length, width, and depth [m]
   420               # For Cartesian grids, number of x cells; otherwise, variable x-refinement array [-]
   30,40,50,40,30    # For Cartesian grids, number of y cells; otherwise, variable y-refinement array [-] (SPE11C)
   5,3,1,2,3,2,4,4,10,4,6,6,4,8,4,15,30,9 # For Cartesian grids, number of z cells; for tensor grids, variable z-refinement; for corner-point grids, fixed 11- or 18-entry z-refinement array [-]
   70 36.12          # Bottom and top-rig temperatures [degrees Celsius]
   300 3e7 0.1       # Datum [m], pressure at the datum [Pa], and vertical-permeability multiplier [-]
   1e-9 2e-8         # Molecular diffusion in the liquid and gas phases [m2/s]
   8.5e-1 2500       # Rock specific heat capacity [kJ/(kg K)] and density [kg/m3] (SPE11B and SPE11C)
   0 5e4 1           # Added top-boundary pore volume for SPE11A (0 selects free flow), lateral-boundary pore volume, and buffer-cell width [m] for SPE11B and SPE11C
   150 10            # Maximum y-direction arch elevation and back-boundary elevation relative to the front boundary [m] (SPE11C)

See :doc:`model`, :doc:`grid`, and :doc:`initial-conditions` for the complete
variable descriptions and validation rules.

Rock and saturation properties
------------------------------

The saturation-function section defines the wetting and non-wetting relative
permeabilities, capillary pressure, points used to tabulate the functions, and
the facies-dependent saturation properties.

.. code-block:: text

   """Set the saturation functions"""
   (max(0, (s_w - swi) / (1 - swi))) ** 1.5                                                        # Wetting relative-permeability function [-]
   (max(0, (1 - s_w - sni) / (1 - sni))) ** 1.5                                                    # Non-wetting relative-permeability function [-]
   penmax * math.erf(pen * ((s_w-swi) / (1.-swi)) ** (-(1.0 / 1.5)) * math.pi**0.5 / (penmax * 2)) # Capillary-pressure function [Pa]
   (np.exp(np.flip(np.linspace(0, 5.0, npoints))) - 1) / (np.exp(5.0) - 1)                         # Wetting-saturation points used to evaluate the functions [-]

   """Properties sat functions"""
   """swi [-], sni [-], pen [Pa], penmax [Pa], npoints [-]"""
   SWI1 0.32 SNI1 0.1 PEN1 193531.39 PENMAX1 3e7 NPOINTS1 1000  # Facies 1
   SWI2 0.14 SNI2 0.1 PEN2   8654.99 PENMAX2 3e7 NPOINTS2 1000  # Facies 2
   SWI3 0.12 SNI3 0.1 PEN3   6120.00 PENMAX3 3e7 NPOINTS3 1000  # Facies 3
   SWI4 0.12 SNI4 0.1 PEN4   3870.63 PENMAX4 3e7 NPOINTS4 1000  # Facies 4
   SWI5 0.12 SNI5 0.1 PEN5   3060.00 PENMAX5 3e7 NPOINTS5 1000  # Facies 5
   SWI6 0.10 SNI6 0.1 PEN6   2560.18 PENMAX6 3e7 NPOINTS6 1000  # Facies 6
   SWI7    0 SNI7   0 PEN7         0 PENMAX7 3e7 NPOINTS7    2  # Facies 7

The rock-property section defines permeability, porosity, dispersivity, and
thermal conductivity for every facies.

.. code-block:: text

   """Properties rock"""
   """K [mD], phi [-], disp [m], thconr [W m-1 K-1]"""
   PERM1 0.10132 PORO1 0.10 DISP1 10 THCONR1 1.90  # Facies 1
   PERM2 101.324 PORO2 0.20 DISP2 10 THCONR2 1.25  # Facies 2
   PERM3 202.650 PORO3 0.20 DISP3 10 THCONR3 1.25  # Facies 3
   PERM4 506.625 PORO4 0.20 DISP4 10 THCONR4 1.25  # Facies 4
   PERM5 1013.25 PORO5 0.25 DISP5 10 THCONR5 0.92  # Facies 5
   PERM6 2026.50 PORO6 0.35 DISP6 10 THCONR6 0.26  # Facies 6
   PERM7    1e-5 PORO7 1e-6 DISP7  0 THCONR7 2.00  # Facies 7

See :doc:`rock-fluid` for the TOML equivalents, units, matrix layouts, and
validation rules.

Wells and schedule
------------------

The final sections define the radius and coordinates of each well, followed by
the injection schedule. An optional quoted value at the end of a schedule row
sets OPM ``TUNING`` values.

.. code-block:: text

   """Wells radius and position"""
   """radius (0 selects SOURCE), initial x, y, z, and final x, y, z [m] (final coordinates apply to SPE11C)"""
   0.15 2700. 1000. 300. 2700. 4000. 300. # Well 1
   0.15 5100. 1000. 700. 5100. 4000. 700. # Well 2

   """Define the injection values ([hours] for SPE11A; [years] for SPE11B and SPE11C)"""
   """1) duration, 2) result interval, 3) fluid well 1, 4) rate well 1 [kg/s], 5) temperature well 1 [degrees Celsius], 6) fluid well 2, 7) rate well 2 [kg/s], 8) temperature well 2 [degrees Celsius], and optional TUNING values [days]"""
   999.9 999.9 1  0 10 1  0 10 # Initial period without injection
     0.1   0.1 1  0 10 1  0 10 # Short initialization period
      25     5 1 50 10 1  0 10 # Inject CO2 through well 1
      25     5 1 50 10 1 50 10 # Inject CO2 through wells 1 and 2
      50    25 1  0 10 1  0 10 # Post-injection period
     400    50 1  0 10 1  0 10 # Long-term migration period
     500   100 1  0 10 1  0 10 # Final monitoring period

Here, fluid ``0`` means water and fluid ``1`` means CO2. See
:doc:`wells-schedule` for detailed column definitions and TUNING guidance.

.. note::

   When ``--enable-tuning=true`` is included in the Flow command, append the
   corresponding TUNING values to an injection row. For example, to set a
   maximum time step of 10 days at the beginning of injection:

   .. code-block:: text

      25 5 1 50 10 1 0 10 '1* 10' # First TUNING value defaulted; second value sets TSMAXZ

   TUNING time quantities are expressed in days for all three SPE cases. See
   the `OPM Flow manual <https://opm-project.org/?page_id=955>`_ for all 34
   options and their default values.

.. warning::

   Preserve the blank line between legacy TXT sections. The current parser uses
   these line breaks to separate and read the parameter groups.

Modify generated decks
----------------------

A legacy configuration can still generate only the deck:

.. code-block:: console

   pyopmspe11 -i input.txt -o output -m deck

After generation, modify the OPM input files and run the simulation with
``-m flow`` when appropriate. See the `OPM Flow manual
<https://opm-project.org/?page_id=955>`_ for keyword definitions.
