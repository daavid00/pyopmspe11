# SPDX-FileCopyrightText: 2023-2026 NORCE Research AS
# SPDX-License-Identifier: MIT

"""Test the script to plot the data"""

import pathlib
import shutil

from pyopmspe11.visualization.plotting import main

testpth = pathlib.Path(__file__).parent


def test_g_plot(tmp_path, monkeypatch):
    """Generate benchmark plots"""
    monkeypatch.chdir(tmp_path)
    tflags = {"a": "1", "b": "5", "c": "5"}
    for x in ("a", "b", "c"):
        run = tmp_path / f"spe11{x}_corner-point"
        shutil.copytree(testpth / "datas" / f"spe11{x}_corner-point", run)
        flags = [
            "-p",
            f"spe11{x}_corner-point",
            "-g",
            "all",
            "-f",
            "0",
            "-d",
            f"spe11{x}",
            "-t",
            tflags[x],
        ]
        main(flags)
        files = [
            "performance",
            "performance_detailed",
            "sparse_data",
            "co2_max_norm_res_2dmaps",
            "co2_mb_error_2dmaps",
            "h2o_max_norm_res_2dmaps",
            "h2o_mb_error_2dmaps",
            "arat_2dmaps",
            "cvol_2dmaps",
            "tco2_2dmaps",
            "gden_2dmaps",
            "pressure_2dmaps",
            "sgas_2dmaps",
            "wden_2dmaps",
            "xco2_2dmaps",
            "xh2o_2dmaps",
        ]
        if x in ["b", "c"]:
            files += ["temp_2dmaps"]
        for file in files:
            figure = run / f"spe11{x}_{file}.png"
            assert figure.is_file(), f"Missing {figure}"
