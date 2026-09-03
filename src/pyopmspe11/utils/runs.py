# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT

"""Coordinate simulation, data-generation, and plotting operations.

The module runs OPM Flow with the generated deck and converts Config values to
the dictionaries accepted by the data and plotting entry points.
"""

import shlex
import subprocess

from pyopmspe11.config.config import Config
from pyopmspe11.visualization.plotting import plot_results


def run_flow(cfg: Config, flowfol: str) -> None:
    """Run OPM Flow for the generated simulation deck.

    The configured Flow command is combined with the output directory and generated
    DATA file before execution.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.
    flowfol : str
        Directory in which OPM Flow writes simulation results.

    Raises
    ------
    subprocess.CalledProcessError
        If an invoked process exits with a nonzero status.
    """
    data_file = f"{cfg.deckfol}/{cfg.fol.split('/')[-1].upper()}.DATA"
    flow_cmd = shlex.split(cfg.flow) + [f"--output-dir={flowfol}", data_file]
    subprocess.run(flow_cmd, check=True)


def generate_plots(cfg: Config) -> list[str]:
    """Generate figures for the configured benchmark outputs.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.

    Returns
    -------
    list[str]
        Names of the generated figure files.
    """
    return plot_results(
        {
            "folder": cfg.fol,
            "compare": "",
            "deck": cfg.spe11,
            "generate": cfg.generate,
            "subfolders": cfg.subfolders,
            "time": cfg.time_data,
            "neighbourhood": "lower" if cfg.lower else "",
        }
    )


def generate_benchmark_data(cfg: Config) -> list[str]:
    """Generate benchmark CSV data for the configured simulation.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.

    Returns
    -------
    list[str]
        Names of the generated benchmark CSV files.
    """
    # Import lazily because visualization.data requires the optional OPM Python
    # bindings. Deck-only workflows, including the supported Windows workflow,
    # must be able to import and run pyopmspe11 without those bindings.
    # pylint: disable=C0415
    from pyopmspe11.visualization.data import generate_data

    # pylint: enable=C0415

    return generate_data(
        {
            "path": cfg.fol,
            "deck": cfg.spe11,
            "resolution": cfg.resolution,
            "generate": cfg.generate,
            "subfolders": cfg.subfolders,
            "write": f"{cfg.dt_data}",
            "time": cfg.time_data,
            "neighbourhood": "lower" if cfg.lower else "",
        }
    )
