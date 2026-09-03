# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT
# pylint: disable=R0902,R0912,R0801,R0913,R0914,R0915,R0917

"""Create benchmark figures from pyopmspe11 CSV output.

The module reads sparse, dense, and performance data, configures shared plotting
styles, creates individual case figures, and compares compatible results from
multiple folders.
"""

import argparse
import math as mt
import os
import shutil
import subprocess
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from io import StringIO

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from alive_progress import alive_bar
from matplotlib import colors, ticker
from mpl_toolkits.axes_grid1 import make_axes_locatable
from numpy.typing import NDArray

from pyopmspe11.utils.terminal import (
    pyopmspe11_info,
    pyopmspe11_success,
    pyopmspe11_tip,
)

SECONDS_IN_YEAR = 31536000.0

font = {"family": "normal", "weight": "normal", "size": 20}
matplotlib.rc("font", **font)


@dataclass(frozen=True)
class PlotCase:
    """Case-dependent settings used by all plotting functions.

    Attributes
    ----------
    case
        SPE11 case identifier.
    tlabel
        Short time-unit label used in titles and filenames.
    dims
        Number of coordinate columns in spatial CSV files.
    tscale
        Factor converting simulation seconds to the displayed time unit.
    lower
        Whether plots represent only the lower neighbourhood.
    """

    case: str
    tlabel: str
    dims: int
    tscale: float
    lower: bool


@dataclass(frozen=True)
class PlotConfig:
    """Folders, output settings, and styles shared by one plotting run.

    Attributes
    ----------
    folders
        Case directories whose generated CSV files are plotted.
    generate
        Requested combination of plot types.
    compare
        SPE11 case selected for a multi-folder comparison.
    where
        Directory in which figures are saved.
    dataf
        Optional data subdirectory relative to each case folder.
    colors, linestyles
        Style sequences used to distinguish cases and quantities.
    props
        Matplotlib properties used for folder labels.
    """

    folders: list
    generate: str
    compare: str
    where: str
    dataf: str
    colors: list
    linestyles: list
    props: dict


@dataclass(frozen=True)
class PlotGrid:
    """Coordinates and display settings for dense spatial plots.

    Attributes
    ----------
    times
        Spatial output times selected for plotting.
    xmsh, zmsh
        Meshgrid coordinates passed to ``pcolormesh``.
    xmx, ymy, zmz
        Reporting-grid vertices along x, y, and z.
    kinds
        Dense data variants to plot.
    cmaps
        Colormaps assigned to dense quantities.
    dims
        Number of coordinate columns in the spatial CSV files.
    """

    times: list
    xmsh: np.ndarray
    zmsh: np.ndarray
    xmx: np.ndarray
    ymy: np.ndarray
    zmz: np.ndarray
    kinds: list
    cmaps: list
    dims: int


def configure_matplotlib() -> None:
    """Configure Matplotlib defaults for benchmark figures."""
    latex_available = shutil.which("latex") is not None
    if not latex_available:
        pyopmspe11_tip("LaTeX is recommended for the figures.")
    plt.rcParams.update(
        {
            "text.usetex": latex_available,
            "font.family": "monospace",
            "legend.columnspacing": 0.9,
            "legend.handlelength": 3.5,
            "legend.fontsize": 15,
            "lines.linewidth": 4,
            "axes.titlesize": 20,
            "axes.grid": True,
            "figure.figsize": (10, 5),
        }
    )


def read_csv(path: str) -> NDArray:
    """Read a benchmark CSV file into a numeric array.

    Parameters
    ----------
    path : str
        Input or output path.

    Returns
    -------
    NDArray
        Calculated numeric values.
    """
    return np.genfromtxt(path, delimiter=",", skip_header=1)


def load_time_series(folder: str, case: str) -> tuple[NDArray | None, bool]:
    """Load a sparse time-series CSV file when available.

    Parameters
    ----------
    folder : str
        Case output directory.
    case : str
        SPE11 case identifier.

    Returns
    -------
    csv : NDArray or None
        Loaded sparse time-series values, or ``None`` when the file is absent.
    found : bool
        Whether a matching time-series file was found.
    """
    path = f"{folder}/data/{case}_time_series.csv"
    if not os.path.isfile(path):
        path = f"{folder}/{case}_time_series.csv"
    if not os.path.isfile(path):
        return None, False
    return read_csv(path), True


def load_performance_series(
    folder: str, case: str, kind: str
) -> tuple[NDArray | None, bool]:
    """Load a performance time-series CSV file when available.

    Parameters
    ----------
    folder : str
        Case output directory.
    case : str
        SPE11 case identifier.
    kind : str
        Regular or detailed data variant.

    Returns
    -------
    csv : NDArray or None
        Loaded performance values, or ``None`` when the file is absent.
    found : bool
        Whether a matching performance file was found.
    """
    path = f"{folder}/data/{case}_performance_time_series{kind}.csv"
    if not os.path.isfile(path):
        path = f"{folder}/{case}_performance_time_series{kind}.csv"
    if not os.path.isfile(path):
        return None, True
    return read_csv(path), True


def load_spatial_map(
    folder: str, dataf: str, case: str, kind: str, time: str, tlabel: str
) -> NDArray:
    """Load one dense or performance-spatial CSV map.

    Parameters
    ----------
    folder : str
        Case output directory.
    dataf : str
        Optional data subdirectory.
    case : str
        SPE11 case identifier.
    kind : str
        Regular or detailed data variant.
    time : str
        Case-dependent time conversion factor.
    tlabel : str
        Short time-unit label.

    Returns
    -------
    NDArray
        Calculated numeric values.
    """
    return read_csv(f"{folder}{dataf}/{case}{kind}_spatial_map_{time}{tlabel}.csv")


def format_performance_label(csv: NDArray, index: int, folder: str) -> str:
    """Format the aggregate metric shown in a performance legend.

    Parameters
    ----------
    csv : NDArray
        Loaded numeric CSV data.
    index : int
        Metric index.
    folder : str
        Case output directory.

    Returns
    -------
    str
        Generated filename or formatted text.
    """
    stats = [
        f"sum={np.sum(csv[:,1]):.3e}",
        f"sum={np.sum(csv[:,2]):.3e}",
        f"max={np.max(csv[:,3]):.3e}",
        f"max={csv[-1,4]:.3e}",
        f"sum={np.sum(csv[:,5]):.3e}",
        f"sum={np.sum(csv[:,6]):.3e}",
        f"sum={np.sum(csv[:,7]):.3e}",
        f"sum={np.sum(csv[:,8]):.3e}",
        f"sum={np.sum(csv[:,9]):.3e}",
    ]
    return f"{stats[index]} ({folder})"


def build_plot_grid(
    folder: str, dataf: str, tlabel: str, dims: int, time
) -> tuple[list, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Build plotting coordinates and select spatial output times.

    Parameters
    ----------
    folder : str
        Case output directory.
    dataf : str
        Optional data subdirectory.
    tlabel : str
        Short time-unit label.
    dims : int
        Number of coordinate columns.
    time : float
        Case-dependent time conversion factor.

    Returns
    -------
    times : list[int]
        Spatial output times selected for plotting.
    xmsh, zmsh : NDArray
        Meshgrid coordinates used by ``pcolormesh``.
    xmx, ymy, zmz : NDArray
        Reporting-grid vertices along x, y, and z.
    """
    files = [f for f in os.listdir(f"{folder}{dataf}") if f.endswith(f"{tlabel}.csv")]
    tmp = np.array([int(f[19:-5]) for f in files if len(f) < 30])
    if tmp.size == 0:
        tmp = np.array([int(f[31:-5]) for f in files])
    times = list(tmp[np.argsort(tmp)])
    if time.size == 1:
        if time > 0:
            times = list(range(0, times[-1] + 1, time))
        else:
            times = [time]
    else:
        times = list(time)
    csv = read_csv(f"{folder}{dataf}/{files[0]}")
    length = csv[-1][0] + csv[0][0]
    width = csv[-1][dims - 2] + csv[0][dims - 2]
    height = csv[-1][dims - 1] + csv[0][dims - 1]
    xmx = np.linspace(0, length, round(length / (2.0 * csv[0][0])) + 1)
    ymy = np.linspace(0, width, round(width / (2.0 * csv[0][dims - 2])) + 1)
    zmz = np.linspace(0, height, round(height / (2.0 * csv[0][dims - 1])) + 1)
    xmsh, zmsh = np.meshgrid(xmx, zmz[::-1])
    return times, xmsh, zmsh, xmx, ymy, zmz


def plot_performance(case_cfg: PlotCase, run_cfg: PlotConfig) -> list[str]:
    """Create regular and detailed performance figures.

    Parameters
    ----------
    case_cfg : PlotCase
        Case-dependent plotting settings.
    run_cfg : PlotConfig
        Folders and styles for the plotting run.

    Returns
    -------
    list[str]
        Names of the generated regular and detailed performance figures.
    """
    files: list[str] = []
    for kind in ["", "_detailed"]:
        fig = plt.figure(figsize=(40, 75))
        plots = [
            "tstep",
            "fsteps",
            "mass",
            "dof",
            "nliter",
            "nres",
            "liniter",
            "runtime",
            "tlinsol",
        ]
        ylabels = ["s", "\\#", "kg", "\\#", "\\#", "\\#", "\\#", "s", "s"]
        for i, (plot, ylabel) in enumerate(zip(plots, ylabels)):
            axis = fig.add_subplot(9, 5, i + 1)
            for folder_index, folder in enumerate(run_cfg.folders):
                csv, has_performance_series = load_performance_series(
                    folder, case_cfg.case, kind
                )
                if not has_performance_series:
                    return files
                assert csv is not None
                if len(csv.flatten()) < 12:
                    csv = np.array([csv])
                times = csv[:, 0] / case_cfg.tscale
                label = format_performance_label(csv, i, folder.split("/")[-1])
                axis.step(
                    times,
                    csv[:, i + 1],
                    lw=2,
                    color=run_cfg.colors[folder_index],
                    label=label,
                )
            axis.set_title(f"{plot}, {case_cfg.case}")
            axis.set_ylabel(ylabel)
            axis.set_xlabel(f"Time [{case_cfg.tlabel}]")
            axis.legend()
        fig.savefig(
            f"{run_cfg.where}/{case_cfg.case}_performance{kind}.png",
            bbox_inches="tight",
        )
        plt.close(fig)
        files.append(f"{case_cfg.case}_performance{kind}.png")
    return files


def plot_sparse_data(case_cfg: PlotCase, run_cfg: PlotConfig) -> str:
    """Create the sparse benchmark figure.

    Parameters
    ----------
    case_cfg : PlotCase
        Case-dependent plotting settings.
    run_cfg : PlotConfig
        Folders and styles for the plotting run.

    Returns
    -------
    str
        Generated filename or formatted text.
    """
    fig = plt.figure(figsize=(25, 40))
    plots = ["sensors", "boxA", "boxB", "boxC", "facie 1"]
    ylabels = ["Presure [Pa]", "Mass [kg]", "Mass [kg]", "Length [m]", "Mass [kg]"]
    labels = [
        ["p1", "p2"],
        ["mobA", "immA", "dissA", "sealA"],
        ["mobB", "immB", "dissB", "sealB"],
        ["MC"],
        ["sealTot"],
    ]
    nfigs = 5
    if case_cfg.case != "spe11a":
        plots.append("boundaries")
        ylabels.append("Mass [kg]")
        labels.append(["boundTot"])
        nfigs += 1
    for k, (plot, ylabel) in enumerate(zip(plots, ylabels)):
        axis = fig.add_subplot(nfigs, 3, k + 1)
        for folder_index, folder in enumerate(run_cfg.folders):
            column = sum(len(labels[i]) for i in range(k)) + 1
            axis.text(
                0.7,
                0.15 + folder_index * 0.05,
                run_cfg.folders[-1 - folder_index].split("/")[-1],
                transform=axis.transAxes,
                verticalalignment="top",
                bbox=run_cfg.props,
                color=run_cfg.colors[len(run_cfg.folders) - folder_index - 1],
            )
            csv, has_time_series = load_time_series(folder, case_cfg.case)
            if not has_time_series:
                return ""
            assert csv is not None
            times = csv[:, 0] / case_cfg.tscale
            for j, label in enumerate(labels[k]):
                if folder_index == 0:
                    axis.plot(
                        times,
                        csv[:, column],
                        label=label,
                        color="k",
                        linestyle=run_cfg.linestyles[-1 + j],
                    )
                if label == "MC":
                    axis.plot(
                        times,
                        csv[:, column],
                        color=run_cfg.colors[folder_index],
                        linestyle=run_cfg.linestyles[-1 + j + folder_index],
                    )
                else:
                    axis.plot(
                        times,
                        csv[:, column],
                        color=run_cfg.colors[folder_index],
                        linestyle=run_cfg.linestyles[-1 + j],
                    )
                column += 1
        axis.set_title(f"{plot}, {case_cfg.case}")
        axis.set_ylabel(ylabel)
        axis.set_xlabel(f"Time [{case_cfg.tlabel}]")
        axis.legend()
    fig.savefig(f"{run_cfg.where}/{case_cfg.case}_sparse_data.png", bbox_inches="tight")
    plt.close(fig)
    return f"{case_cfg.case}_sparse_data.png"


def plot_dense_data(
    case_cfg: PlotCase, run_cfg: PlotConfig, grid: PlotGrid
) -> list[str]:
    """Create dense spatial-map figures.

    Parameters
    ----------
    case_cfg : PlotCase
        Case-dependent plotting settings.
    run_cfg : PlotConfig
        Folders and styles for the plotting run.
    grid : PlotGrid
        Spatial coordinates and plot settings.

    Returns
    -------
    list[str]
        Names of the generated dense spatial-map figures.
    """
    files: list[str] = []
    for kind in grid.kinds:
        if kind == "":
            quantities = [
                "pressure",
                "sgas",
                "xco2",
                "xh2o",
                "gden",
                "wden",
                "tco2",
                "temp",
            ]
            units = [
                "[Pa]",
                "[-]",
                "[-]",
                "[-]",
                r"[kg/m$^3$]",
                r"[kg/m$^3$]",
                "[kg]",
                "C",
            ]
            allplots = [-1] * 8
        else:
            quantities = [
                "cvol",
                "arat",
                "co2_max_norm_res",
                "h2o_max_norm_res",
                "co2_mb_error",
                "h2o_mb_error",
            ]
            units = [r"[m$^3$]", "[-]", "[-]", "[-]", "[-]", "[-]"]
            allplots = [0, 0, -1, -1, -1, -1]
        nplots = len(quantities)
        csvs = [
            load_spatial_map(
                run_cfg.folders[0],
                run_cfg.dataf,
                case_cfg.case,
                kind,
                t,
                case_cfg.tlabel,
            )
            for t in grid.times
        ]
        show_progress = sys.stdout.isatty()
        if show_progress:
            bar_ctx = alive_bar(nplots, bar="fish")
        else:
            bar_ctx = nullcontext()
        pyopmspe11_info(f"processing dense{kind} data")
        with bar_ctx as bar_animation:
            for qi, quantity in enumerate(quantities):
                if show_progress:
                    bar_animation()  # pylint: disable=not-callable
                if qi == csvs[0].shape[1] - grid.dims:
                    break
                first = csvs[0][:, grid.dims + qi]
                if np.isnan(first).all():
                    continue
                minc, maxc = np.nanmin(first), np.nanmax(first)
                ptimes = grid.times[: allplots[qi]] + [grid.times[-1]]
                if case_cfg.case != "spe11a":
                    fig = plt.figure(
                        figsize=(100 if case_cfg.lower else 50, 3 * len(ptimes))
                    )
                else:
                    fig = plt.figure(figsize=(45, 6.5 * len(ptimes)), dpi=80)
                plots = []
                mins = []
                maxs = []
                sums = []
                for ti, time in enumerate(ptimes):
                    values = csvs[ti][:, grid.dims + qi]
                    mins.append(np.nanmin(values))
                    maxs.append(np.nanmax(values))
                    if quantity == "tco2":
                        sums.append(np.sum(values[values >= 0]))
                    minc = min(minc, mins[-1])
                    maxc = max(maxc, maxs[-1])
                    nx = len(grid.xmx) - 1
                    nz = len(grid.zmz) - 1
                    zi = np.arange(nz)
                    if case_cfg.case != "spe11c":
                        idx = zi[:, None] * nx + np.arange(nx)
                        arr = values[idx][::-1]
                    else:
                        ny = len(grid.ymy) - 1
                        mid = mt.floor(ny / 2)
                        idx = (zi[:, None] * ny + mid) * nx + np.arange(nx)
                        arr = values[idx][::-1]
                    plots.append(arr)
                for j, time in enumerate(ptimes):
                    axis = fig.add_subplot(len(ptimes), 3, j + 1)
                    imag = axis.pcolormesh(
                        grid.xmsh,
                        grid.zmsh,
                        plots[j],
                        shading="flat",
                        cmap=(
                            grid.cmaps[qi]
                            if mins != maxs
                            else colors.ListedColormap(["#1319bf"])
                        ),
                    )
                    if quantity == "tco2":
                        title = (
                            f"{time}{case_cfg.tlabel}, {quantity} "
                            f"{units[qi]}(sum={sums[j]:.1E})"
                        )
                    else:
                        prefix = (
                            f"{time}{case_cfg.tlabel}, " if allplots[qi] == -1 else ""
                        )
                        title = (
                            f"{prefix}{quantity} {units[qi]}(min={mins[j]:.1E}, "
                            f"max={maxs[j]:.1E})"
                        )
                    axis.set_title(
                        f"{title}, {case_cfg.case} ({run_cfg.folders[0].split('/')[-1]})"
                    )
                    axis.axis("scaled")
                    axis.xaxis.set_major_locator(ticker.MaxNLocator(14))
                    axis.yaxis.set_major_locator(ticker.MaxNLocator(4))
                    imag.set_clim(minc, maxc)
                    if j % 3 != 0:
                        axis.set_yticks([])
                    if (
                        j
                        < ((len(ptimes) - len(ptimes) % 3) / 3) * 3
                        - (3 - len(ptimes) % 3)
                        or (len(ptimes) % 3 == 1 and j == len(ptimes) - 4)
                        or (len(ptimes) % 3 == 2 and j == len(ptimes) - 5)
                    ):
                        axis.set_xticks([])
                    if (
                        (j + 1) % 3 == 0
                        or len(ptimes) == 1
                        or (len(ptimes) == 2 and j == 1)
                    ):
                        divider = make_axes_locatable(axis)
                        fig.colorbar(
                            imag,
                            cax=divider.append_axes("right", size="5%", pad=0.05),
                            ticks=np.linspace(minc, maxc, 5),
                            format=lambda x, _: f"{x:.2e}",
                        )
                    if case_cfg.lower:
                        axis.set_ylim(
                            (0.0, 0.55) if case_cfg.case == "spe11a" else (0.0, 550.0)
                        )
                fig.savefig(
                    f"{run_cfg.where}/{case_cfg.case}_{quantity}_2dmaps.png",
                    bbox_inches="tight",
                )
                plt.close(fig)
                files.append(f"{case_cfg.case}_{quantity}_2dmaps.png")
    return files


def plot_results(args: dict) -> list[str]:
    """Create all figures requested by the plotting configuration.

    Comparison mode discovers compatible case folders, while normal mode reads data
    from one configured output directory.

    Parameters
    ----------
    args : dict
        Plotting options.

    Returns
    -------
    list[str]
        Names of all figures generated by the selected plotting workflow.
    """
    generated_files: list[str] = []
    configure_matplotlib()
    where = ""
    dataf = ""
    if args["compare"]:
        args["deck"] = args["compare"]
        args["neighbourhood"] = ""
        args["generate"] = "performance_sparse"
        where = "compare/"
        folders = sorted(
            [n for n in os.listdir(".") if os.path.isdir(n) and n != "compare"]
        )
        if not os.path.isdir("compare"):
            subprocess.run(["mkdir", "compare"], check=False)
    else:
        folders = [args["folder"].strip()]
        if int(args["subfolders"]) == 1:
            dataf = "/data"
            where = f"{folders[0]}/figures"
        else:
            where = folders[0]
    if args["deck"] == "spe11a":
        case_cfg = PlotCase(args["deck"], "h", 2, 3600.0, bool(args["neighbourhood"]))
    else:
        case_cfg = PlotCase(
            args["deck"], "y", 2, SECONDS_IN_YEAR, bool(args["neighbourhood"])
        )
    if args["deck"] == "spe11c":
        case_cfg = PlotCase(
            args["deck"], "y", 3, SECONDS_IN_YEAR, bool(args["neighbourhood"])
        )
    run_cfg = PlotConfig(
        folders,
        args["generate"],
        args["compare"],
        where,
        dataf,
        [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
            "r",
            "k",
        ],
        [
            "--",
            (0, (1, 1)),
            "-.",
            (0, (1, 10)),
            (0, (1, 1)),
            (5, (10, 3)),
            (0, (5, 10)),
            (0, (5, 5)),
            (0, (5, 1)),
            (0, (3, 10, 1, 10)),
            (0, (3, 5, 1, 5)),
            (0, (3, 1, 1, 1)),
            (0, (3, 5, 1, 5, 1, 5)),
            (0, (3, 10, 1, 10, 1, 10)),
            (0, (3, 1, 1, 1, 1, 1)),
            (0, ()),
            "-",
        ],
        {"boxstyle": "round", "facecolor": "wheat", "alpha": 0.1},
    )
    if args["generate"] in [
        "all",
        "performance",
        "dense_performance",
        "performance_sparse",
        "dense_performance_sparse",
    ]:
        generated_files.extend(plot_performance(case_cfg, run_cfg))
    if args["generate"] in [
        "all",
        "sparse",
        "dense_sparse",
        "performance_sparse",
        "dense_performance_sparse",
    ]:
        generated_files.append(plot_sparse_data(case_cfg, run_cfg))
    if args["compare"]:
        return generated_files
    plt.rcParams.update({"axes.grid": False})
    if args["generate"] in [
        "all",
        "dense",
        "performance-spatial",
        "dense_performance",
        "dense_sparse",
        "dense_performance-spatial",
        "dense_performance_sparse",
    ]:
        time = np.genfromtxt(StringIO(args["time"]), delimiter=",", dtype=int)
        times, xmsh, zmsh, xmx, ymy, zmz = build_plot_grid(
            run_cfg.folders[0], run_cfg.dataf, case_cfg.tlabel, case_cfg.dims, time
        )
        kinds = (
            ["", "_performance"]
            if args["generate"] in ["all", "dense_performance-spatial"]
            else [""] if args["generate"].startswith("dense") else ["_performance"]
        )
        grid = PlotGrid(
            times,
            xmsh,
            zmsh,
            xmx,
            ymy,
            zmz,
            kinds,
            [
                "seismic",
                "jet",
                "viridis",
                "viridis_r",
                "PuOr",
                "PuOr_r",
                "turbo",
                "coolwarm",
            ],
            case_cfg.dims,
        )
        generated_files.extend(plot_dense_data(case_cfg, run_cfg, grid))
    return generated_files


def main(argv: list[str] | None = None) -> None:
    """Run benchmark plotting from the command line.

    The function parses standalone plotting arguments and creates the requested
    sparse, dense, or performance figures from generated benchmark CSV files.
    It can also compare compatible results from multiple case directories.

    Parameters
    ----------
    argv : list[str], optional
        Arguments to parse instead of ``sys.argv[1:]``. This is primarily used
        by tests and programmatic callers.

    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Main script to plot the results",
    )
    parser.add_argument("-p", "--folder", default="output", type=str.strip)
    parser.add_argument("-c", "--compare", default="", type=str.strip)
    parser.add_argument("-d", "--deck", default="spe11b", type=str.strip)
    parser.add_argument("-g", "--generate", default="sparse", type=str.strip)
    parser.add_argument("-f", "--subfolders", default="1", type=str.strip)
    parser.add_argument("-t", "--time", default="5", type=str.strip)
    parser.add_argument("-n", "--neighbourhood", default="", type=str.strip)
    args = vars(parser.parse_args(argv))
    generated_files = plot_results(args)
    pyopmspe11_success("", args["folder"], generated_files)


if __name__ == "__main__":
    main(sys.argv[1:])
