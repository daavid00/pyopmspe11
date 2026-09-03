# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT
# pylint: disable=C0103, R0902

"""Configuration and runtime settings shared across pyopmspe11 workflows.

Config combines command-line selections, validated TOML input, case-dependent
SPE11 properties, and values derived while creating decks and processing OPM
Flow results. The object is mutable because grid dimensions, feature locations,
and output paths are populated progressively.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Config:
    """Options, TOML input, and runtime settings for a pyopmspe11 operation.

    TOML-backed attributes retain the spelling used by existing configuration files.
    Derived attributes are populated while the input is initialized, grids are built,
    and output workflows are executed.

    Attributes
    ----------
    fol
        Base output directory for the current run.
    generate
        Benchmark data products requested from the data and plotting workflows.
    mode
        Workflow stages to execute, such as deck generation, Flow, data, or plotting.
    resolution
        Reporting-grid resolution supplied as x, y, and z element counts.
    time_data
        Requested dense-output times in hours for SPE11A or years for SPE11B/C.
    dt_data
        Sampling interval for sparse and performance data.
    lower
        Whether only the lower benchmark neighbourhood is modeled.
    subfolders
        Whether deck, flow, data, and figure files use separate subdirectories.
    flow
        OPM Flow command and command-line options.
    spe11
        Benchmark case identifier: ``spe11a``, ``spe11b``, or ``spe11c``.
    version
        OPM input-template version, such as release or master.
    model
        Physical model selection, including immiscible, isothermal, convective, or complete.
    grid
        Grid representation: Cartesian, tensor, or corner-point.
    dims
        Physical model dimensions along the x, y, and z axes.
    x_n, y_n, z_n
        Refinement counts used to construct the grid along each axis.
    temperature
        Reference and boundary temperatures used by the generated deck.
    datum
        Datum depth used for pressure initialization.
    pressure
        Pressure specified at the datum depth.
    kzMult
        Vertical permeability multiplier from the TOML configuration.
    diffusion
        Molecular diffusion coefficients for the fluid components.
    dispersion
        Facies-dependent dispersion coefficients.
    radius
        Well radii for the two injection wells.
    wellCoord
        Initial coordinates of the two injection wells.
    krw, krn, pcap, s_w
        Expressions for saturation tables (rel perms and cap pressure).
    safu
        Facies-dependent saturation-function parameters.
    rock
        Facies-dependent permeability and porosity values.
    inj
        Injection periods, rates, controls, and optional TUNING values.
    spe11aBC
        SPE11A boundary-condition selector from the TOML configuration.
    drsdtcon
        Optional convective-dissolution parameters for each facies.
    elevation, backElevation
        SPE11C elevation parameters used to curve and tilt the model.
    rockCond
        Facies-dependent rock thermal conductivities.
    widthBuffer
        Width of boundary-buffer cells for SPE11B and SPE11C.
    rockExtra
        Additional rock heat-capacity and density properties.
    pvAdded
        Extra boundary pore-volume width used in open-boundary cells.
    wellCoordF
        Final SPE11C well coordinates at the opposite side of the model.
    maxelevation
        Vertical SPE11C reference offset used during coordinate conversion.
    cut
        Height removed when modeling only the lower neighbourhood.
    nxyz
        Number of grid cells along the x, y, and z axes.
    boxa, boxb, boxc
        Opposite corners defining the benchmark reporting boxes.
    sensors
        Physical coordinates of the benchmark pressure sensors.
    sensorijk
        Zero-based grid indices of the pressure sensors.
    wellijk, wellijkf
        One-based initial and final grid indices of the injection wells.
    wellkh
        SPE11C well-layer indices along the sloping well trajectory.
    pat
        Package root containing templates and reference geometry.
    tuning
        Whether injection records include OPM TUNING values.
    deckfol
        Directory in which generated deck and include files are written.
    compact_dx
        Whether a compact nonuniform DX keyword is generated for a Cartesian grid.
    """

    # ------------------------------------------------------------------
    # CLI configuration (normalized)
    # ------------------------------------------------------------------
    fol: str
    generate: str
    mode: str
    resolution: str
    time_data: str
    dt_data: float
    lower: bool
    subfolders: str
    # ------------------------------------------------------------------
    # TOML configuration (simulation setup)
    # ------------------------------------------------------------------
    flow: str
    spe11: str
    version: str
    model: str
    grid: str
    dims: list[float]
    x_n: list[int]
    y_n: list[int]
    z_n: list[int]
    temperature: list[float]
    datum: float
    pressure: float
    kzMult: float
    diffusion: list[float]
    dispersion: list[float]
    radius: list[float]
    wellCoord: list[list[float]]
    krw: str
    krn: str
    pcap: str
    s_w: str
    safu: list[list[float]]
    rock: list[list[float]]
    inj: list[list[float]]
    # ------------------------------------------------------------------
    # TOML configuration optional (e.g., bc spe11a, convective mixing)
    # ------------------------------------------------------------------
    spe11aBC: float | None = 0
    drsdtcon: list[list[float | str]] | None = None
    elevation: float | None = None
    backElevation: float | None = None
    rockCond: list[float] | None = None
    widthBuffer: float | None = None
    rockExtra: list[float] | None = None
    pvAdded: float | None = None
    wellCoordF: list[list[float]] | None = None
    # ------------------------------------------------------------------
    # SPE11 geometry and observation setup
    # ------------------------------------------------------------------
    maxelevation: float = 0
    cut: float | None = 0
    nxyz: list[int] = field(default_factory=lambda: [0, 0, 0])
    boxa: list[list[float]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    boxb: list[list[float]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    boxc: list[list[float]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    sensors: list[list[float]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    sensorijk: list[list[int]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    wellijk: list[list[int]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    wellijkf: list[list[int]] = field(default_factory=lambda: [[0, 0, 0], [0, 0, 0]])
    wellkh: list[int] | None = field(default_factory=list)
    # ------------------------------------------------------------------
    # Miscellaneous runtime flags and metadata
    # ------------------------------------------------------------------
    pat: Path = Path(__file__).resolve().parents[1]  # Do not overwritte
    tuning: bool = False
    deckfol: str = "output"
    compact_dx: bool = False
