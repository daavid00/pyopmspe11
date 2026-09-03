.. _configuration-complete-example:

Complete TOML example
=====================

The following configuration defines a complete SPE11C corner-point model.
Comments identify units, array positions, and case-specific settings. See the
focused configuration pages for complete descriptions and validation rules.

.. code-block:: toml
   :linenos:

   # OPM Flow executable and options
   flow = "flow --relaxed-max-pv-fraction=0 --enable-tuning=true --enable-opm-rst-file=true --output-extra-convergence-info=steps,iterations"

   # Model
   spe11 = "spe11c" # SPE case: spe11a, spe11b, or spe11c
   version = "release" # OPM Flow compatibility: release or master
   model = "complete" # Physical model: immiscible, isothermal, convective, or complete
   grid = "corner-point" # Grid type: cartesian, tensor, or corner-point

   # Geometry and refinement
   dims = [8400.0, 5000.0, 1200.0] # Length, width, and depth [m]
   x_n = [420] # X-direction refinement
   y_n = [30, 40, 50, 40, 30] # Y-direction refinement for the five SPE11C regions
   z_n = [5, 3, 1, 2, 3, 2, 4, 4, 10, 4, 6, 6, 4, 8, 4, 15, 30, 9] # Refinement for the 11 or 18 geological levels
   elevation = 150 # Maximum y-direction arch elevation [m]
   backElevation = 10 # Back-boundary elevation relative to the front boundary [m]

   # Initial and boundary conditions
   temperature = [70.0, 36.12] # Bottom and top-rig temperatures [degrees Celsius]
   datum = 300 # Pressure datum depth [m]
   pressure = 3e7 # Pressure at the datum [Pa]
   diffusion = [1e-9, 2e-8] # Liquid- and gas-phase molecular diffusion [m2/s]
   pvAdded = 5e4 # Extra lateral-boundary pore volume per unit area [m]
   widthBuffer = 1 # Lateral buffer-cell width [m]

   # Rock and transport properties
   kzMult = 0.1 # Vertical-permeability multiplier [-]
   rockExtra = [0.85, 2500.0] # Rock heat capacity [kJ/(kg K)] and density [kg/m3]
   dispersion = [10, 10, 10, 10, 10, 10, 0] # Dispersivity [m], facies 1 to 7
   rockCond = [1.9, 1.25, 1.25, 1.25, 0.92, 0.26, 2.0] # Thermal conductivity [W/(m K)], facies 1 to 7

   # Wells
   radius = [0.15, 0.15] # Radius [m], wells 1 and 2; use 0 to generate SOURCE keywords
   wellCoord = [[2700.0, 1000.0, 300.0], [5100.0, 1000.0, 700.0]] # Initial [x, y, z] coordinates [m], wells 1 and 2
   wellCoordF = [[2700.0, 4000.0, 300.0], [5100.0, 4000.0, 700.0]] # Final [x, y, z] coordinates [m], wells 1 and 2

   # Saturation functions
   krw = "(max(0, (s_w - swi) / (1 - swi))) ** 1.5" # Wetting relative-permeability function [-]
   krn = "(max(0, (1 - s_w - sni) / (1 - sni))) ** 1.5" # Non-wetting relative-permeability function [-]
   pcap = "penmax * math.erf(pen * ((s_w-swi) / (1.-swi)) ** (-(1.0 / 1.5)) * math.pi**0.5 / (penmax * 2))" # Capillary-pressure function [Pa]
   s_w = "(np.exp(np.flip(np.linspace(0, 5.0, npoints))) - 1) / (np.exp(5.0) - 1)" # Wetting-saturation points [-]

   # Saturation properties per facies
   # Columns: 1) swi [-], 2) sni [-], 3) pen [Pa], 4) penmax [Pa], 5) npoints [-]
   safu = [
       [0.32, 0.1, 193531.39, 3e7, 1000], # Facies 1
       [0.14, 0.1,   8654.99, 3e7, 1000], # Facies 2
       [0.12, 0.1,   6120.00, 3e7, 1000], # Facies 3
       [0.12, 0.1,   3870.63, 3e7, 1000], # Facies 4
       [0.12, 0.1,   3060.00, 3e7, 1000], # Facies 5
       [0.10, 0.1,   2560.18, 3e7, 1000], # Facies 6
       [0,      0,         0, 3e7,    2], # Facies 7
   ]

   # Rock properties per facies
   # Columns: 1) permeability [mD], 2) porosity [-]
   rock = [
       [0.10132, 0.10], # Facies 1
       [101.324, 0.20], # Facies 2
       [202.650, 0.20], # Facies 3
       [506.625, 0.20], # Facies 4
       [1013.25, 0.25], # Facies 5
       [2026.50, 0.35], # Facies 6
       [1e-5,    1e-6], # Facies 7
   ]

   # Injection schedule
   # Time units: hours for SPE11A; years for SPE11B and SPE11C
   # Columns: 1) duration, 2) result interval,
   #          3) fluid well 1 (0 water, 1 CO2), 4) rate well 1 [kg/s],
   #          5) temperature well 1 [degrees Celsius],
   #          6) fluid well 2 (0 water, 1 CO2), 7) rate well 2 [kg/s],
   #          8) temperature well 2 [degrees Celsius],
   #          9) optional OPM TUNING values [days]
   inj = [
       [999.9, 999.9, 1,  0, 10, 1,  0, 10], # Initial period without injection
       [  0.1,   0.1, 1,  0, 10, 1,  0, 10], # Short initialization period
       [   25,     5, 1, 50, 10, 1,  0, 10], # Inject CO2 through well 1
       [   25,     5, 1, 50, 10, 1, 50, 10], # Inject CO2 through wells 1 and 2
       [   50,    25, 1,  0, 10, 1,  0, 10], # Post-injection period
       [  400,    50, 1,  0, 10, 1,  0, 10], # Long-term migration period
       [  500,   100, 1,  0, 10, 1,  0, 10], # Final monitoring period
   ]

The column comments are intentionally included so the array and matrix layouts
remain understandable when this example is copied and modified. See
:doc:`rock-fluid` for ``safu`` and ``rock``, and :doc:`wells-schedule` for
``inj`` and optional TUNING values.

Additional configurations are available in the repository `examples
<https://github.com/OPM/pyopmspe11/tree/main/examples>`_, `benchmark
<https://github.com/OPM/pyopmspe11/tree/main/benchmark>`_, and `test
configurations <https://github.com/OPM/pyopmspe11/tree/main/tests/configs>`_.
