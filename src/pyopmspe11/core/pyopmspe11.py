# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT
# pylint: disable=R0912, R0915

"""Command-line entry point and top-level workflow coordination for pyopmspe11.

pyopmspe11 supports four connected workflows for the SPE11 benchmark cases:

* Deck generation creates OPM Flow input from TOML or legacy configuration.
* Simulation execution runs OPM Flow for the generated deck.
* Data processing converts OPM results to sparse, dense, and performance CSVs.
* Plotting creates benchmark figures or comparisons from generated CSV data.

This module parses and validates command-line arguments, builds the shared
configuration, creates output folders, dispatches the selected workflows, and
reports generated files. Geometry, file writing, result processing, and plotting
are implemented in the utility and visualization modules.
"""

import argparse
import os
import subprocess

from pyopmspe11.utils.inputvalues import build_config, check_flow_version
from pyopmspe11.utils.mapproperties import generate_deck_files
from pyopmspe11.utils.runs import generate_benchmark_data, generate_plots, run_flow
from pyopmspe11.utils.terminal import (
    cli_correct_value,
    cli_error_value,
    pyopmspe11_error,
    pyopmspe11_info,
    pyopmspe11_success,
    pyopmspe11_warning,
)
from pyopmspe11.visualization.plotting import plot_results


def main(argv: list[str] | None = None) -> None:
    """Run the pyopmspe11 command-line workflow.

    Parse and validate CLI arguments, initialize the shared configuration, and
    dispatch the selected deck, Flow, data, plotting, or comparison operations.

    Parameters
    ----------
    argv : list[str] | None, optional
        Arguments to parse instead of ``sys.argv[1:]``. This is primarily used by
        tests and programmatic callers.
    """
    args = _parse_arguments(argv)
    _validate_arguments(args)
    current_dir = os.getcwd()

    if args.compare:
        pyopmspe11_info("processing the comparison, please wait...")
        generated_files = plot_results({"compare": args.compare})
        pyopmspe11_success("", f"{current_dir}/compare", generated_files)
        return

    cfg = build_config(args)
    cfg.deckfol = f"{cfg.fol}/deck" if cfg.subfolders == "1" else cfg.fol
    flowfol = f"{cfg.fol}/flow" if cfg.subfolders == "1" else cfg.fol
    plotfol = f"{cfg.fol}/plot" if cfg.subfolders == "1" else cfg.fol
    datafol = f"{cfg.fol}/data" if cfg.subfolders == "1" else cfg.fol
    _create_directory(cfg.fol)
    os.chdir(cfg.fol)

    try:
        if cfg.mode == "all" or "deck" in cfg.mode:
            if cfg.subfolders == "1":
                _create_directory(cfg.deckfol)
            pyopmspe11_info("generating the input files, please wait...")
            generated_files = generate_deck_files(cfg)
            pyopmspe11_success("", cfg.deckfol, sorted(generated_files))

        if cfg.mode == "all" or "flow" in cfg.mode:
            check_flow_version(cfg)
            pyopmspe11_info("running the simulations, please wait...")
            run_flow(cfg, flowfol)
            pyopmspe11_success("simulation results written to ", flowfol, [""])

        if cfg.mode == "all" or "data" in cfg.mode:
            _create_directory(f"{cfg.fol}/data" if cfg.subfolders == "1" else cfg.fol)
            pyopmspe11_info("generating the csv files, please wait...")
            generated_files = generate_benchmark_data(cfg)
            n = len(generated_files)
            if n > 10:
                pyopmspe11_success(f"{n} csv files written to ", datafol, [""])
            else:
                pyopmspe11_success("", datafol, generated_files)

        if cfg.mode == "all" or "plot" in cfg.mode:
            _create_directory(
                f"{cfg.fol}/figures" if cfg.subfolders == "1" else cfg.fol
            )
            pyopmspe11_info("generating png figures, please wait...")
            generated_files = generate_plots(cfg)
            n = len(generated_files)
            if n > 10:
                pyopmspe11_success(f"{n} png figures written to ", plotfol, [""])
            else:
                pyopmspe11_success("", plotfol, generated_files)
    finally:
        os.chdir(current_dir)


def _create_directory(path: str) -> None:
    """Create an output directory when it does not exist.

    Parameters
    ----------
    path : str
        Input or output path.
    """
    if not os.path.exists(path):
        subprocess.run(["mkdir", "-p", path], check=True)


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    """Create the CLI parser and parse pyopmspe11 arguments.

    Parameters
    ----------
    argv : list[str] | None
        Arguments to parse instead of ``sys.argv[1:]``. This is primarily used by
        tests and programmatic callers.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="pyopmspe11, a Python tool for the three SPE11 benchmark"
        " cases provided by the Open Porous Media (OPM) project.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str.strip,
        default="input.toml",
        help="The base name of the input file",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str.strip,
        choices=[
            "deck",
            "flow",
            "data",
            "plot",
            "deck_flow",
            "flow_data",
            "data_plot",
            "deck_flow_data",
            "flow_data_plot",
            "all",
        ],
        default="deck_flow",
        help="Parts of pyopmspe11 to run",
    )
    parser.add_argument(
        "-c",
        "--compare",
        type=str.strip,
        choices=["spe11a", "spe11b", "spe11c", ""],
        default="",
        help="Generate a common plot for the current folders",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str.strip,
        default="output",
        help="The base name of the output folder",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=str.strip,
        default="5",
        help="If one number, time step for the spatial maps (spe11a [h]; spe11b/c "
        "[y]); otherwise, times separated by commas",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=str.strip,
        default="8,1,5",
        help="Number of x, y, and z elements to map the simulation results to the "
        "dense report data",
    )
    parser.add_argument(
        "-g",
        "--generate",
        type=str.strip,
        default="performance_sparse",
        choices=[
            "dense",
            "sparse",
            "performance",
            "performance-spatial",
            "dense_performance",
            "dense_sparse",
            "performance_sparse",
            "dense_performance-spatial",
            "dense_performance_sparse",
            "all",
        ],
        help="Type of data to generate",
    )
    parser.add_argument(
        "-w",
        "--write",
        type=str.strip,
        default="0.1",
        help="Time interval for the sparse and performance data (spe11a [h]; spe11b/c [y])",
    )
    parser.add_argument(
        "-f",
        "--subfolders",
        choices=["0", "1"],
        type=str.strip,
        default="1",
        help="Set to 0 to not create the subfolders deck, flow, data, and figures, i.e., to "
        "write all generated files in the output directory",
    )
    parser.add_argument(
        "-n",
        "--neighbourhood",
        choices=["lower", ""],
        type=str.strip,
        default="",
        help="Region to model (the default '' means the whole system)",
    )
    return parser.parse_args(argv)


def _validate_arguments(cmdargs: argparse.Namespace) -> None:
    """Validate command-line values and incompatible operations.

    Validation covers numeric syntax, benchmark-specific restrictions, workflow
    dependencies, and requested data and plotting modes.

    Parameters
    ----------
    cmdargs : argparse.Namespace
        Parsed data-generation arguments.

    Raises
    ------
    SystemExit
        If an input value is invalid or required input cannot be used.
    """
    input_file = cmdargs.input
    if not input_file:
        pyopmspe11_error(
            f"invalid value {cli_error_value('-i')}, the input file cannot be empty."
        )
    if not input_file.lower().endswith((".toml", ".txt")):
        pyopmspe11_error(
            f"invalid extension {cli_error_value(f'-i {input_file}')}, valid extensions "
            f"are {cli_correct_value('.toml')} or {cli_correct_value('.txt')}."
        )
    if not cmdargs.output:
        pyopmspe11_error(
            f"invalid value {cli_error_value('-o')}, the output folder cannot be empty."
        )
    resolution = cmdargs.resolution
    try:
        resolution_values = [int(value.strip()) for value in resolution.split(",")]
    except ValueError:
        resolution_values = []
    if len(resolution_values) != 3 or any(value <= 0 for value in resolution_values):
        pyopmspe11_error(
            f"invalid value {cli_error_value(f'-r {resolution}')}, expected three positive "
            f"integers separated by commas, {cli_correct_value('e.g., -r 8,1,5')}."
        )
    time = cmdargs.time
    try:
        time_values = [float(value.strip()) for value in time.split(",")]
    except ValueError:
        time_values = []
    if not time_values or any(value < 0 for value in time_values):
        pyopmspe11_error(
            f"invalid value {cli_error_value(f'-t {time}')}, expected non-negative numbers."
        )
    write = cmdargs.write
    try:
        write_value = float(write)
    except ValueError:
        write_value = 0
    if write_value <= 0:
        pyopmspe11_error(
            f"invalid value {cli_error_value(f'-w {write}')}, expected a positive number."
        )
    mode = cmdargs.mode
    has_data_plot = mode == "all" or ("data" in mode or "plot" in mode)
    data_options = {
        "-g": ("generate", "performance_sparse"),
        "-r": ("resolution", "8,1,5"),
        "-t": ("time", "5"),
        "-w": ("write", "0.1"),
    }
    if not has_data_plot:
        invalid_options = [
            option
            for option, (name, default) in data_options.items()
            if getattr(cmdargs, name) != default
        ]
        if invalid_options:
            txt = ", ".join(invalid_options)
            pyopmspe11_error(
                f"invalid value {cli_error_value(f'-m {mode}; {txt}')} "
                "can only be used when the selected mode writes benchmark "
                "data or figures."
            )
    compare = cmdargs.compare
    if compare:
        compare_options = {
            "-i": ("input", "input.toml"),
            "-m": ("mode", "deck_flow"),
            "-o": ("output", "output"),
            "-t": ("time", "5"),
            "-r": ("resolution", "8,1,5"),
            "-g": ("generate", "performance_sparse"),
            "-w": ("write", "0.1"),
            "-f": ("subfolders", "1"),
            "-n": ("neighbourhood", ""),
        }
        invalid_options = [
            option
            for option, (name, default) in compare_options.items()
            if getattr(cmdargs, name) != default
        ]
        if invalid_options:
            pyopmspe11_error(
                f"invalid combination, {cli_error_value('-c')} runs the standalone comparison "
                "workflow and cannot be combined with "
                f"{cli_error_value(', '.join(invalid_options))}."
            )
    if os.name == "nt" and mode != "deck":
        pyopmspe11_warning(
            f"unsupported {cli_error_value(f'-m {mode}')} in Windows; only"
            f"{cli_correct_value('-m deck')} is supported. The execution "
            f"of pyopmspe11 will continue using {cli_correct_value('-m deck')}."
        )
