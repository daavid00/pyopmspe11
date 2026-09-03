# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT
# pylint: disable=C0302,R0912,R0914,R0801,R0915,E1102,C0325,R0902,R0913,R0917,R0911

"""Generate SPE11 benchmark CSV data from OPM Flow results.

The module reads INIT, UNRST, EGRID, SMSPEC, and INFOSTEP data and supports four
outputs: performance time series, sparse benchmark quantities, dense spatial
maps, and spatial performance metrics. Simulation cells are mapped to the
regular benchmark reporting grid by aligned-grid or polygon-intersection methods.
"""

import argparse
import csv
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from io import StringIO
from itertools import pairwise

import numpy as np
from alive_progress import alive_bar
from numpy.typing import NDArray
from opm.io.ecl import EclFile as OpmFile
from opm.io.ecl import EGrid as OpmGrid
from opm.io.ecl import ERst as OpmRestart
from opm.io.ecl import ESmry as OpmSummary
from rtree import index
from scipy.interpolate import interp1d
from shapely.geometry import Polygon

from pyopmspe11.utils.terminal import (
    pyopmspe11_error,
    pyopmspe11_info,
    pyopmspe11_success,
)

GAS_DEN_REF = 1.86843
WAT_DEN_REF = 998.108
SECONDS_IN_YEAR = 31536000
SGAS_THR = 0.097


@dataclass(slots=True)
class DataConfig:
    """Paths and benchmark settings used to generate CSV output.

    Attributes
    ----------
    outfol
        Base directory containing the generated deck and Flow results.
    case
        SPE11 case identifier.
    mode
        Requested combination of dense, sparse, and performance outputs.
    lower
        Whether processing is restricted to the lower neighbourhood.
    deckfol, flowfol, where
        Directories containing the deck, Flow results, and generated CSV files.
    nxyz
        Reporting-grid cell counts along x, y, and z.
    dims
        Physical reporting-grid dimensions.
    denset
        Simulation times requested for dense output, in seconds.
    sparset
        Sparse and performance sampling interval, in seconds.
    nocellsrepgrid
        Total number of cells in the benchmark reporting grid.
    """

    outfol: str
    case: str
    mode: str
    lower: bool
    deckfol: str
    flowfol: str
    where: str
    nxyz: NDArray
    dims: list
    denset: NDArray
    sparset: float
    nocellsrepgrid: int


@dataclass(slots=True)
class SimulationData:
    """OPM readers and derived metadata for one simulation result set.

    Arrays in global order contain all grid cells. Active arrays follow the indexing
    used by INIT and UNRST properties.

    Attributes
    ----------
    simres
        Common path stem of the simulation result files.
    unrst, init, egrid, smspec
        OPM readers for restart, initialization, grid, and summary data.
    times
        Restart times measured from the detected injection start.
    timesumary
        Summary times measured from the same injection start.
    timeini
        Absolute simulation time at the detected injection start.
    noskiprst
        Restart index immediately before or at the injection start.
    norst
        Number of restart report steps.
    porv, porva
        Pore volume in global and active-cell order.
    actind
        Global indices of active cells.
    immiscible, isothermal
        Whether dissolved components or thermal variables are absent.
    cornpoint
        Whether the simulation uses the corner-point grid layout handled here.
    nocellst, nocellsa, nocellsxz
        Total, active, and x-z plane cell counts.
    dof
        Number of primary degrees of freedom per active cell.
    simdim
        Simulation-grid dimensions along x, y, and z.
    """

    simres: str
    unrst: OpmRestart
    init: OpmFile
    egrid: OpmGrid
    smspec: OpmSummary
    times: list
    timesumary: list
    timeini: float
    noskiprst: int
    norst: int
    porv: NDArray
    porva: NDArray
    actind: list
    immiscible: bool
    isothermal: bool
    cornpoint: bool
    nocellst: int
    nocellsa: int
    dof: int
    nocellsxz: int
    simdim: list


def generate_data(cmdargs: dict) -> list[str]:
    """Generate the requested SPE11 benchmark CSV files.

    The function initializes readers once and dispatches performance, sparse,
    dense, and performance-spatial processing according to the selected mode.

    Parameters
    ----------
    cmdargs : dict
        Parsed data-generation arguments.

    Returns
    -------
    list[str]
        Names of the generated benchmark CSV files.
    """
    generated_files: list[str] = []
    cfg = build_config_from_args(cmdargs)
    sim = read_simulations(cfg)

    if cfg.mode in (
        "performance",
        "all",
        "dense_performance",
        "performance_sparse",
        "dense_performance_sparse",
    ):
        generate_performance_data(cfg, sim)
        generated_files.append(f"{cfg.case}_performance_time_series.csv")
        generated_files.append(f"{cfg.case}_performance_time_series_detailed.csv")
    if cfg.mode in (
        "all",
        "sparse",
        "dense_sparse",
        "dense_performance_sparse",
        "performance_sparse",
    ):
        generate_sparse_data(cfg, sim)
        generated_files.append(f"{cfg.case}_time_series.csv")
    if cfg.mode in (
        "all",
        "performance-spatial",
        "dense",
        "dense_performance",
        "dense_sparse",
        "dense_performance-spatial",
        "dense_performance_sparse",
    ):
        if isinstance(cfg.denset, float):
            dt = cfg.denset
            cfg.denset = [i * dt for i in range(int(np.floor(sim.times[-1] / dt)) + 1)]
        generated_files.extend(generate_dense_data(cfg, sim))
    return generated_files


def build_config_from_args(cmdargs: dict) -> DataConfig:
    """Build data-generation settings from parsed arguments.

    Parameters
    ----------
    cmdargs : dict
        Parsed data-generation arguments.

    Returns
    -------
    DataConfig
        Initialized benchmark data settings.
    """
    outfol = cmdargs["path"].strip()
    case = cmdargs["deck"].strip()
    mode = cmdargs["generate"].strip()
    lower = bool(cmdargs["neighbourhood"].strip())
    if int(cmdargs["subfolders"]) == 1:
        deckfol = f"{outfol}/deck"
        flowfol = f"{outfol}/flow"
        where = f"{outfol}/data"
    else:
        deckfol = flowfol = where = outfol
    nxyz = np.genfromtxt(StringIO(cmdargs["resolution"]), delimiter=",", dtype=int)
    if case == "spe11a":
        denset = (
            np.genfromtxt(StringIO(cmdargs["time"]), delimiter=",", dtype=float) * 3600
        )
        sparset = float(round(float(cmdargs["write"].strip()) * 3600))
        dims = [2.8, 1.0, 1.2]
        nxyz[1] = 1
    else:
        denset = (
            np.genfromtxt(StringIO(cmdargs["time"]), delimiter=",", dtype=float)
            * SECONDS_IN_YEAR
        )
        sparset = float(cmdargs["write"].strip()) * SECONDS_IN_YEAR
        dims = [8400.0, 1.0, 1200.0]
    if case == "spe11c":
        dims[1] = 5000.0
    nocellsrepgrid = nxyz[0] * nxyz[1] * nxyz[2]
    return DataConfig(
        outfol=outfol,
        case=case,
        mode=mode,
        lower=lower,
        deckfol=deckfol,
        flowfol=flowfol,
        where=where,
        nxyz=nxyz,
        dims=dims,
        denset=denset,
        sparset=sparset,
        nocellsrepgrid=nocellsrepgrid,
    )


def read_simulations(cfg: DataConfig) -> SimulationData:
    """Open OPM result files and derive shared simulation metadata.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.

    Returns
    -------
    SimulationData
        Loaded OPM readers and derived simulation metadata.
    """
    simres = f"{cfg.flowfol}/{cfg.outfol.split('/')[-1].upper()}"
    unrst = OpmRestart(f"{simres}.UNRST")
    immiscible = unrst.count("RSW", 0) == 0
    isothermal = unrst.count("TEMP", 0) == 0
    dof = 2 if isothermal else 3
    absolute_times = []
    relative_times: list[float] = []
    initial_time = 0.0
    first_restart_index = 0

    for restart_index in range(len(unrst.report_steps)):
        absolute_time = 86400.0 * unrst["DOUBHEAD", restart_index][0]
        absolute_times.append(absolute_time)

        if relative_times:
            relative_times.append(absolute_time - initial_time)
            continue

        injection_detected = (
            np.max(unrst["RSW", restart_index]) > 0
            if not immiscible
            else np.max(unrst["SGAS", restart_index]) > 0
        )

        if not injection_detected:
            continue

        first_restart_index = max(0, restart_index - 1)
        initial_time = absolute_times[first_restart_index]

        if restart_index == 0:
            relative_times = [0.0]
        else:
            relative_times = [0.0, absolute_time - initial_time]

    if not relative_times:
        relative_times = absolute_times
    init = OpmFile(f"{simres}.INIT")
    egrid = OpmGrid(f"{simres}.EGRID")
    smspec = OpmSummary(f"{simres}.SMSPEC")
    norst = len(unrst.report_steps)
    porv = np.array(init["PORV"])
    actind = [i for i, p in enumerate(porv) if p > 0]
    porva = np.array([p for p in porv if p > 0])
    nocellst = len(porv)
    nocellsa = egrid.active_cells
    timesumary = [0.0] + list(86400.0 * smspec["TIME"] - initial_time)
    dims = egrid.dimension
    simdim = [dims[0], dims[1], dims[2]]
    nocellsxz = dims[0] * dims[2]
    cornpoint = porv[-1] == 0
    return SimulationData(
        simres=simres,
        unrst=unrst,
        immiscible=immiscible,
        isothermal=isothermal,
        dof=dof,
        times=relative_times,
        timeini=initial_time,
        noskiprst=first_restart_index,
        init=init,
        egrid=egrid,
        smspec=smspec,
        norst=norst,
        porv=porv,
        actind=actind,
        porva=porva,
        nocellst=nocellst,
        nocellsa=nocellsa,
        timesumary=timesumary,
        simdim=simdim,
        nocellsxz=nocellsxz,
        cornpoint=cornpoint,
    )


def generate_performance_data(cfg: DataConfig, sim: SimulationData) -> None:
    """Generate regular and detailed performance CSV data.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    """
    perf = build_performance_data(cfg, sim)
    write_performance_csv(cfg, perf)


def read_infostep_data(cfg: DataConfig, sim: SimulationData) -> tuple[list, NDArray]:
    """Read solver-step records from the INFOSTEP file.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    tags : list[str]
        Column names read from the INFOSTEP header.
    infosteps : NDArray
        Numeric INFOSTEP rows at or after the selected simulation start.
    """
    infosteps = []
    with open(
        f"{cfg.flowfol}/{cfg.outfol.split('/')[-1].upper()}.INFOSTEP",
        "r",
        encoding="utf8",
    ) as file:
        reader = csv.reader(file)
        tags = next(reader)[0].strip().split()
        for row in reader:
            values = row[0].strip().split()
            if float(values[0]) >= (sim.timeini - cfg.sparset) / 86400.0:
                infosteps.append([float(val) for val in values])
    return tags, np.array(infosteps)


def build_performance_data(cfg: DataConfig, sim: SimulationData) -> dict:
    """Build regular and detailed performance-series records.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    dict[str, list[str]]
        Regular and detailed performance CSV rows keyed by ``series`` and
        ``detailed``.
    """
    tags, infosteps = read_infostep_data(cfg, sim)
    infotimes = infosteps[:, tags.index("Time(day)")] * 86400.0 - sim.timeini
    times_data = np.linspace(0, sim.times[-1], round(sim.times[-1] / cfg.sparset) + 1)
    time_offset = max(0, sim.noskiprst - 1)
    map_info = np.array(
        [time_offset + int(np.floor(time_val / cfg.sparset)) for time_val in infotimes]
    )
    tmp = [0]
    for i in range(len(infotimes) - 1):
        if infotimes[i] != infotimes[i + 1]:
            tmp.append(tmp[-1] + 1)
        else:
            tmp.append(tmp[-1])
    detail_info = np.array(tmp)
    times_det = np.array(
        [np.max(infotimes[detail_info == i]) for i in range(np.max(detail_info) + 1)]
    )
    metrics = extract_solver_metrics(infosteps, tags)
    cpu_times, map_summary, summary_times = compute_cpu_times(cfg, sim, times_det)
    fgmip_values = sim.smspec["FGMIP"]
    if sim.timeini == 0:
        summary_times = np.insert(summary_times, 0, 0.0)
        fgmip_values = np.insert(fgmip_values, 0, 0.0)
    interp_fgmip = interp1d(summary_times, fgmip_values, fill_value="extrapolate")
    return {
        "series": build_time_series(
            sim, times_data, metrics, map_info, map_summary, interp_fgmip, cpu_times
        ),
        "detailed": build_detailed_series(
            sim, metrics, detail_info, infotimes, interp_fgmip, cpu_times
        ),
    }


def extract_solver_metrics(infosteps: NDArray, tags: list) -> dict:
    """Extract solver metrics from INFOSTEP columns.

    Parameters
    ----------
    infosteps : NDArray
        Numeric INFOSTEP records.
    tags : list
        INFOSTEP column names.

    Returns
    -------
    dict[str, NDArray]
        Convergence flags, iteration counts, time-step sizes, and solver times
        extracted from the INFOSTEP columns.
    """
    return {
        "fsteps": np.array(infosteps[:, tags.index("Conv")] == 0, dtype=float),
        "nres": infosteps[:, tags.index("Lins")],
        "tlsolve": infosteps[:, tags.index("LSolve")],
        "linit": infosteps[:, tags.index("LinIt")],
        "nlinit": infosteps[:, tags.index("NewtIt")],
        "tsteps": 86400.0
        * infosteps[:, tags.index("TStep(day)")]
        * infosteps[:, tags.index("Conv")],
    }


def compute_cpu_times(
    cfg: DataConfig, sim: SimulationData, times_det: NDArray
) -> tuple[list, NDArray, NDArray]:
    """Align CPU-time increments with performance output intervals.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    times_det : NDArray
        Detailed output times.

    Returns
    -------
    cpu_times : NDArray
        CPU-time increments for the detailed output intervals.
    map_summary : NDArray
        Sparse-output interval associated with each detailed interval.
    summary_times : NDArray
        Summary-vector times relative to the simulation start.
    """
    cpu = sim.smspec["TCPU"]
    summary_times = 86400.0 * sim.smspec["TIME"] - sim.timeini
    map_summary = np.array(
        [
            max(0, sim.noskiprst - 1) + int(np.floor(time_val / cfg.sparset))
            for time_val in times_det
        ]
    )
    # For some spe11a cases (e.g., benchmark/spe11a/r3_cp_1cmish_capmax2500Pa.toml), it
    # seems a bug in OPM Flow is triggered where these arrays have different sizes. This is
    # a temporal fix, removing it (hopefully) later when that bug is fixed in OPM Flow.
    if cfg.case == "spe11a" and len(times_det) != len(cpu):
        interp_cpu = interp1d(summary_times, cpu, fill_value="extrapolate")
        tmp = np.append(times_det[1:], summary_times[-1])
        cpu = interp_cpu(tmp)
    if sim.timeini > 0:
        cpu = cpu[-len(map_summary) - 1 :]
        cpu = cpu[1:] - cpu[:-1]
    else:
        cpu = cpu[-len(map_summary) :]
        cpu[1:] -= cpu[:-1]
    # Extend later the temporal fix to spe11b/c cases if this issue is observed
    assert len(map_summary) == len(
        cpu
    ), "Please raise an issue with 'spe11b/c cpu/infostep fix'"
    return cpu, map_summary, np.array(summary_times)


def build_time_series(
    sim: SimulationData,
    times_data: NDArray,
    metrics: dict,
    map_info: NDArray,
    map_summary: NDArray,
    interp_fgmip: interp1d,
    cpu: list,
) -> list:
    """Build regular performance time-series rows.

    Parameters
    ----------
    sim : SimulationData
        Loaded simulation readers and metadata.
    times_data : NDArray
        Requested output times.
    metrics : dict
        Extracted solver metrics.
    map_info : NDArray
        Mapping from INFOSTEP rows to output intervals.
    map_summary : NDArray
        Mapping from detailed intervals to summary records.
    interp_fgmip : interp1d
        Interpolated field gas mass in place.
    cpu : list
        CPU-time increments.

    Returns
    -------
    list[str]
        Header and rows for the regularly sampled performance CSV file.
    """
    header = (
        "# t [s], tstep [s], fsteps [-], mass [kg], dof [-], "
        + "nliter [-], nres [-], liniter [-], runtime [s], tlinsol [s]"
    )
    rows = [header]
    if sim.noskiprst == 0:
        rows.append(
            f"0.000e+00, 0.000e+00, 0.000e+00, 0.000e+00, "
            f"{sim.dof * sim.nocellsa:.3e}, 0.000e+00, 0.000e+00, "
            f"0.000e+00, 0.000e+00, 0.000e+00"
        )
        times_data = np.delete(times_data, 0)

    fsteps = metrics["fsteps"]
    nres = metrics["nres"]
    tlsolve = metrics["tlsolve"]
    linit = metrics["linit"]
    nlinit = metrics["nlinit"]
    tsteps = metrics["tsteps"]
    dof_val = sim.dof * sim.nocellsa
    nrows = len(times_data)

    freq = np.zeros(nrows, dtype=int)
    run, itd = 0, 0
    for j in range(nrows):
        if np.sum(cpu[map_summary == j]) == 0:
            run += 1
            freq[j] = run
        else:
            run = 0
            freq[j] = 0

    weig = np.ones(nrows, dtype=float)
    quan = 1.0
    for j in range(nrows - 1, -1, -1):
        if freq[j] > 0 and quan == 1.0:
            quan = freq[j] + 1.0
        elif freq[j] == 0:
            weig[j] = quan
            quan = 1.0
            continue
        weig[j] = quan

    max_block = map_info.max() + 1
    sum_tstep = np.zeros(max_block)
    cnt_tstep = np.zeros(max_block, dtype=int)
    sum_fsteps = np.zeros(max_block)
    sum_nlinit = np.zeros(max_block)
    sum_nres = np.zeros(max_block)
    sum_linit = np.zeros(max_block)
    sum_tlinsol = np.zeros(max_block)

    for b in range(max_block):
        ind = map_info == b
        if np.any(ind):
            sum_tstep[b] = np.sum(tsteps[ind])
            cnt_tstep[b] = np.sum(ind)
            sum_fsteps[b] = np.sum(fsteps[ind])
            sum_nlinit[b] = np.sum(nlinit[ind])
            sum_nres[b] = np.sum(nres[ind])
            sum_linit[b] = np.sum(linit[ind])
            sum_tlinsol[b] = np.sum(tlsolve[ind])

    cur_block = None
    cur_tstep = 0.0

    for j, time_val in enumerate(times_data):
        if freq[j] == 0:
            cur_block = j
            itd = map_summary == j
            if cnt_tstep[j] > 0:
                cur_tstep = sum_tstep[j] / cnt_tstep[j]
            else:
                cur_tstep = 0.0
        w = weig[j]
        rows.append(
            f"{time_val:.3e}, "
            f"{cur_tstep / w:.3e}, "
            f"{sum_fsteps[cur_block] / w:.3e}, "
            f"{interp_fgmip(time_val):.3e}, "
            f"{dof_val:.3e}, "
            f"{sum_nlinit[cur_block] / w:.3e}, "
            f"{sum_nres[cur_block] / w:.3e}, "
            f"{sum_linit[cur_block] / w:.3e}, "
            f"{np.sum(cpu[itd]) / w:.3e}, "
            f"{sum_tlinsol[cur_block] / w:.3e}"
        )

    return rows


def build_detailed_series(
    sim: SimulationData,
    metrics: dict,
    detail_info: NDArray,
    infotimes: NDArray,
    interp_fgmip: interp1d,
    cpu: list,
) -> list:
    """Build detailed performance time-series rows.

    Parameters
    ----------
    sim : SimulationData
        Loaded simulation readers and metadata.
    metrics : dict
        Extracted solver metrics.
    detail_info : NDArray
        Detail info.
    infotimes : NDArray
        Infotimes.
    interp_fgmip : interp1d
        Interpolated field gas mass in place.
    cpu : list
        CPU-time increments.

    Returns
    -------
    list[str]
        Header and rows for the detailed performance CSV file.
    """
    header = (
        "# t [s], tstep [s], fsteps [-], mass [kg], dof [-], nliter [-], "
        + "nres [-], liniter [-], runtime [s], tlinsol [s]"
    )
    rows = [header]
    for detail_index in range(np.max(detail_info) + 1):
        mask = detail_info == detail_index
        time_val = np.max(infotimes[mask])
        if time_val >= 0:
            rows.append(
                f"{time_val:.3e}, {np.max(metrics['tsteps'][mask]):.3e}, "
                f"{np.sum(metrics['fsteps'][mask]):.3e}, "
                f"{interp_fgmip(time_val):.3e}, {sim.dof*sim.nocellsa:.3e}, "
                f"{np.sum(metrics['nlinit'][mask]):.3e}, {np.sum(metrics['nres'][mask]):.3e}, "
                f"{np.sum(metrics['linit'][mask]):.3e}, {cpu[detail_index]:.3e}, "
                f"{np.sum(metrics['tlsolve'][mask]):.3e}"
            )
    return rows


def write_performance_csv(cfg: DataConfig, perf: dict) -> None:
    """Write regular and detailed performance CSV files.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    perf : dict
        Perf.
    """
    with open(
        f"{cfg.where}/{cfg.case}_performance_time_series.csv", "w", encoding="utf8"
    ) as file:
        file.write("\n".join(perf["series"]))
    with open(
        f"{cfg.where}/{cfg.case}_performance_time_series_detailed.csv",
        "w",
        encoding="utf8",
    ) as file:
        file.write("\n".join(perf["detailed"]))


def generate_sparse_data(cfg: DataConfig, sim: SimulationData) -> None:
    """Generate sparse benchmark time-series data.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    """
    sparse = build_sparse_data(cfg, sim)
    write_sparse_csv(cfg, sparse)


def build_sparse_data(cfg: DataConfig, sim: SimulationData) -> dict:
    """Build and interpolate sparse benchmark quantities.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    dict[str, NDArray]
        Sparse benchmark quantities interpolated to the requested output times.
    """
    times_data = np.linspace(0, sim.times[-1], round(sim.times[-1] / cfg.sparset) + 1)
    fipnum = list(sim.init["FIPNUM"])
    dx = np.array(sim.init["DX"])
    dy = np.array(sim.init["DY"])
    dz = np.array(sim.init["DZ"])
    fip_groups = get_fip_groups(cfg)
    summary_data = build_summary_data(cfg, sim, fipnum, fip_groups)
    m_c = (
        compute_mixing_measure(cfg, sim, fipnum, dx, dy, dz)
        if not sim.immiscible
        else [0.0] * (sim.norst - sim.noskiprst - 1)
    )
    interpolated = interpolate_sparse_data(times_data, sim, summary_data, m_c)
    return interpolated


def get_fip_groups(cfg: DataConfig) -> dict:
    """Return FIPNUM groups used by sparse benchmark quantities.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.

    Returns
    -------
    dict[str, list[int]]
        FIPNUM values contributing to dissolved, sealing, and boundary quantities.
    """
    if cfg.lower:
        result = {
            "diss_a": [2, 4, 8],
            "seal_a": [],
            "diss_b": [],
            "seal_b": [],
            "bound": [],
        }
    else:
        result = {
            "diss_a": [2, 4, 5, 8],
            "seal_a": [5, 8],
            "diss_b": [3, 6],
            "seal_b": [6],
            "bound": [],
        }
    if cfg.case != "spe11a":
        result["bound"] = [11]
    if cfg.case == "spe11c":
        result["diss_a"] += [13, 17]
        result["bound"] += [13, 17]
        if not cfg.lower:
            result["diss_a"] += [14]
            result["seal_a"] += [14]
            result["diss_b"] += [15, 16]
            result["seal_b"] += [16]
            result["bound"] += [14, 15, 16]
    return result


def build_summary_data(
    cfg: DataConfig, sim: SimulationData, fipnum: list, groups: dict
) -> dict:
    """Build sparse quantities from OPM summary vectors.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    fipnum : list
        FIPNUM values in global cell order.
    groups : dict
        FIPNUM groups for sparse benchmark quantities.

    Returns
    -------
    dict[str, NDArray]
        Sensor pressures and mobile, immobile, dissolved, sealing, and boundary
        mass series.
    """
    zero_series = 0.0 * sim.smspec["TIME"]
    pop1, pop2 = extract_boundary_pressures(cfg, sim, fipnum)
    result = {
        "pop1": pop1,
        "pop2": pop2,
        "moba": zero_series.copy(),
        "imma": zero_series.copy(),
        "dissa": zero_series.copy(),
        "seala": zero_series.copy(),
        "mobb": zero_series.copy(),
        "immb": zero_series.copy(),
        "dissb": zero_series.copy(),
        "sealb": zero_series.copy(),
        "sealt": zero_series.copy(),
        "boundtot": zero_series.copy(),
    }
    for i in groups["diss_a"]:
        result["moba"] += sim.smspec[f"RGKMO:{i}"]
        result["imma"] += sim.smspec[f"RGKTR:{i}"]
        result["dissa"] += sim.smspec[f"RGMDS:{i}"]
    for i in groups["seal_a"]:
        result["seala"] += sim.smspec[f"RGMDS:{i}"]
        result["seala"] += sim.smspec[f"RGKMO:{i}"]
        result["seala"] += sim.smspec[f"RGKTR:{i}"]
    for i in groups["diss_b"]:
        result["mobb"] += sim.smspec[f"RGKMO:{i}"]
        result["immb"] += sim.smspec[f"RGKTR:{i}"]
        result["dissb"] += sim.smspec[f"RGMDS:{i}"]
    for i in groups["seal_b"]:
        result["sealb"] += sim.smspec[f"RGMDS:{i}"]
        result["sealb"] += sim.smspec[f"RGKMO:{i}"]
        result["sealb"] += sim.smspec[f"RGKTR:{i}"]
    result["sealt"] = result["seala"] + result["sealb"]
    for name in ("RGMDS", "RGKMO", "RGKTR"):
        if not cfg.lower:
            result["sealt"] += sim.smspec[f"{name}:7"]
            result["sealt"] += sim.smspec[f"{name}:9"]
        else:
            if 7 in fipnum:
                result["sealt"] += sim.smspec[f"{name}:7"]
    for i in groups["bound"]:
        if i in fipnum:
            result["boundtot"] += sim.smspec[f"RGMDS:{i}"]
            result["boundtot"] += sim.smspec[f"RGKMO:{i}"]
            result["boundtot"] += sim.smspec[f"RGKTR:{i}"]
    return result


def extract_boundary_pressures(
    cfg: DataConfig, sim: SimulationData, fipnum: list
) -> tuple[list, list]:
    """Extract initial and summary pressure series at both sensors.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    fipnum : list
        FIPNUM values in global cell order.

    Returns
    -------
    pop1, pop2 : list[float]
        Pressure series at the first and second benchmark sensors, in pascals.
    """
    pressure = sim.unrst["PRESSURE", 0]
    pcgw = sim.unrst["PCGW", 0]
    index_pop1 = fipnum.index(8)
    pop1_value = (pressure[index_pop1] - pcgw[index_pop1]) * 1.0e5
    keys = sim.smspec.keys()
    summary_keys = [key for key in keys if key.startswith("BWPR")]
    summary_keys.sort()
    pop1 = [pop1_value] + list(sim.smspec[summary_keys[0]] * 1.0e5)
    if cfg.lower:
        pop2 = pop1
    else:
        index_pop2 = fipnum.index(9)
        pop2_value = (pressure[index_pop2] - pcgw[index_pop2]) * 1.0e5
        pop2 = [pop2_value] + list(sim.smspec[summary_keys[1]] * 1.0e5)
    return pop1, pop2


def compute_mixing_measure(
    cfg: DataConfig,
    sim: SimulationData,
    fipnum: list,
    dx: NDArray,
    dy: NDArray,
    dz: NDArray,
) -> list:
    """Calculate the Box C mixing measure for each restart step.

    Concentration differences are evaluated between Box C cells and valid
    neighboring cells without wrapping across grid boundaries.

    Parameters
    ----------
    cfg : DataConfig
        Initialized benchmark-data configuration.
    sim : SimulationData
        Loaded simulation readers and grid dimensions.
    fipnum : list
        FIPNUM values in global cell order.
    dx, dy, dz : np.ndarray
        Cell dimensions in the same order as ``fipnum``.

    Returns
    -------
    list[float]
        Mixing-measure values for the selected restart steps.

    """
    nx, ny, _ = sim.simdim
    box_mask = np.isin(fipnum, (4, 12, 17, 18))
    box_indices = np.flatnonzero(box_mask)

    i_indices = box_indices % nx
    j_indices = (box_indices // nx) % ny
    k_indices = box_indices // (nx * ny)

    has_x_neighbor = i_indices < nx - 1
    has_y_neighbor = j_indices > 0
    has_z_neighbor = k_indices > 0

    x_cells = box_indices[has_x_neighbor]
    y_cells = box_indices[has_y_neighbor]
    z_cells = box_indices[has_z_neighbor]

    x_neighbors = x_cells + 1
    y_neighbors = y_cells - nx
    z_neighbors = z_cells - nx * ny

    dx_box = dx[box_indices]
    dy_box = dy[box_indices]
    dz_box = dz[box_indices]

    density_ratio = WAT_DEN_REF / GAS_DEN_REF
    values = []

    for step in range(sim.noskiprst + 1, sim.norst):
        dissolved_ratio = np.asarray(sim.unrst["RSW", step])
        saturated_ratio = np.asarray(sim.unrst["RSWSAT", step])

        concentration = dissolved_ratio / (dissolved_ratio + density_ratio)
        concentration /= saturated_ratio / (saturated_ratio + density_ratio)

        x_variation = np.abs(concentration[x_neighbors] - concentration[x_cells])
        z_variation = np.abs(concentration[z_neighbors] - concentration[z_cells])

        if cfg.case != "spe11c":
            mixing_measure = np.sum(x_variation * dz_box[has_x_neighbor])
            mixing_measure += np.sum(z_variation * dx_box[has_z_neighbor])
        else:
            y_variation = np.abs(concentration[y_neighbors] - concentration[y_cells])
            mixing_measure = np.sum(
                x_variation * dy_box[has_x_neighbor] * dz_box[has_x_neighbor]
            )
            mixing_measure += np.sum(
                y_variation * dx_box[has_y_neighbor] * dz_box[has_y_neighbor]
            )
            mixing_measure += np.sum(
                z_variation * dx_box[has_z_neighbor] * dy_box[has_z_neighbor]
            )

        values.append(float(mixing_measure))

    return values


def interpolate_sparse_data(
    times_data: NDArray, sim: SimulationData, summary: dict, m_c: list
) -> dict:
    """Interpolate sparse quantities to the requested output times.

    Parameters
    ----------
    times_data : NDArray
        Requested output times.
    sim : SimulationData
        Loaded simulation readers and metadata.
    summary : dict
        Sparse summary quantities.
    m_c : list
        Mixing-measure values at restart times.

    Returns
    -------
    dict[str, NDArray]
        Sparse quantities and output times evaluated on the requested time grid.
    """
    result = {}
    tsim = sim.timesumary
    tlen = len(tsim)
    for key, values in summary.items():
        if isinstance(values, float):
            series = [0.0] * (tlen - 1)
        else:
            series = list(values)
        if len(series) == tlen - 1:
            series = [0.0] + series
        interp = interp1d(tsim, series, fill_value="extrapolate")
        result[key] = interp(times_data)
    interp_mc = interp1d(sim.times, [0.0] + list(m_c), fill_value="extrapolate")
    result["m_c"] = interp_mc(times_data)
    result["times"] = times_data
    return result


def write_sparse_csv(cfg: DataConfig, sparse: dict) -> None:
    """Write the sparse benchmark time-series CSV file.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sparse : dict
        Sparse.
    """
    header = (
        "# t [s], p1 [Pa], p2 [Pa], mobA [kg], immA [kg], dissA [kg], sealA [kg], "
        + "mobB [kg], immB [kg], dissB [kg], sealB [kg], MC [m], sealTot [kg]"
    )
    times = sparse["times"]
    pop1 = sparse["pop1"]
    pop2 = sparse["pop2"]
    moba = sparse["moba"]
    imma = sparse["imma"]
    dissa = sparse["dissa"]
    seala = sparse["seala"]
    mobb = sparse["mobb"]
    immb = sparse["immb"]
    dissb = sparse["dissb"]
    sealb = sparse["sealb"]
    mc = sparse["m_c"]
    sealt = sparse["sealt"]
    path = f"{cfg.where}/{cfg.case}_time_series.csv"
    with open(path, "w", encoding="utf8") as file:
        if cfg.case == "spe11a":
            file.write(header)
            file.writelines(
                f"\n{time_val:.3e}, {pop1[i]:.5e}, {pop2[i]:.5e}, "
                f"{moba[i]:.3e}, {imma[i]:.3e}, {dissa[i]:.3e}, "
                f"{seala[i]:.3e}, {mobb[i]:.3e}, {immb[i]:.3e}, "
                f"{dissb[i]:.3e}, {sealb[i]:.3e}, {mc[i]:.3e}, "
                f"{sealt[i]:.3e}"
                for i, time_val in enumerate(times)
            )
        else:
            file.write(header + ", boundTot [kg]")
            boundtot = sparse["boundtot"]
            file.writelines(
                f"\n{time_val:.4e}, {pop1[i]:.3e}, {pop2[i]:.3e}, "
                f"{moba[i]:.3e}, {imma[i]:.3e}, {dissa[i]:.3e}, "
                f"{seala[i]:.3e}, {mobb[i]:.3e}, {immb[i]:.3e}, "
                f"{dissb[i]:.3e}, {sealb[i]:.3e}, {mc[i]:.3e}, "
                f"{sealt[i]:.3e}, {boundtot[i]:.3e}"
                for i, time_val in enumerate(times)
            )


def generate_dense_data(cfg: DataConfig, sim: SimulationData) -> list[str]:
    """Generate dense and performance-spatial benchmark files.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    list[str]
        Names of the generated dense and performance-spatial CSV files.
    """
    files = []
    rstno, refgrid, mapping, actindr = prepare_dense_mapping(cfg, sim)
    if cfg.mode == "all" or cfg.mode[:5] == "dense":
        show_progress = sys.stdout.isatty()
        if show_progress:
            bar_ctx = alive_bar(len(rstno), bar="fish")
        else:
            bar_ctx = nullcontext()
        pyopmspe11_info("processing dense data")
        with bar_ctx as bar_animation:
            for step_index, restart in enumerate(rstno):
                if show_progress:
                    bar_animation()
                restart_index = restart + sim.noskiprst
                dense_step = build_dense_step(cfg, sim, mapping, restart_index, actindr)
                files.append(write_dense_csv(cfg, sim, refgrid, dense_step, step_index))
    if cfg.mode in ("all", "performance-spatial", "dense_performance-spatial"):
        files.extend(
            generate_performance_spatial_data(
                cfg, sim, rstno, refgrid, mapping, actindr
            )
        )
    return files


def supports_fast_dense_mapping(
    cfg: DataConfig, sim: SimulationData, dx: NDArray, dz: NDArray
) -> bool:
    """Return whether aligned grids support direct dense mapping.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    dx : NDArray
        Cell sizes along x.
    dz : NDArray
        Cell sizes along z.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if cfg.lower:
        return False
    if np.min(dz) != np.max(dz):
        return False
    if cfg.nxyz[2] == sim.simdim[2] and cfg.nxyz[0] == sim.simdim[0]:
        return np.min(dx) == np.max(dx)
    if cfg.nxyz[2] == sim.simdim[2] and cfg.nxyz[0] == sim.simdim[0] - 2:
        return np.min(dx[2:-2]) == np.max(dx[2:-2])
    if sim.simdim[2] % cfg.nxyz[2] == 0 and sim.simdim[0] % cfg.nxyz[0] == 0:
        return np.min(dx) == np.max(dx)
    if sim.simdim[2] % cfg.nxyz[2] == 0 and (sim.simdim[0] - 2) % cfg.nxyz[0] == 0:
        return np.min(dx[2:-2]) == np.max(dx[2:-2])
    return False


def build_general_dense_mapping(
    cfg: DataConfig,
    sim: SimulationData,
    refgrid: tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray],
    geometry: tuple[NDArray, NDArray, list],
) -> tuple[list[list[list[int | float]]], NDArray]:
    """Map simulation cells to reporting cells by polygon intersection.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    refgrid : tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
        Reporting-grid vertices and centers.
    geometry : tuple[NDArray, NDArray, list]
        Simulation centers and cell polygons.

    Returns
    -------
    cell_ind : list[list[list[int | float]]]
        Reporting-cell indices and overlap weights for each simulation cell.
    cell_cent : NDArray
        Representative simulation-cell index for each reporting cell.
    """
    refxvert, _, refzvert, refxcent, _, refzcent = refgrid
    simxcent, simzcent, simpoly = geometry
    cell_ind: list[list[list[int | float]]] = [[] for _ in range(sim.nocellsxz)]
    cell_cent = np.zeros(cfg.nocellsrepgrid, dtype=float)
    nrefx = cfg.nxyz[0]
    nrefz = cfg.nxyz[2]
    refpoly = [None] * (nrefx * nrefz)
    refxgrid = np.zeros(nrefx * nrefz)
    refzgrid = np.zeros(nrefx * nrefz)
    idx = index.Index()
    rid = 0
    for kz, zcen in enumerate(refzcent):
        zv0 = refzvert[kz]
        zv1 = refzvert[kz + 1]
        for ix, xcen in enumerate(refxcent):
            xv0 = refxvert[ix]
            xv1 = refxvert[ix + 1]
            refxgrid[rid] = xcen
            refzgrid[rid] = zcen
            poly = Polygon(((xv0, zv0), (xv1, zv0), (xv1, zv1), (xv0, zv1)))
            refpoly[rid] = poly
            idx.insert(rid, poly.bounds)
            rid += 1
    pyopmspe11_info(
        "processing polygon intersections between simulation and reporting grids"
    )
    show_progress = sys.stdout.isatty()
    if show_progress:
        bar_ctx = alive_bar(len(simpoly), bar="fish")
    else:
        bar_ctx = nullcontext()
    with bar_ctx as bar_animation:
        for sim_cell, poly_s in enumerate(simpoly):
            if show_progress:
                bar_animation()
            if poly_s.area > 0.0:
                area_s = poly_s.area
                for tgt in idx.intersection(poly_s.bounds):
                    a = poly_s.intersection(refpoly[tgt]).area
                    if a > 0.0:
                        cell_ind[sim_cell].append([tgt, a / area_s])
            else:
                cell_ind[sim_cell] = cell_ind[sim_cell - 1]
    pyopmspe11_info("finding the cell indices between simulation and reporting grids")
    show_progress = sys.stdout.isatty()
    if show_progress:
        bar_ctx = alive_bar(len(refxgrid), bar="fish")
    else:
        bar_ctx = nullcontext()
    with bar_ctx as bar_animation:
        for rep, (xc, zc) in enumerate(zip(refxgrid, refzgrid)):
            if show_progress:
                bar_animation()
            cell_cent[rep] = np.nanargmin(np.abs(simxcent - xc) + np.abs(simzcent - zc))
    return cell_ind, cell_cent


def prepare_dense_mapping(cfg: DataConfig, sim: SimulationData) -> tuple[
    list,
    tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray],
    tuple[list[list[list[int | float]]], NDArray],
    NDArray,
]:
    """Prepare static geometry and the simulation-to-report mapping.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    rstno : list[int]
        Restart indices selected for dense output.
    refgrid : tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
        Reporting-grid vertices and centers along x, y, and z.
    mapping : tuple[list[list[list[int | float]]], NDArray]
        Weighted cell mapping and representative simulation cells.
    actindr : NDArray
        Indices of inactive reporting-grid cells.
    """
    rstno = select_dense_restart_steps(cfg, sim)
    refgrid = build_dense_reference_grid(cfg)
    simxcent, simycent, simzcent, simpoly, satnum = extract_simulation_geometry(
        cfg, sim
    )
    dx = np.array(sim.init["DX"])
    dz = np.array(sim.init["DZ"])
    if supports_fast_dense_mapping(cfg, sim, dx, dz):
        cell_ind, cell_cent = build_fast_dense_mapping(cfg, sim, dx, dz)
    else:
        cell_ind, cell_cent = build_general_dense_mapping(
            cfg, sim, refgrid, (simxcent, simzcent, simpoly)
        )
    cell_ind, cell_cent, actindr = finalize_dense_mapping(
        cfg, sim, refgrid, (cell_ind, cell_cent), simycent, satnum
    )
    return rstno, refgrid, (cell_ind, cell_cent), actindr


def select_dense_restart_steps(cfg: DataConfig, sim: SimulationData) -> list[int]:
    """Select restart indices for requested dense output times.

    Each requested time must match an available restart time within floating-
    point precision.

    Parameters
    ----------
    cfg : DataConfig
        Initialized benchmark-data configuration.
    sim : SimulationData
        Loaded readers and timing data.

    Returns
    -------
    list[int]
        Restart indices corresponding to the requested dense output times.

    Raises
    ------
    ValueError
        If a requested time does not match an available restart time.

    """
    simulation_times = np.asarray(sim.times, dtype=float)
    requested_times = np.atleast_1d(cfg.denset)
    max_time = np.max(np.abs(simulation_times))
    tolerance = max(1e-6, 10 * np.spacing(max_time))
    restart_indices = []

    for requested_time in requested_times:
        restart_index = int(np.argmin(np.abs(simulation_times - requested_time)))
        if not np.isclose(
            simulation_times[restart_index],
            requested_time,
            rtol=0.0,
            atol=tolerance,
        ):
            pyopmspe11_error(
                f"requested dense output time {requested_time} s does not "
                "match an available restart time"
            )
        restart_indices.append(restart_index)

    return restart_indices


def build_dense_reference_grid(
    cfg: DataConfig,
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Build reporting-grid vertices and centers.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.

    Returns
    -------
    refxvert, refyvert, refzvert : NDArray
        Reporting-grid vertices along x, y, and z.
    refxcent, refycent, refzcent : NDArray
        Reporting-grid cell centers along x, y, and z.
    """
    refxvert = np.linspace(0, cfg.dims[0], cfg.nxyz[0] + 1)
    refyvert = np.linspace(0, cfg.dims[1], cfg.nxyz[1] + 1)
    refzvert = np.linspace(0, cfg.dims[2], cfg.nxyz[2] + 1)
    refxcent = 0.5 * (refxvert[1:] + refxvert[:-1])
    refycent = 0.5 * (refyvert[1:] + refyvert[:-1])
    refzcent = 0.5 * (refzvert[1:] + refzvert[:-1])
    return refxvert, refyvert, refzvert, refxcent, refycent, refzcent


def extract_simulation_geometry(
    cfg: DataConfig, sim: SimulationData
) -> tuple[NDArray, NDArray, NDArray, list, NDArray]:
    """Extract simulation centers, polygons, and SATNUM values.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.

    Returns
    -------
    simxcent, simycent, simzcent : NDArray
        Simulation-cell centers along x, y, and z.
    simpoly : list[Polygon]
        Simulation-cell polygons in the x-z plane.
    satnum : NDArray
        Saturation-region identifiers in global cell order.
    """
    simxcent = np.zeros(sim.nocellsxz)
    simzcent = np.zeros(sim.nocellsxz)
    simycent = np.zeros(sim.simdim[1])
    simpoly = [None] * sim.nocellsxz
    satnum = np.array(sim.init["SATNUM"])
    z_0 = 155.04166666666666 if cfg.case == "spe11c" else 0.0
    nx, ny, nz = sim.simdim
    dims_z = cfg.dims[2]
    for j in range(nz):
        for i in range(nx):
            n = i + (nz - j - 1) * nx
            xyz = sim.egrid.xyz_from_ijk(i, 0, nz - j - 1)
            poly = Polygon(
                [
                    [xyz[0][0], dims_z - (xyz[2][0] - z_0)],
                    [xyz[0][1], dims_z - (xyz[2][1] - z_0)],
                    [xyz[0][5], dims_z - (xyz[2][5] - z_0)],
                    [xyz[0][4], dims_z - (xyz[2][4] - z_0)],
                ]
            )
            simpoly[n] = poly
            xcen, zcen = (float(v) for v in poly.centroid.wkt[7:-1].split())
            simxcent[n] = xcen if zcen > 0 else np.nan
            simzcent[n] = zcen if zcen > 0 else np.nan
    for j in range(ny):
        xyz = sim.egrid.xyz_from_ijk(0, j, 0)
        simycent[j] = 0.5 * (xyz[1][2] - xyz[1][1]) + xyz[1][1]
    if cfg.lower and sim.cornpoint:
        nx = sim.simdim[0]
        simxcent = np.insert(simxcent, 0, simxcent[:nx])
        simzcent = np.insert(simzcent, 0, simzcent[:nx] + 1e-4)
    return simxcent, simycent, simzcent, simpoly, satnum


def build_fast_dense_mapping(
    cfg: DataConfig, sim: SimulationData, dx: NDArray, dz: NDArray
) -> tuple[list[list[list[int | float]]], NDArray]:
    """Build a direct mapping for aligned simulation and reporting grids.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    dx : NDArray
        Cell sizes along x.
    dz : NDArray
        Cell sizes along z.

    Returns
    -------
    cell_ind : list[list[list[int | float]]]
        Reporting-cell indices and overlap weights for each simulation cell.
    cell_cent : NDArray
        Representative simulation-cell index for each reporting cell.
    """
    cell_ind: list[list[list[int | float]]] = [[] for _ in range(sim.nocellsxz)]
    cell_indc = np.zeros(sim.nocellsxz, dtype=int)
    cell_cent = np.zeros(cfg.nocellsrepgrid, dtype=float)
    iszunif = (np.min(dz) == np.max(dz)) and not cfg.lower

    if (
        iszunif
        and cfg.nxyz[2] == sim.simdim[2]
        and np.min(dx) == np.max(dx)
        and cfg.nxyz[0] == sim.simdim[0]
    ):
        for layer in range(cfg.nxyz[2]):
            cell_cent[
                (cfg.nxyz[2] - layer - 1)
                * cfg.nxyz[0] : (cfg.nxyz[2] - layer)
                * cfg.nxyz[0]
            ] = range(layer * cfg.nxyz[0], (layer + 1) * cfg.nxyz[0])
        cell_indc[:] = cell_cent
        for i, value in enumerate(cell_indc):
            cell_ind[i] = [[int(value), 1.0]]

    elif (
        iszunif
        and cfg.nxyz[2] == sim.simdim[2]
        and np.min(dx[2:-2]) == np.max(dx[2:-2])
        and cfg.nxyz[0] == sim.simdim[0] - 2
    ):
        for layer in range(cfg.nxyz[2]):
            base = (sim.simdim[2] - layer - 1) * sim.simdim[0]
            cell_indc[base] = layer * cfg.nxyz[0]
            cell_indc[base + 1 : base + sim.simdim[0] - 1] = range(
                layer * cfg.nxyz[0], (layer + 1) * cfg.nxyz[0] + 1
            )
            cell_indc[base + sim.simdim[0] - 1] = (layer + 1) * cfg.nxyz[0] - 1
            cell_cent[
                (cfg.nxyz[2] - layer - 1)
                * cfg.nxyz[0] : (cfg.nxyz[2] - layer)
                * cfg.nxyz[0]
            ] = [
                value + 2 * layer
                for value in range(
                    layer * cfg.nxyz[0] + 1, (layer + 1) * cfg.nxyz[0] + 1
                )
            ]
        for i, value in enumerate(cell_indc):
            cell_ind[i] = [[int(value), 1.0]]

    elif (
        iszunif
        and sim.simdim[2] % cfg.nxyz[2] == 0
        and np.min(dx) == np.max(dx)
        and sim.simdim[0] % cfg.nxyz[0] == 0
    ):
        x_repeat = sim.simdim[0] // cfg.nxyz[0]
        z_repeat = sim.simdim[2] // cfg.nxyz[2]
        for layer in range(cfg.nxyz[2]):
            cell_cent[
                (cfg.nxyz[2] - layer - 1)
                * cfg.nxyz[0] : (cfg.nxyz[2] - layer)
                * cfg.nxyz[0]
            ] = [
                value * x_repeat
                + (x_repeat / 2 - 1)
                + (z_repeat / 2 - 1) * sim.simdim[0]
                + layer * (z_repeat - 1) * sim.simdim[0]
                for value in range(layer * cfg.nxyz[0], (layer + 1) * cfg.nxyz[0])
            ]
        for layer in range(cfg.nxyz[2]):
            for zloc in range(z_repeat):
                for xloc in range(cfg.nxyz[0]):
                    start = (
                        sim.simdim[2] - (layer * z_repeat + zloc) - 1
                    ) * sim.simdim[0] + xloc * x_repeat
                    cell_indc[start : start + x_repeat] = [
                        xloc + layer * cfg.nxyz[0]
                    ] * x_repeat
        for i, value in enumerate(cell_indc):
            cell_ind[i] = [[int(value), 1.0]]

    elif (
        iszunif
        and sim.simdim[2] % cfg.nxyz[2] == 0
        and np.min(dx[2:-2]) == np.max(dx[2:-2])
        and (sim.simdim[0] - 2) % cfg.nxyz[0] == 0
    ):
        x_repeat = (sim.simdim[0] - 2) // cfg.nxyz[0]
        z_repeat = sim.simdim[2] // cfg.nxyz[2]
        for layer in range(cfg.nxyz[2]):
            cell_cent[
                (cfg.nxyz[2] - layer - 1)
                * cfg.nxyz[0] : (cfg.nxyz[2] - layer)
                * cfg.nxyz[0]
            ] = [
                value * x_repeat
                + (x_repeat / 2 - 1)
                + (z_repeat / 2 - 1) * sim.simdim[0]
                + layer * (z_repeat - 1) * sim.simdim[0]
                + 2 * layer
                + 1
                for value in range(layer * cfg.nxyz[0], (layer + 1) * cfg.nxyz[0])
            ]
        for layer in range(cfg.nxyz[2]):
            for zloc in range(z_repeat):
                for xloc in range(cfg.nxyz[0]):
                    base = (sim.simdim[2] - (layer * z_repeat + zloc) - 1) * sim.simdim[
                        0
                    ] + xloc * x_repeat
                    cell_indc[base] = layer * cfg.nxyz[0] + xloc
                    cell_indc[base + 1 : base + x_repeat + 1] = [
                        layer * cfg.nxyz[0] + xloc
                    ] * x_repeat
                    cell_indc[base + x_repeat + 1] = layer * cfg.nxyz[0] + xloc
        for i, value in enumerate(cell_indc):
            cell_ind[i] = [[int(value), 1.0]]

    return cell_ind, cell_cent


def finalize_dense_mapping(
    cfg: DataConfig,
    sim: SimulationData,
    refgrid: tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray],
    mapping: tuple[list[list[list[int | float]]], NDArray],
    simycent: NDArray,
    satnum: NDArray,
) -> tuple[list[list[list[int | float]]], NDArray, NDArray]:
    """Apply inactive-cell and SPE11C y-axis mapping adjustments.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    refgrid : tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
        Reporting-grid vertices and centers.
    mapping : tuple[list[list[list[int | float]]], NDArray]
        Simulation-to-report mapping and representative cells.
    simycent : NDArray
        Simulation-cell centers along y.
    satnum : NDArray
        SATNUM values in global cell order.

    Returns
    -------
    cell_ind : list[list[list[int | float]]]
        Final extensive-quantity mapping for all simulation cells.
    cell_cent : NDArray
        Final representative simulation cells for intensive quantities.
    actindr : NDArray
        Indices of inactive reporting-grid cells.
    """
    cell_ind, cell_cent = mapping
    actindr = np.empty(0)
    if np.max(satnum) < 7 and cfg.case == "spe11a":
        actindr = find_inactive_report_cells(cfg, sim, cell_ind)
    if cfg.case == "spe11c":
        cell_cent = handle_yaxis_mapping_intensive(
            cfg, sim, cell_cent, refgrid[4], simycent
        )
        cell_ind = handle_yaxis_mapping_extensive(
            cfg, sim, cell_ind, simycent, refgrid[1]
        )
    return cell_ind, cell_cent, actindr


def build_dense_step(
    cfg: DataConfig,
    sim: SimulationData,
    mapping: tuple[list[list[list[int | float]]], NDArray],
    restart_index: int,
    actindr: NDArray,
) -> dict:
    """Build all dense quantities for one restart step.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    mapping : tuple[list[list[list[int | float]]], NDArray]
        Simulation-to-report mapping and representative cells.
    restart_index : int
        Restart report-step index.
    actindr : NDArray
        Inactive reporting-cell indices.

    Returns
    -------
    dict[str, NDArray]
        Simulation-grid and reporting-grid arrays for all dense quantities.
    """
    names = ["pressure", "sgas", "xco2", "xh2o", "gden", "wden", "tco2"]
    if not sim.isothermal:
        names = ["temp"] + names
    arrays = generate_arrays(cfg, sim, names, restart_index, actindr)
    map_dense_arrays_to_report_grid(sim, mapping, arrays)
    return arrays


def write_dense_csv(
    cfg: DataConfig,
    sim: SimulationData,
    refgrid: tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray],
    dense_step: dict,
    step_index: int,
) -> str:
    """Write one dense spatial benchmark CSV file.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    refgrid : tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
        Reporting-grid vertices and centers.
    dense_step : dict
        Dense step.
    step_index : int
        Selected dense output index.

    Returns
    -------
    str
        Generated filename or formatted text.
    """
    name_t, text = get_header(cfg, sim, step_index)
    if cfg.lower:
        dense_step["tco2_refg"][np.isnan(dense_step["sgas_refg"])] = np.nan
    _, _, _, refxcent, refycent, refzcent = refgrid
    nx, ny, nz = cfg.nxyz
    p_arr = dense_step["pressure_refg"]
    s_arr = dense_step["sgas_refg"]
    xco2_arr = dense_step["xco2_refg"]
    xh2o_arr = dense_step["xh2o_refg"]
    gden_arr = dense_step["gden_refg"]
    wden_arr = dense_step["wden_refg"]
    tco2_arr = dense_step["tco2_refg"]
    temp_arr = dense_step.get("temp_refg")
    file_name = f"{cfg.case}_spatial_map_{name_t}.csv"
    path = f"{cfg.where}/{cfg.case}_spatial_map_{name_t}.csv"
    with open(path, "w", encoding="utf8") as file:
        file.write("\n".join(text))
        for idz, zcord in enumerate(refzcent):
            idxy = 0
            for ycord in refycent:
                for xcord in refxcent:
                    cell = -nx * ny * (nz - idz) + idxy
                    p = p_arr[cell]
                    if np.isnan(p):
                        co2v = tco2_arr[cell]
                        co2 = "n/a" if np.isnan(co2v) else f"{co2v:.3e}"
                        if cfg.case == "spe11a":
                            row = (
                                f"{xcord:.3e}, {zcord:.3e}, n/a, n/a, n/a, n/a, n/a, n/a, {co2}"
                                + (", n/a" if not sim.isothermal else "")
                            )
                        elif cfg.case == "spe11b":
                            row = (
                                f"{xcord:.3e}, {zcord:.3e}, n/a, n/a, n/a, n/a, n/a, n/a, "
                                f"{co2}, n/a"
                            )
                        else:
                            row = (
                                f"{xcord:.3e}, {ycord:.3e}, {zcord:.3e}, n/a, n/a, n/a, n/a, "
                                f"n/a, n/a, {co2}, n/a"
                            )
                    else:
                        pf = f"{p:.3e}"
                        sf = f"{s_arr[cell]:.3e}"
                        gf = f"{gden_arr[cell]:.3e}"
                        wf = f"{wden_arr[cell]:.3e}"
                        co2 = f"{tco2_arr[cell]:.3e}"
                        if sim.immiscible:
                            xf = hf = "n/a"
                        else:
                            xf = f"{xco2_arr[cell]:.3e}"
                            hf = f"{xh2o_arr[cell]:.3e}"
                        tf = f"{temp_arr[cell]:.3e}" if temp_arr is not None else None
                        if cfg.case == "spe11a":
                            row = (
                                f"{xcord:.3e}, {zcord:.3e}, {pf}, {sf}, {xf}, {hf}, "
                                f"{gf}, {wf}, {co2}" + (f", {tf}" if tf else "")
                            )
                        elif cfg.case == "spe11b":
                            row = (
                                f"{xcord:.3e}, {zcord:.3e}, {pf}, {sf}, {xf}, {hf}, {gf}, "
                                f"{wf}, {co2}, {tf}"
                            )
                        else:
                            row = (
                                f"{xcord:.3e}, {ycord:.3e}, {zcord:.3e}, {pf}, {sf}, {xf}, "
                                f"{hf}, {gf}, {wf}, {co2}, {tf}"
                            )
                    file.write("\n" + row)
                    idxy += 1
    return file_name


def handle_yaxis_mapping_extensive(
    cfg: DataConfig,
    sim: SimulationData,
    cell_ind: list[list[list[int | float]]],
    simycent: NDArray,
    refyvert: NDArray,
) -> list[list[list[int | float]]]:
    """Extend indices for y direction (extensive).

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    cell_ind : list[list[list[int | float]]]
        Weighted simulation-to-report cell mapping.
    simycent : NDArray
        Simulation-cell centers along y.
    refyvert : NDArray
        Reporting-grid vertices along y.

    Returns
    -------
    list[list[list[int | float]]]
        Mapping expanded across the SPE11C y direction with overlap weights.
    """
    simyvert = [0.0]
    for yval in simycent:
        simyvert.append(simyvert[-1] + 2.0 * (yval - simyvert[-1]))
    weights = []
    indy = []
    ind = 0
    for y_i, y_f in pairwise(simyvert):
        if refyvert[ind + 1] <= y_i:
            ind += 1
        if refyvert[ind] <= y_i and y_f <= refyvert[ind + 1]:
            indy.append(ind)
            weights.append([1.0])
        else:
            w0 = (refyvert[ind + 1] - y_i) / (y_f - y_i)
            w1 = (y_f - refyvert[ind + 1]) / (y_f - y_i)
            indy.append(ind)
            weights.append([w0, w1])
            ind += 1
    nx, ny, nz = sim.simdim
    nrep_x = cfg.nxyz[0]
    expanded: list[list[list[int | float]]] = [[] for _ in range(sim.nocellst)]
    for iz in range(nz):
        base_sim = nx * (nz - iz - 1)
        base_rep = nx * ny * (nz - iz - 1)
        maps = [
            [
                [tgt + (tgt // nrep_x) * nrep_x * (cfg.nxyz[1] - 1), w * weights[0][0]]
                for tgt, w in row
            ]
            for row in cell_ind[base_sim : base_sim + nx]
        ]
        expanded[base_rep : base_rep + nx] = maps
        for j, iy in enumerate(indy[1:]):
            start = base_rep + nx * (j + 1)
            wy = weights[j + 1][0]
            expanded[start : start + nx] = [
                [[tgt + iy * nrep_x, w * wy] for tgt, w in row] for row in maps
            ]
    return expanded


def handle_yaxis_mapping_intensive(
    cfg: DataConfig,
    sim: SimulationData,
    cell_cent: NDArray,
    refycent: NDArray,
    simycent: NDArray,
) -> NDArray:
    """Extend representative cell indices for y direction (intensive).

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    cell_cent : NDArray
        Representative simulation cell for each reporting cell.
    refycent : NDArray
        Reporting-grid centers along y.
    simycent : NDArray
        Simulation-cell centers along y.

    Returns
    -------
    NDArray
        Calculated numeric values.
    """
    indy = np.array([np.argmin(np.abs(simycent - y)) for y in refycent])
    expanded = np.zeros(cfg.nocellsrepgrid, dtype=int)
    nx, ny, nz = cfg.nxyz
    gx = sim.simdim[0]
    for iz in range(nz):
        base_xz = nx * (nz - iz - 1)
        base_xyz = nx * ny * (nz - iz - 1)
        row = cell_cent[base_xz : base_xz + nx]
        mults = np.floor(row / gx) if iz != 0 else 0
        values = row + mults * gx * (sim.simdim[1] - 1)
        expanded[base_xyz : base_xyz + nx] = values
        for j, iy in enumerate(indy[1:]):
            start = base_xyz + nx * (j + 1)
            expanded[start : start + nx] = iy * gx + values
    return expanded


def find_inactive_report_cells(
    cfg: DataConfig, sim: SimulationData, cell_ind: list[list[list[int | float]]]
) -> NDArray:
    """Find reporting cells not covered by active simulation cells.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    cell_ind : list[list[list[int | float]]]
        Weighted simulation-to-report cell mapping.

    Returns
    -------
    NDArray
        Calculated numeric values.
    """
    actindr = []
    for i in sim.actind:
        for mask in cell_ind[i]:
            actindr.append(mask[0])
    actindr = list(dict.fromkeys(actindr))
    allc = np.linspace(0, cfg.nocellsrepgrid - 1, cfg.nocellsrepgrid, dtype=int)
    return np.delete(allc, actindr)


def generate_performance_spatial_data(
    cfg: DataConfig,
    sim: SimulationData,
    rstno: list,
    refgrid: tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray],
    mapping: tuple[list, NDArray],
    actindr: NDArray,
) -> list[str]:
    """Generate performance-spatial benchmark CSV files.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    rstno : list
        Selected restart indices.
    refgrid : tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
        Reporting-grid vertices and centers.
    mapping : tuple[list, NDArray]
        Simulation-to-report mapping and representative cells.
    actindr : NDArray
        Inactive reporting-cell indices.

    Returns
    -------
    list[str]
        Names of the generated performance-spatial CSV files.
    """
    files = []
    cell_ind, _ = mapping
    _, _, _, refxcent, refycent, refzcent = refgrid
    counter = 0.0 * np.ones(cfg.nocellsrepgrid)
    pore_volume = 0.0 * np.ones(cfg.nocellsrepgrid)
    if actindr.size > 0:
        pore_volume[actindr] = 1.0
    latest_dts, cvol_refg, arat_refg, valid = map_static_performance_properties(
        cfg, sim, cell_ind, counter, pore_volume
    )
    names = ("co2mn", "h2omn", "co2mb", "h2omb")
    show_progress = sys.stdout.isatty()
    if show_progress:
        bar_ctx = alive_bar(len(rstno), bar="fish")
    else:
        bar_ctx = nullcontext()
    pyopmspe11_info("processing performance spatial data")
    with bar_ctx as bar_animation:
        for i, rst in enumerate(rstno):
            if show_progress:
                bar_animation()
            arrays = initialize_performance_arrays(sim, names)
            step_index = rst + sim.noskiprst
            if step_index > 0:
                populate_performance_arrays(sim, arrays, step_index - 1)
            refg = map_performance_to_report_grid(
                cfg, sim, arrays, cell_ind, latest_dts[i], pore_volume, valid
            )
            files.append(
                write_dense_performance_spatial(
                    cfg, refg, cvol_refg, arat_refg, refxcent, refycent, refzcent, i
                )
            )
    return files


def map_performance_to_report_grid(
    cfg: DataConfig,
    sim: SimulationData,
    arrays: dict,
    cell_ind: list,
    delta_t: float,
    pore_volume: NDArray,
    valid: NDArray,
) -> dict:
    """Map residual and mass-balance metrics to the reporting grid.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    arrays : dict
        Simulation-grid quantity arrays.
    cell_ind : list
        Weighted simulation-to-report cell mapping.
    delta_t : float
        Latest accepted time-step length.
    pore_volume : NDArray
        Accumulated pore volume per reporting cell.
    valid : NDArray
        Mask of reporting cells with positive pore volume.

    Returns
    -------
    dict[str, NDArray]
        Normalized residual and mass-balance quantities on the reporting grid.
    """
    refg = {
        "co2mn": np.full(cfg.nocellsrepgrid, -np.inf),
        "h2omn": np.full(cfg.nocellsrepgrid, -np.inf),
        "co2mb": np.zeros(cfg.nocellsrepgrid),
        "h2omb": np.zeros(cfg.nocellsrepgrid),
    }
    co2mn = arrays["co2mn_array"]
    h2omn = arrays["h2omn_array"]
    co2mb = arrays["co2mb_array"]
    h2omb = arrays["h2omb_array"]
    ref_co2mn = refg["co2mn"]
    ref_h2omn = refg["h2omn"]
    ref_co2mb = refg["co2mb"]
    ref_h2omb = refg["h2omb"]
    for cell in sim.actind:
        v_co2mn = co2mn[cell]
        v_h2omn = h2omn[cell]
        v_co2mb = co2mb[cell]
        v_h2omb = h2omb[cell]
        for tgt, w in cell_ind[cell]:
            ref_co2mn[tgt] = max(ref_co2mn[tgt], v_co2mn * w)
            ref_h2omn[tgt] = max(ref_h2omn[tgt], v_h2omn * w)
            ref_co2mb[tgt] += v_co2mb * w
            ref_h2omb[tgt] += v_h2omb * w
    ref_co2mn[np.isfinite(ref_co2mn)] *= delta_t
    ref_h2omn[np.isfinite(ref_h2omn)] *= delta_t
    ref_co2mb[valid] = delta_t * ref_co2mb[valid] / pore_volume[valid]
    ref_h2omb[valid] = delta_t * ref_h2omb[valid] / pore_volume[valid]
    return refg


def map_static_performance_properties(
    cfg: DataConfig,
    sim: SimulationData,
    cell_ind: list,
    counter: NDArray,
    pore_volume: NDArray,
) -> tuple[list, NDArray, NDArray, NDArray]:
    """Map static cell-volume and aspect-ratio metrics.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    cell_ind : list
        Weighted simulation-to-report cell mapping.
    counter : NDArray
        Number of simulation contributions per reporting cell.
    pore_volume : NDArray
        Accumulated pore volume per reporting cell.

    Returns
    -------
    latest_dts : list[float]
        Latest accepted time-step size for each dense output time.
    cvol_refg : NDArray
        Average simulation-cell volume on the reporting grid.
    arat_refg : NDArray
        Average cell aspect ratio on the reporting grid.
    valid : NDArray
        Mask of reporting cells with positive mapped pore volume.
    """
    tmp1, tmp2 = [], []
    with open(
        f"{cfg.flowfol}/{cfg.outfol.split('/')[-1].upper()}.INFOSTEP",
        "r",
        encoding="utf8",
    ) as file:
        for i, row in enumerate(csv.reader(file)):
            if i > 0:
                vals = row[0].strip().split()
                tmp1.append(86400.0 * float(vals[0]))
                tmp2.append(86400.0 * float(vals[1]))
    infotimes = np.array(tmp1)
    tsteps = np.array(tmp2)
    latest_dts = []
    for time_val in cfg.denset[:-1]:
        pos = np.argmin(np.abs(infotimes - (time_val + sim.timeini)))
        latest_dts.append(tsteps[pos - 1] if pos > 0 else 0.0)
    latest_dts.append(tsteps[-1])
    cvol_array = np.zeros(sim.nocellst)
    arat_array = np.zeros(sim.nocellst)
    cvol_refg = np.zeros(cfg.nocellsrepgrid)
    arat_refg = np.zeros(cfg.nocellsrepgrid)
    act = sim.actind
    cvol_array[act] = sim.porva / np.array(sim.init["PORO"])
    if cfg.case != "spe11c":
        arat_array[act] = np.array(sim.init["DZ"]) / np.array(sim.init["DX"])
    else:
        dx = np.array(sim.init["DX"])
        dy = np.array(sim.init["DY"])
        arat_array[act] = np.array(sim.init["DZ"]) / np.sqrt(dx**2 + dy**2)
    for cell in act:
        pv = sim.porv[cell]
        for tgt, _ in cell_ind[cell]:
            cvol_refg[tgt] += cvol_array[cell]
            arat_refg[tgt] += arat_array[cell]
            counter[tgt] += 1.0
            pore_volume[tgt] += pv
    mask = counter > 0.0
    cvol_refg[mask] /= counter[mask]
    arat_refg[mask] /= counter[mask]
    cvol_refg[cvol_refg < 1e-12] = np.nan
    arat_refg[arat_refg < 1e-12] = np.nan
    valid = pore_volume > 0.0
    return latest_dts, cvol_refg, arat_refg, valid


def initialize_performance_arrays(
    sim: SimulationData, names: tuple[str, str, str, str]
) -> dict:
    """Initialize global arrays for performance-spatial quantities.

    Parameters
    ----------
    sim : SimulationData
        Loaded simulation readers and metadata.
    names : tuple[str, str, str, str]
        Quantity names to initialize or populate.

    Returns
    -------
    dict[str, NDArray]
        Zero-filled global arrays for the requested performance quantities.
    """
    arrays = {}
    for name in names:
        arrays[f"{name}_array"] = np.zeros(sim.nocellst)
    return arrays


def populate_performance_arrays(
    sim: SimulationData, arrays: dict, step_index: int
) -> None:
    """Populate performance arrays from one restart step.

    Parameters
    ----------
    sim : SimulationData
        Loaded simulation readers and metadata.
    arrays : dict
        Simulation-grid quantity arrays.
    step_index : int
        Selected dense output index.
    """
    act = sim.actind
    co2mb = arrays["co2mb_array"]
    h2omb = arrays["h2omb_array"]
    co2mn = arrays["co2mn_array"]
    h2omn = arrays["h2omn_array"]
    porva = sim.porva
    co2mb[act] = np.array(sim.unrst["RES_GAS", step_index + 1])
    if sim.unrst.count("RES_WAT", step_index + 1):
        h2omb[act] = np.array(sim.unrst["RES_WAT", step_index + 1])
    else:
        h2omb[act] = np.array(sim.unrst["RES_OIL", step_index + 1])
    co2mn[act] = np.abs(co2mb[act]) / porva
    h2omn[act] = np.abs(h2omb[act]) / porva


def write_dense_performance_spatial(
    cfg: DataConfig,
    refg: dict,
    cvol_refg: NDArray,
    arat_refg: NDArray,
    refxcent: NDArray,
    refycent: NDArray,
    refzcent: NDArray,
    i: int,
) -> str:
    """Write one performance-spatial benchmark CSV file.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    refg : dict
        Performance quantities on the reporting grid.
    cvol_refg : NDArray
        Cell-volume metric on the reporting grid.
    arat_refg : NDArray
        Aspect-ratio metric on the reporting grid.
    refxcent : NDArray
        Reporting-grid centers along x.
    refycent : NDArray
        Reporting-grid centers along y.
    refzcent : NDArray
        Reporting-grid centers along z.
    i : int
        Selected record index.

    Returns
    -------
    str
        Generated filename or formatted text.
    """
    if cfg.case == "spe11a":
        name_t = f"{round(cfg.denset[i]/3600)}h"
    else:
        name_t = f"{round(cfg.denset[i]/SECONDS_IN_YEAR)}y"
    nx, ny, nz = cfg.nxyz
    co2mn = refg["co2mn"]
    h2omn = refg["h2omn"]
    co2mb = refg["co2mb"]
    h2omb = refg["h2omb"]
    file_name = f"{cfg.case}_performance_spatial_map_{name_t}.csv"
    path = f"{cfg.where}/{file_name}"
    with open(path, "w", encoding="utf8") as file:
        if cfg.case != "spe11c":
            file.write(
                "# x [m], z [m], cvol [m^3], arat [-], CO2 max_norm_res [-], "
                "H2O max_norm_res [-], CO2 mb_error [-], H2O mb_error [-], post_est [-]"
            )
        else:
            file.write(
                "# x [m], y [m], z [m], cvol [m^3], arat [-], CO2 max_norm_res [-], "
                "H2O max_norm_res [-], CO2 mb_error [-], H2O mb_error [-], post_est [-]"
            )
        for idz, zcord in enumerate(refzcent):
            idxy = 0
            basez = -nx * ny * (nz - idz)
            for ycord in refycent:
                for xcord in refxcent:
                    idc = basez + idxy
                    if np.isnan(cvol_refg[idc]):
                        if cfg.case != "spe11c":
                            file.write(
                                f"\n{xcord:.3e}, {zcord:.3e}, n/a, n/a, n/a, n/a, n/a, n/a, n/a"
                            )
                        else:
                            file.write(
                                f"\n{xcord:.3e}, {ycord:.3e}, {zcord:.3e}, n/a, n/a, n/a, n/a, "
                                "n/a, n/a, n/a"
                            )
                    else:
                        if cfg.case != "spe11c":
                            file.write(
                                f"\n{xcord:.3e}, {zcord:.3e}, {cvol_refg[idc]:.3e}, "
                                f"{arat_refg[idc]:.3e}, {co2mn[idc]:.3e}, {h2omn[idc]:.3e}, "
                                f"{co2mb[idc]:.3e}, {h2omb[idc]:.3e}, n/a"
                            )
                        else:
                            file.write(
                                f"\n{xcord:.3e}, {ycord:.3e}, {zcord:.3e}, "
                                f"{cvol_refg[idc]:.3e}, {arat_refg[idc]:.3e}, "
                                f"{co2mn[idc]:.3e}, {h2omn[idc]:.3e}, "
                                f"{co2mb[idc]:.3e}, {h2omb[idc]:.3e}, n/a"
                            )
                    idxy += 1
    return file_name


def generate_arrays(
    cfg: DataConfig,
    sim: SimulationData,
    names: list,
    restart_index: int,
    actindr: NDArray,
) -> dict:
    """Build simulation and reporting arrays for dense quantities.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    names : list
        Quantity names to initialize or populate.
    restart_index : int
        Restart report-step index.
    actindr : NDArray
        Inactive reporting-cell indices.

    Returns
    -------
    dict[str, NDArray]
        Dense quantities in simulation-cell and reporting-grid order.
    """
    arrays = {}
    act = sim.actind
    porva = sim.porva
    for name in names[:-1]:
        arr = np.zeros(sim.nocellst)
        if cfg.case == "spe11a" or (cfg.lower and not sim.cornpoint):
            arr[:] = np.nan
        arrays[f"{name}_array"] = arr
        refg = np.zeros(cfg.nocellsrepgrid)
        if actindr.size > 0:
            refg[actindr] = np.nan
        arrays[f"{name}_refg"] = refg
    tco2_array = np.zeros(sim.nocellst)
    tco2_refg = np.zeros(cfg.nocellsrepgrid)
    sgas = np.abs(np.array(sim.unrst["SGAS", restart_index]))
    rhog = np.array(sim.unrst["GAS_DEN", restart_index])
    pres = np.array(sim.unrst["PRESSURE", restart_index]) - np.array(
        sim.unrst["PCGW", restart_index]
    )
    rhow = np.array(sim.unrst["WAT_DEN", restart_index])
    mask_g = sgas > SGAS_THR
    if not sim.immiscible:
        rss = np.array(sim.unrst["RSW", restart_index])
        rvv = (
            np.array(sim.unrst["RVW", restart_index])
            if sim.unrst.count("RVW", restart_index)
            else 0.0 * rss
        )
        if not sim.isothermal:
            arrays["temp_array"][act] = np.array(sim.unrst["TEMP", restart_index])
        xco2 = rss / (rss + WAT_DEN_REF / GAS_DEN_REF)
        xh2o = rvv / (rvv + GAS_DEN_REF / WAT_DEN_REF)
        co2_g = (1 - xh2o) * sgas * rhog * porva
        co2_d = xco2 * (1 - sgas) * rhow * porva
    else:
        xco2 = 0.0 * sgas
        xh2o = 0.0 * sgas
        co2_g = sgas * rhog * porva
        co2_d = 0.0
    arrays["pressure_array"][act] = 1e5 * pres
    arrays["sgas_array"][act] = sgas * mask_g
    arrays["gden_array"][act] = rhog * mask_g
    arrays["wden_array"][act] = rhow
    arrays["xco2_array"][act] = xco2
    arrays["xh2o_array"][act] = xh2o * mask_g
    tco2_array[act] = co2_d + co2_g
    arrays["tco2_array"] = tco2_array
    arrays["tco2_refg"] = tco2_refg
    if cfg.lower and sim.cornpoint:
        pad = np.full(sim.simdim[0] * sim.simdim[1], np.nan)
        for key, value in arrays.items():
            if key.endswith("_array") and key != "tco2_array":
                arrays[key] = np.insert(value, 0, pad)
    return arrays


def map_dense_arrays_to_report_grid(
    sim: SimulationData,
    mapping: tuple[list[list[list[int | float]]], NDArray],
    arrays: dict,
) -> None:
    """Map intensive and extensive dense quantities to the reporting grid.

    Parameters
    ----------
    sim : SimulationData
        Loaded simulation readers and metadata.
    mapping : tuple[list[list[list[int | float]]], NDArray]
        Simulation-to-report mapping and representative cells.
    arrays : dict
        Simulation-grid quantity arrays.
    """
    cell_ind, cell_cent = mapping
    tco2_arr = arrays["tco2_array"]
    tco2_refg = arrays["tco2_refg"]
    for cell in sim.actind:
        tval = tco2_arr[cell]
        for tgt, w in cell_ind[cell]:
            tco2_refg[tgt] += tval * w
    for rep, cent in enumerate(cell_cent):
        cell = int(cent)
        for key in arrays:
            if key.endswith("_array") and not key.startswith("tco2"):
                arrays[key.replace("_array", "_refg")][rep] = arrays[key][cell]


def get_header(cfg: DataConfig, sim: SimulationData, i: int) -> tuple[str, list[str]]:
    """Build the dense CSV time label and column header.

    Parameters
    ----------
    cfg : DataConfig
        Initialized runtime configuration.
    sim : SimulationData
        Loaded simulation readers and metadata.
    i : int
        Selected record index.

    Returns
    -------
    name_t : str
        Time label used in the dense spatial filename.
    text : list[str]
        CSV header lines for the selected SPE11 case.
    """
    if cfg.case == "spe11a":
        name_t = f"{round(cfg.denset[i]/3600)}h"
        text = [
            "# x [m], z [m], pressure [Pa], gas saturation [-], "
            + "mass fraction of CO2 in liquid [-], mass fraction of H20 in vapor [-], "
            + "phase mass density gas [kg/m3], phase mass density water [kg/m3], "
            + "total mass CO2 [kg]"
            + (", temperature [C]" if not sim.isothermal else "")
        ]
    elif cfg.case == "spe11b":
        name_t = f"{round(cfg.denset[i]/SECONDS_IN_YEAR)}y"
        text = [
            "# x [m], z [m], pressure [Pa], gas saturation [-], "
            + "mass fraction of CO2 in liquid [-], mass fraction of H20 in vapor [-], "
            + "phase mass density gas [kg/m3], phase mass density water [kg/m3], "
            + "total mass CO2 [kg], temperature [C]"
        ]
    else:
        name_t = f"{round(cfg.denset[i]/SECONDS_IN_YEAR)}y"
        text = [
            "# x [m], y [m], z [m], pressure [Pa], gas saturation [-], "
            + "mass fraction of CO2 in liquid [-], mass fraction of H20 in vapor [-], "
            + "phase mass density gas [kg/m3], phase mass density water [kg/m3], "
            + "total mass CO2 [kg], temperature [C]"
        ]
    return name_t, text


def main(argv: list[str] | None = None) -> None:
    """Run benchmark-data generation from the command line.

    The function parses standalone data-processing arguments and generates the
    requested sparse, dense, performance, or performance-spatial CSV files from
    existing OPM Flow results.

    Parameters
    ----------
    argv : list[str], optional
        Arguments to parse instead of ``sys.argv[1:]``. This is primarily used
        by tests and programmatic callers.

    """
    parser = argparse.ArgumentParser(description="Main script to process the data")
    parser.add_argument("-p", "--path", default="output", help="Output folder")
    parser.add_argument("-d", "--deck", default="spe11b", help="Simulated case")
    parser.add_argument("-r", "--resolution", default="10,1,5", help="x,y,z elements")
    parser.add_argument(
        "-t",
        "--time",
        default="24",
        help="Dense output time(s): spe11a [h], spe11b/c [y]",
    )
    parser.add_argument(
        "-w",
        "--write",
        default="0.1",
        help="Sparse/performance interval: spe11a [h], spe11b/c [y]",
    )
    parser.add_argument(
        "-g",
        "--generate",
        default="sparse",
        help="dense, sparse, performance, performance-spatial or combinations",
    )
    parser.add_argument(
        "-n", "--neighbourhood", default="", help="Region: 'lower' or all"
    )
    parser.add_argument("-f", "--subfolders", default=1, help="Create subfolders")
    cmdargs = vars(parser.parse_args(argv))
    generated_files = generate_data(cmdargs)
    pyopmspe11_success("", cmdargs["path"], generated_files)


if __name__ == "__main__":
    main(sys.argv[1:])
