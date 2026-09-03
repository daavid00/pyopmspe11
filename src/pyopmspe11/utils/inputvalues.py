# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT
# pylint: disable=R0912,R0913,R0914,R0915,R0917,C0302

"""Read, validate, and initialize pyopmspe11 configuration values.

The module loads TOML or legacy text input, validates types and case-dependent
requirements, converts physical units, and derives grid dimensions, benchmark
regions, sensor locations, and other runtime settings stored in Config.
"""

import argparse
import ast
import csv
import os
import shlex
import subprocess
import tomllib
from io import StringIO
from typing import Any

import numpy as np

from pyopmspe11.config.config import Config
from pyopmspe11.utils.terminal import (
    cli_correct_value,
    cli_error_value,
    cli_warning_value,
    pyopmspe11_error,
    pyopmspe11_warning,
)


def build_config(cli: argparse.Namespace) -> Config:
    """Build the shared runtime configuration.

    Read the selected TOML or legacy text file, merge command-line selections,
    validate values, and derive case-dependent settings.

    Parameters
    ----------
    cli : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    Config
        Initialized runtime configuration.

    Raises
    ------
    SystemExit
        If an input value is invalid or required input cannot be used.
    """
    msg = (
        "\nAfter the pyopmspe11 2025.04 release, column 3 for the maximum solver time "
        + "step in the injection has been moved to the end of the column, including the "
        + "items for the TUNING keyword, which gives more control when setting "
        + "the simulations. Please see the configuration files in the examples and "
        + "online documentation, and update your configuration file accordingly.\n"
    )
    if cli.input.lower().endswith(".toml"):
        with open(cli.input, "rb") as file:
            cfg_file = tomllib.load(file)
        cfg_file = _validate_toml(cfg_file)
    else:
        with open(cli.input, "r", encoding="utf8") as file:
            lines = list(csv.reader(file, delimiter="#"))
        cfg_file = _parse_legacy_config(lines)
    cfg = Config(
        fol=os.path.abspath(cli.output),
        generate=cli.generate,
        mode=cli.mode,
        resolution=cli.resolution,
        time_data=cli.time,
        dt_data=float(cli.write),
        lower=cli.neighbourhood,
        subfolders=cli.subfolders,
        **cfg_file,
    )
    time = _set_case_properties(cfg)
    _finalize_config(cfg, time, msg)
    for value in cfg.flow.split():
        if value.lower() in {
            "--enable-tuning=true",
            "--enable-tuning=1",
        }:
            cfg.tuning = True
            break

    return cfg


def _parse_legacy_config(lines: list) -> dict:
    """Parse the legacy text configuration format.

    Parameters
    ----------
    lines : list
        Rows read from a legacy configuration file.

    Returns
    -------
    dict[str, Any]
        Configuration values parsed from the legacy text input.
    """
    dic: dict[str, Any] = {"flow": str(lines[1])[2:-2]}
    row = lines[4][0].strip().split()
    dic["spe11"] = row[0]
    dic["version"] = row[1]
    row = lines[5][0].strip().split()
    dic["model"] = row[0]
    dic["grid"] = lines[6][0].strip()
    split7 = lines[7][0].strip().split()
    dic["dims"] = [float(split7[0]), float(split7[1]), float(split7[2])]
    dic["x_n"] = np.genfromtxt(StringIO(lines[8][0]), delimiter=",", dtype=int)
    dic["y_n"] = np.genfromtxt(StringIO(lines[9][0]), delimiter=",", dtype=int)
    dic["z_n"] = np.genfromtxt(StringIO(lines[10][0]), delimiter=",", dtype=int)
    for key in ["x_n", "y_n", "z_n"]:
        if np.size(dic[key]) == 1:
            dic[key] = [int(dic[key])]
    row = lines[11][0].strip().split()
    dic["temperature"] = [float(row[0]), float(row[1])]
    row = lines[12][0].strip().split()
    dic["datum"] = float(row[0])
    dic["pressure"] = float(row[1])
    dic["kzMult"] = float(row[2])
    row = lines[13][0].strip().split()
    dic["diffusion"] = [float(row[0]), float(row[1])]
    row = lines[14][0].strip().split()
    dic["rockExtra"] = [float(row[0]), float(row[1])]
    row = lines[15][0].strip().split()
    dic["spe11aBC"] = float(row[0])
    dic["pvAdded"] = float(row[1])
    dic["widthBuffer"] = float(row[2])
    row = lines[16][0].strip().split()
    dic["elevation"] = float(row[0])
    dic["backElevation"] = float(row[1])
    idx = 19
    dic["krw"] = str(lines[idx][0])
    dic["krn"] = str(lines[idx + 1][0])
    dic["pcap"] = str(lines[idx + 2][0])
    dic["s_w"] = str(lines[idx + 3][0])
    idx += 7
    dic["rock"] = [[] for _ in range(7)]
    dic["safu"] = [[] for _ in range(7)]
    dic["dispersion"] = [0.0 for _ in range(7)]
    dic["rockCond"] = [0.0 for _ in range(7)]
    for ind in range(7):
        row = lines[idx + ind][0].strip().split()
        dic["safu"][ind] = [
            float(row[1]),
            float(row[3]),
            float(row[5]),
            float(row[7]),
            int(row[9]),
        ]
    idx += 10
    for ind in range(7):
        row = lines[idx + ind][0].strip().split()
        dic["rock"][ind] = [float(row[1]), float(row[3])]
        dic["dispersion"][ind] = float(row[5])
        if dic["spe11"] != "spe11a":
            dic["rockCond"][ind] = float(row[7])
    idx += 10
    dic["wellCoord"], dic["wellCoordF"], dic["radius"] = [], [], []
    for ind in range(len(lines) - idx):
        if not lines[idx + ind]:
            break
        row = lines[idx + ind][0].strip().split()
        dic["radius"].append(float(row[0]))
        dic["wellCoord"].append([float(row[1]), float(row[2]), float(row[3])])
        if dic["spe11"] == "spe11c":
            dic["wellCoordF"].append([float(row[4]), float(row[5]), float(row[6])])
    idx += len(dic["wellCoord"]) + 3
    injections, tunning = [], []
    for ind in range(len(lines) - idx):
        if not lines[idx + ind]:
            break
        row = lines[idx + ind][0].strip().split()
        entry = [float(row[0]), float(row[1])] + [float(row[j]) for j in range(2, 8)]
        if len(row) > 8:
            parts = " ".join(row[8:]).split("/")
            for val in parts:
                tunning.append(val.strip().replace("'", "").replace('"', ""))
        injections.append(entry + tunning)
    dic["inj"] = injections
    return dic


def _finalize_config(cfg: Config, time: float, msg: str) -> None:
    """Convert units and populate derived configuration values.

    The function derives grid dimensions, transforms depth coordinates, normalizes
    physical properties, and separates optional TUNING values.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.
    time : float
        Case-dependent time conversion factor.
    msg : str
        Error message used for invalid injection settings.
    """
    cfg.nxyz = [sum(cfg.x_n), sum(cfg.y_n), sum(cfg.z_n)]
    cfg.diffusion = [val * 86400 for val in cfg.diffusion]
    for inj in cfg.inj:
        inj[0] *= time
        inj[1] *= time
    dims_z = cfg.dims[2]
    cfg.wellCoord[0][-1] = dims_z - cfg.wellCoord[0][-1]
    cfg.wellCoord[1][-1] = dims_z - cfg.wellCoord[1][-1]
    if cfg.spe11 == "spe11c":
        assert cfg.wellCoordF is not None
        cfg.wellCoordF[0][-1] = dims_z - cfg.wellCoordF[0][-1]
        cfg.wellCoordF[1][-1] = dims_z - cfg.wellCoordF[1][-1]
    if not hasattr(cfg, "rockCond"):
        cfg.rockCond = [0.0] * 7
    if not hasattr(cfg, "rockExtra"):
        cfg.rockExtra = [0.0, 0.0]
    if cfg.rockCond:
        cfg.rockCond = [val * 86400.0 / 1e3 for val in cfg.rockCond]
    for inj in cfg.inj:
        if len(inj) == 9 and not isinstance(inj[-1], str):
            pyopmspe11_error(msg)
        if len(inj) >= 9 and isinstance(inj[-1], str):
            parts = inj[-1].split("/")
            inj[-1] = parts[0].strip()
            for extra in parts[1:]:
                inj.append(extra.strip())


def _set_case_properties(cfg: Config) -> float:
    """Set case-dependent time scales, boxes, and sensor coordinates.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.

    Returns
    -------
    float
        Calculated scalar value.
    """
    mult = 0.995 if cfg.lower and cfg.grid != "corner-point" else 1
    if cfg.spe11 == "spe11a":
        cfg.sensors = [[1.5, 0.005, mult * 0.5], [1.7, 0.005, 1.1]]
        cfg.boxa = [[1.1, 0.0, 0.0], [2.8, 0.01, 0.6]]
        cfg.boxb = [[0.0, 0.0, 0.6], [1.1, 0.01, 1.2]]
        cfg.boxc = [[1.1, 0.0, 0.1], [2.6, 0.01, 0.4]]
        time = 3600.0
    elif cfg.spe11 == "spe11b":
        cfg.sensors = [[4500.0, 0.5, mult * 500], [5100.0, 0.5, 1100.0]]
        cfg.boxa = [[3300.0, 0.0, 0.0], [8300.0, 1.0, 600.0]]
        cfg.boxb = [[100.0, 0.0, 600.0], [3300.0, 1.0, 1200.0]]
        cfg.boxc = [[3300.0, 0.0, 100.0], [7800.0, 1.0, 400.0]]
        time = 31536000.0
    else:
        cfg.maxelevation = 155.04166666666666
        assert cfg.elevation is not None
        assert cfg.backElevation is not None
        correction = cfg.elevation + 0.5 * cfg.backElevation
        cfg.sensors = [
            [4500.0, 2500.0, mult * (655.0 - correction)],
            [5100.0, 2500.0, 1255.0 - correction],
        ]
        cfg.boxa = [[3300.0, 0.0, 0.0], [8300.0, 5000.0, 750.0]]
        cfg.boxb = [[100.0, 0.0, 750.0], [3300.0, 5000.0, 1350.0]]
        cfg.boxc = [[3300.0, 0.0, 250.0], [7800.0, 5000.0, 550.0]]
        time = 31536000.0
    return time


def check_flow_version(cfg: Config) -> None:
    """Check that the configured OPM Flow release is supported.

    Parameters
    ----------
    cfg : Config
        Initialized runtime configuration.

    Raises
    ------
    SystemExit
        If an input value is invalid or required input cannot be used.
    """
    flow_args = shlex.split(cfg.flow)
    result = subprocess.run(
        [flow_args[0], "--version"], capture_output=True, check=False
    )
    flow_version = result.stdout.decode(errors="ignore")[5:].strip()
    flow_release = flow_version.removesuffix("-pre")
    for forbidden in ["2025.04", "2024.10", "2024.04"]:
        if flow_release == forbidden:
            pyopmspe11_error(
                f"You are using Flow {cli_error_value(flow_version)}. Please update to "
                f"{cli_correct_value('at least Flow 2025.10')}, or build Flow from the "
                "master GitHub branches."
            )


def _is_finite_number(value: Any) -> bool:
    """Return whether a value is a finite non-Boolean number.

    Parameters
    ----------
    value : Any
        Value to inspect.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and bool(np.isfinite(value))
    )


def _is_integer(value: Any) -> bool:
    """Return whether a value is a non-Boolean integer.

    Parameters
    ----------
    value : Any
        Value to inspect.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _add_validation_error(errors: list[str], message: str) -> None:
    """Add a TOML validation error.

    Parameters
    ----------
    errors : list[str]
        Validation messages collected so far.
    message : str
        Validation message to append.
    """
    errors.append(message)


def _validate_string(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
) -> bool:
    """Check that a TOML variable is a non-empty string.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if key not in cfg_file:
        return False
    value = cfg_file[key]
    if not isinstance(value, str) or not value.strip():
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has invalid value "
            f"{cli_error_value(str(value))}, expected "
            f"{cli_correct_value('a non-empty string')}.",
        )
        return False
    return True


def _validate_number(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
    minimum: float | None = None,
    strict: bool = False,
) -> bool:
    """Check that a TOML variable is a finite number in the expected range.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.
    minimum : float | None, optional
        Optional lower bound for accepted values.
    strict : bool, optional
        Whether the lower bound is exclusive.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if key not in cfg_file:
        return False
    value = cfg_file[key]
    if not _is_finite_number(value):
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has invalid value "
            f"{cli_error_value(str(value))}, expected "
            f"{cli_correct_value('a finite number')}.",
        )
        return False
    if minimum is None:
        return True
    valid = value > minimum if strict else value >= minimum
    if valid:
        return True
    condition = (
        f"a value greater than {minimum}"
        if strict
        else f"a value greater than or equal to {minimum}"
    )
    _add_validation_error(
        errors,
        f"variable {cli_error_value(key)} has invalid value "
        f"{cli_error_value(str(value))}, expected "
        f"{cli_correct_value(condition)}.",
    )
    return False


def _validate_array(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
    length: int | None = None,
    integer: bool = False,
    minimum: float | None = None,
    strict: bool = False,
    nonempty: bool = False,
) -> bool:
    """Check the type, length, and values of a TOML array.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.
    length : int | None, optional
        Required array length, if specified.
    integer : bool, optional
        Whether every array entry must be an integer.
    minimum : float | None, optional
        Optional lower bound for accepted values.
    strict : bool, optional
        Whether the lower bound is exclusive.
    nonempty : bool, optional
        Whether the array must contain at least one entry.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if key not in cfg_file:
        return False
    value = cfg_file[key]
    if not isinstance(value, list):
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has invalid type "
            f"{cli_error_value(type(value).__name__)}, expected "
            f"{cli_correct_value('an array')}.",
        )
        return False
    if length is not None and len(value) != length:
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has "
            f"{cli_error_value(str(len(value)))} entries, expected "
            f"{cli_correct_value(str(length))}.",
        )
        return False
    if nonempty and not value:
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} must contain "
            f"{cli_correct_value('at least one entry')}.",
        )
        return False
    valid = True
    for index, entry in enumerate(value):
        correct_type = _is_integer(entry) if integer else _is_finite_number(entry)
        expected_type = "an integer" if integer else "a finite number"
        if not correct_type:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'{key}[{index}]')} has invalid value "
                f"{cli_error_value(str(entry))}, expected "
                f"{cli_correct_value(expected_type)}.",
            )
            valid = False
            continue
        if minimum is None:
            continue
        in_range = entry > minimum if strict else entry >= minimum
        if not in_range:
            condition = (
                f"a value greater than {minimum}"
                if strict
                else f"a value greater than or equal to {minimum}"
            )
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'{key}[{index}]')} has invalid value "
                f"{cli_error_value(str(entry))}, expected "
                f"{cli_correct_value(condition)}.",
            )
            valid = False
    return valid


def _validate_matrix(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
    rows: int,
    columns: int,
) -> bool:
    """Check the dimensions and numeric values of a TOML matrix.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.
    rows : int
        Required number of matrix rows.
    columns : int
        Required number of matrix columns.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if key not in cfg_file:
        return False
    value = cfg_file[key]
    if not isinstance(value, list):
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has invalid type "
            f"{cli_error_value(type(value).__name__)}, expected "
            f"{cli_correct_value('an array of arrays')}.",
        )
        return False
    if len(value) != rows:
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} has "
            f"{cli_error_value(str(len(value)))} rows, expected "
            f"{cli_correct_value(str(rows))}.",
        )
        return False
    valid = True
    for row_index, row in enumerate(value):
        if not isinstance(row, list):
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'{key}[{row_index}]')} has invalid "
                f"type {cli_error_value(type(row).__name__)}, expected "
                f"{cli_correct_value('an array')}.",
            )
            valid = False
            continue
        if len(row) != columns:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'{key}[{row_index}]')} has "
                f"{cli_error_value(str(len(row)))} entries, expected "
                f"{cli_correct_value(str(columns))}.",
            )
            valid = False
            continue
        for column_index, entry in enumerate(row):
            if not _is_finite_number(entry):
                _add_validation_error(
                    errors,
                    f"variable "
                    f"{cli_error_value(f'{key}[{row_index}][{column_index}]')} "
                    f"has invalid value {cli_error_value(str(entry))}, expected "
                    f"{cli_correct_value('a finite number')}.",
                )
                valid = False
    return valid


def _validate_coordinates(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
) -> None:
    """Check that well coordinates are inside the model dimensions.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.
    """
    dims = cfg_file.get("dims")
    coordinates = cfg_file.get(key)
    if not isinstance(dims, list) or len(dims) != 3:
        return
    if not all(_is_finite_number(value) and value > 0 for value in dims):
        return
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return
    for well_index, coordinate in enumerate(coordinates):
        if not isinstance(coordinate, list) or len(coordinate) != 3:
            continue
        for axis, value in enumerate(coordinate):
            if not _is_finite_number(value):
                continue
            if value < 0 or value > dims[axis]:
                _add_validation_error(
                    errors,
                    f"variable "
                    f"{cli_error_value(f'{key}[{well_index}][{axis}]')} has "
                    f"invalid value {cli_error_value(str(value))}, expected a "
                    f"value between {cli_correct_value('0')} and "
                    f"{cli_correct_value(str(dims[axis]))}.",
                )


def _validate_expression(
    cfg_file: dict[str, Any],
    key: str,
    errors: list[str],
) -> None:
    """Check that a TOML variable contains a valid Python expression.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    key : str
        Name of the TOML variable.
    errors : list[str]
        Validation messages collected so far.
    """
    if not _validate_string(cfg_file, key, errors):
        return
    try:
        ast.parse(cfg_file[key], mode="eval")
    except SyntaxError as err:
        _add_validation_error(
            errors,
            f"variable {cli_error_value(key)} contains invalid Python expression "
            f"{cli_error_value(cfg_file[key])}: {err.msg}.",
        )


def _validate_saturation_properties(
    cfg_file: dict[str, Any],
    errors: list[str],
) -> None:
    """Check saturation-function properties.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    errors : list[str]
        Validation messages collected so far.
    """
    if not _validate_matrix(cfg_file, "safu", errors, 7, 5):
        return
    for row_index, row in enumerate(cfg_file["safu"]):
        swi, sni, pen, penmax, npoints = row
        if not 0 <= swi <= 1:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'safu[{row_index}][0]')} has invalid "
                f"value {cli_error_value(str(swi))}, expected "
                f"{cli_correct_value('a value between 0 and 1')}.",
            )
        if not 0 <= sni <= 1:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'safu[{row_index}][1]')} has invalid "
                f"value {cli_error_value(str(sni))}, expected "
                f"{cli_correct_value('a value between 0 and 1')}.",
            )
        if swi + sni > 1:
            _add_validation_error(
                errors,
                f"variables {cli_error_value(f'safu[{row_index}][0]')} and "
                f"{cli_error_value(f'safu[{row_index}][1]')} have a combined "
                f"value {cli_error_value(str(swi + sni))}, expected a combined "
                f"value less than or equal to {cli_correct_value('1')}.",
            )
        if pen < 0:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'safu[{row_index}][2]')} has invalid "
                f"value {cli_error_value(str(pen))}, expected "
                f"{cli_correct_value('a non-negative value')}.",
            )
        if penmax < 0:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'safu[{row_index}][3]')} has invalid "
                f"value {cli_error_value(str(penmax))}, expected "
                f"{cli_correct_value('a non-negative value')}.",
            )
        if not _is_integer(npoints) or npoints < 2:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'safu[{row_index}][4]')} has invalid "
                f"value {cli_error_value(str(npoints))}, expected "
                f"{cli_correct_value('an integer greater than or equal to 2')}.",
            )


def _validate_rock_properties(
    cfg_file: dict[str, Any],
    errors: list[str],
) -> None:
    """Check rock properties.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    errors : list[str]
        Validation messages collected so far.
    """
    if not _validate_matrix(cfg_file, "rock", errors, 7, 2):
        return
    for row_index, row in enumerate(cfg_file["rock"]):
        permeability, porosity = row
        if permeability < 0:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'rock[{row_index}][0]')} has invalid "
                f"value {cli_error_value(str(permeability))}, expected "
                f"{cli_correct_value('a non-negative value')}.",
            )
        if not 0 <= porosity <= 1:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'rock[{row_index}][1]')} has invalid "
                f"value {cli_error_value(str(porosity))}, expected "
                f"{cli_correct_value('a value between 0 and 1')}.",
            )


def _validate_injection_schedule(
    cfg_file: dict[str, Any],
    errors: list[str],
) -> bool:
    """Check injection values and return whether TUNING values are defined.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    errors : list[str]
        Validation messages collected so far.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if "inj" not in cfg_file:
        return False
    inj = cfg_file["inj"]
    if not isinstance(inj, list):
        _add_validation_error(
            errors,
            f"variable {cli_error_value('inj')} has invalid type "
            f"{cli_error_value(type(inj).__name__)}, expected "
            f"{cli_correct_value('an array of injection rows')}.",
        )
        return False
    if not inj:
        _add_validation_error(
            errors,
            f"variable {cli_error_value('inj')} must contain "
            f"{cli_correct_value('at least one injection row')}.",
        )
        return False
    tuning_defined = False
    for row_index, row in enumerate(inj):
        if not isinstance(row, list):
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'inj[{row_index}]')} has invalid type "
                f"{cli_error_value(type(row).__name__)}, expected "
                f"{cli_correct_value('an array')}.",
            )
            continue
        if len(row) not in {8, 9}:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'inj[{row_index}]')} has "
                f"{cli_error_value(str(len(row)))} entries, expected "
                f"{cli_correct_value('8 entries, or 9 with TUNING values')}.",
            )
            continue
        for column_index in range(8):
            value = row[column_index]
            variable = f"inj[{row_index}][{column_index}]"
            if column_index in {2, 5}:
                if not _is_integer(value) or value not in {0, 1}:
                    _add_validation_error(
                        errors,
                        f"variable {cli_error_value(variable)} has invalid value "
                        f"{cli_error_value(str(value))}, expected "
                        f"{cli_correct_value('0 or 1')}.",
                    )
            elif not _is_finite_number(value):
                _add_validation_error(
                    errors,
                    f"variable {cli_error_value(variable)} has invalid value "
                    f"{cli_error_value(str(value))}, expected "
                    f"{cli_correct_value('a finite number')}.",
                )
        for column_index in (0, 1):
            value = row[column_index]
            if _is_finite_number(value) and value <= 0:
                _add_validation_error(
                    errors,
                    f"variable "
                    f"{cli_error_value(f'inj[{row_index}][{column_index}]')} has "
                    f"invalid value {cli_error_value(str(value))}, expected "
                    f"{cli_correct_value('a positive value')}.",
                )
        for column_index in (3, 6):
            value = row[column_index]
            if _is_finite_number(value) and value < 0:
                _add_validation_error(
                    errors,
                    f"variable "
                    f"{cli_error_value(f'inj[{row_index}][{column_index}]')} has "
                    f"invalid value {cli_error_value(str(value))}, expected "
                    f"{cli_correct_value('a non-negative injection rate')}.",
                )
        if len(row) == 9:
            tuning_defined = True
            if not isinstance(row[8], str) or not row[8].strip():
                _add_validation_error(
                    errors,
                    f"variable {cli_error_value(f'inj[{row_index}][8]')} has "
                    f"invalid value {cli_error_value(str(row[8]))}, expected "
                    f"{cli_correct_value('a non-empty TUNING string')}.",
                )
    return tuning_defined


def _validate_drsdtcon(
    cfg_file: dict[str, Any],
    errors: list[str],
) -> None:
    """Check convective-dissolution properties.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.
    errors : list[str]
        Validation messages collected so far.
    """
    if "drsdtcon" not in cfg_file:
        return
    drsdtcon = cfg_file["drsdtcon"]
    if not isinstance(drsdtcon, list):
        _add_validation_error(
            errors,
            f"variable {cli_error_value('drsdtcon')} has invalid type "
            f"{cli_error_value(type(drsdtcon).__name__)}, expected "
            f"{cli_correct_value('an array of 7 records')}.",
        )
        return
    if len(drsdtcon) != 7:
        _add_validation_error(
            errors,
            f"variable {cli_error_value('drsdtcon')} has "
            f"{cli_error_value(str(len(drsdtcon)))} rows, expected "
            f"{cli_correct_value('7')}.",
        )
        return
    for row_index, row in enumerate(drsdtcon):
        if not isinstance(row, list):
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'drsdtcon[{row_index}]')} has invalid "
                f"type {cli_error_value(type(row).__name__)}, expected "
                f"{cli_correct_value('an array with 1 or 4 entries')}.",
            )
            continue
        if len(row) not in {1, 4}:
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'drsdtcon[{row_index}]')} has "
                f"{cli_error_value(str(len(row)))} entries, expected "
                f"{cli_correct_value('1 or 4')}.",
            )
            continue
        numeric_columns = 1 if len(row) == 1 else 3
        for column_index in range(numeric_columns):
            value = row[column_index]
            if not _is_finite_number(value):
                _add_validation_error(
                    errors,
                    f"variable "
                    f"{cli_error_value(f'drsdtcon[{row_index}][{column_index}]')} "
                    f"has invalid value {cli_error_value(str(value))}, expected "
                    f"{cli_correct_value('a finite number')}.",
                )
        if len(row) == 4 and (not isinstance(row[3], str) or not row[3].strip()):
            _add_validation_error(
                errors,
                f"variable {cli_error_value(f'drsdtcon[{row_index}][3]')} has "
                f"invalid value {cli_error_value(str(row[3]))}, expected "
                f"{cli_correct_value('a non-empty string')}.",
            )


def _is_tuning_enabled(flow: Any) -> bool:
    """Return whether TUNING is enabled in the Flow command.

    Parameters
    ----------
    flow : Any
        Flow.

    Returns
    -------
    bool
        Whether the requested condition is satisfied.
    """
    if not isinstance(flow, str):
        return False
    return any(
        value.lower() in {"--enable-tuning=true", "--enable-tuning=1"}
        for value in flow.split()
    )


def _validate_toml(cfg_file: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize TOML configuration values.

    The function checks required and case-dependent variables, removes ignored
    values, reports all validation failures together, and returns values suitable
    for Config.

    Parameters
    ----------
    cfg_file : dict[str, Any]
        TOML values to validate or normalize.

    Returns
    -------
    dict[str, Any]
        Validated configuration values.

    Raises
    ------
    SystemExit
        If an input value is invalid or required input cannot be used.
    """
    if not isinstance(cfg_file, dict):
        pyopmspe11_error(
            f"invalid TOML content {cli_error_value(type(cfg_file).__name__)}, "
            f"expected {cli_correct_value('a dictionary of configuration variables')}."
        )
    cfg_file = cfg_file.copy()
    errors: list[str] = []
    required = {
        "flow",
        "spe11",
        "version",
        "model",
        "grid",
        "dims",
        "x_n",
        "y_n",
        "z_n",
        "temperature",
        "datum",
        "pressure",
        "kzMult",
        "diffusion",
        "dispersion",
        "radius",
        "wellCoord",
        "krw",
        "krn",
        "pcap",
        "s_w",
        "safu",
        "rock",
        "inj",
    }
    optional = {
        "spe11aBC",
        "drsdtcon",
        "elevation",
        "backElevation",
        "rockCond",
        "widthBuffer",
        "rockExtra",
        "pvAdded",
        "wellCoordF",
    }
    internal = {
        "fol",
        "generate",
        "mode",
        "resolution",
        "time_data",
        "dt_data",
        "lower",
        "subfolders",
        "maxelevation",
        "cut",
        "nxyz",
        "boxa",
        "boxb",
        "boxc",
        "sensors",
        "sensorijk",
        "wellijk",
        "wellijkf",
        "wellkh",
        "pat",
        "tuning",
        "deckfol",
        "compact_dx",
    }
    configurable = required | optional
    if "co2store" in cfg_file:
        pyopmspe11_warning(
            f"deprecated variable {cli_warning_value('co2store')} will be ignored. "
            f"The execution of pyopmspe11 will continue using "
            f"{cli_correct_value('gaswater')}."
        )
        cfg_file.pop("co2store")
    internal_values = sorted(internal & cfg_file.keys())
    if internal_values:
        formatted = ", ".join(cli_error_value(key) for key in internal_values)
        plural = len(internal_values) != 1
        pyopmspe11_warning(
            f"variable{'s' if plural else ''} {formatted} "
            f"{'are' if plural else 'is'} managed internally and will be ignored."
        )
        for key in internal_values:
            cfg_file.pop(key)
    unknown_values = sorted(cfg_file.keys() - configurable)
    if unknown_values:
        formatted = ", ".join(cli_error_value(key) for key in unknown_values)
        plural = len(unknown_values) != 1
        pyopmspe11_warning(
            f"unknown TOML variable{'s' if plural else ''} {formatted} will be ignored."
        )
        for key in unknown_values:
            cfg_file.pop(key)
    for key in sorted(required - cfg_file.keys()):
        _add_validation_error(
            errors,
            f"missing required TOML variable {cli_error_value(key)}.",
        )
    for key in ("flow", "spe11", "version", "model", "grid"):
        _validate_string(cfg_file, key, errors)
    allowed = {
        "spe11": {"spe11a", "spe11b", "spe11c"},
        "version": {"master", "release"},
        "model": {"immiscible", "isothermal", "convective", "complete"},
        "grid": {"cartesian", "tensor", "corner-point"},
    }
    for key, values in allowed.items():
        value = cfg_file.get(key)
        if isinstance(value, str) and value.strip() and value not in values:
            expected = ", ".join(sorted(values))
            _add_validation_error(
                errors,
                f"variable {cli_error_value(key)} has invalid value "
                f"{cli_error_value(value)}, expected one of "
                f"{cli_correct_value(expected)}.",
            )
    spe11 = cfg_file.get("spe11")
    model = cfg_file.get("model")
    grid = cfg_file.get("grid")
    case_required: set[str] = set()
    ineffective: set[str] = set()
    if spe11 == "spe11a":
        if "spe11aBC" not in cfg_file:
            cfg_file["spe11aBC"] = 0
            pyopmspe11_warning(
                f"variable {cli_warning_value('spe11aBC')} is missing. The execution "
                f"of pyopmspe11 will continue using "
                f"{cli_correct_value('spe11aBC = 0')}, corresponding to the "
                "free-flow boundary condition."
            )
        ineffective = {
            "elevation",
            "backElevation",
            "widthBuffer",
            "pvAdded",
            "wellCoordF",
        }
        if model == "complete":
            case_required = {"rockCond", "rockExtra"}
        else:
            ineffective.update({"rockCond", "rockExtra"})
    elif spe11 == "spe11b":
        case_required = {"rockCond", "widthBuffer", "rockExtra", "pvAdded"}
        ineffective = {"spe11aBC", "elevation", "backElevation", "wellCoordF"}
    elif spe11 == "spe11c":
        case_required = {
            "elevation",
            "backElevation",
            "rockCond",
            "widthBuffer",
            "rockExtra",
            "pvAdded",
            "wellCoordF",
        }
        ineffective = {"spe11aBC"}
    for key in sorted(case_required - cfg_file.keys()):
        _add_validation_error(
            errors,
            f"missing required variable {cli_error_value(key)} for "
            f"{cli_error_value(str(spe11))}.",
        )
    ignored = sorted(ineffective & cfg_file.keys())
    if ignored:
        formatted = ", ".join(cli_error_value(key) for key in ignored)
        plural = len(ignored) != 1
        pyopmspe11_warning(
            f"variable{'s' if plural else ''} {formatted} "
            f"{'are' if plural else 'is'} not effective for "
            f"{cli_warning_value(f'spe11 = {spe11}')} with "
            f"{cli_warning_value(f'model = {model}')} and will be ignored."
        )
        for key in ignored:
            cfg_file.pop(key)
    if model != "convective" and "drsdtcon" in cfg_file:
        pyopmspe11_warning(
            f"variable {cli_warning_value('drsdtcon')} is only effective for "
            f"{cli_correct_value('model = convective')} and will be ignored."
        )
        cfg_file.pop("drsdtcon")
    elif model == "convective" and "drsdtcon" not in cfg_file:
        pyopmspe11_warning(
            f"variable {cli_warning_value('drsdtcon')} is missing. The execution "
            f"of pyopmspe11 will continue using "
            f"{cli_correct_value('the default DRSDTCON values')}."
        )
    _validate_array(
        cfg_file,
        "dims",
        errors,
        length=3,
        minimum=0,
        strict=True,
    )
    _validate_array(cfg_file, "temperature", errors, length=2)
    _validate_number(cfg_file, "datum", errors, minimum=0)
    _validate_number(
        cfg_file,
        "pressure",
        errors,
        minimum=0,
        strict=True,
    )
    _validate_number(cfg_file, "kzMult", errors, minimum=0)
    _validate_array(
        cfg_file,
        "diffusion",
        errors,
        length=2,
        minimum=0,
    )
    _validate_array(
        cfg_file,
        "dispersion",
        errors,
        length=7,
        minimum=0,
    )
    _validate_array(
        cfg_file,
        "radius",
        errors,
        length=2,
        minimum=0,
    )
    well_coord_valid = _validate_matrix(
        cfg_file,
        "wellCoord",
        errors,
        2,
        3,
    )
    refinement_valid: dict[str, bool] = {}
    for key in ("x_n", "y_n", "z_n"):
        refinement_valid[key] = _validate_array(
            cfg_file,
            key,
            errors,
            integer=True,
            minimum=0,
            strict=True,
            nonempty=True,
        )
    if grid == "cartesian":
        for key in ("x_n", "y_n", "z_n"):
            value = cfg_file.get(key)
            if refinement_valid[key] and isinstance(value, list) and len(value) != 1:
                _add_validation_error(
                    errors,
                    f"variable {cli_error_value(key)} has "
                    f"{cli_error_value(str(len(value)))} entries, expected "
                    f"{cli_correct_value('one entry for a Cartesian grid')}.",
                )
    elif grid == "corner-point":
        value = cfg_file.get("z_n")
        if (
            refinement_valid["z_n"]
            and isinstance(value, list)
            and len(value) not in {11, 18}
        ):
            _add_validation_error(
                errors,
                f"variable {cli_error_value('z_n')} has "
                f"{cli_error_value(str(len(value)))} entries, expected "
                f"{cli_correct_value('11 or 18 entries for a corner-point grid')}.",
            )
    if "spe11aBC" in cfg_file:
        _validate_number(cfg_file, "spe11aBC", errors, minimum=0)
    if "rockExtra" in cfg_file:
        _validate_array(
            cfg_file,
            "rockExtra",
            errors,
            length=2,
            minimum=0,
            strict=True,
        )
    if "rockCond" in cfg_file:
        _validate_array(
            cfg_file,
            "rockCond",
            errors,
            length=7,
            minimum=0,
        )
    if "pvAdded" in cfg_file:
        _validate_number(cfg_file, "pvAdded", errors, minimum=0)
    if "widthBuffer" in cfg_file:
        _validate_number(
            cfg_file,
            "widthBuffer",
            errors,
            minimum=0,
            strict=True,
        )
    if "elevation" in cfg_file:
        _validate_number(cfg_file, "elevation", errors, minimum=0)
    if "backElevation" in cfg_file:
        _validate_number(cfg_file, "backElevation", errors)
    well_coord_f_valid = False
    if "wellCoordF" in cfg_file:
        well_coord_f_valid = _validate_matrix(
            cfg_file,
            "wellCoordF",
            errors,
            2,
            3,
        )
    if well_coord_valid:
        _validate_coordinates(cfg_file, "wellCoord", errors)
    if well_coord_f_valid:
        _validate_coordinates(cfg_file, "wellCoordF", errors)
    for key in ("krw", "krn", "pcap", "s_w"):
        _validate_expression(cfg_file, key, errors)
    _validate_saturation_properties(cfg_file, errors)
    _validate_rock_properties(cfg_file, errors)
    tuning_defined = _validate_injection_schedule(cfg_file, errors)
    if tuning_defined and not _is_tuning_enabled(cfg_file.get("flow")):
        pyopmspe11_warning(
            f"TUNING values are defined in {cli_warning_value('inj')}, but "
            f"{cli_warning_value('--enable-tuning=true')} is not set in "
            f"{cli_correct_value('flow')}. The TUNING values may not be effective."
        )
    if model == "convective":
        _validate_drsdtcon(cfg_file, errors)
    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        pyopmspe11_error(f"invalid TOML configuration:\n{details}")
    return cfg_file
