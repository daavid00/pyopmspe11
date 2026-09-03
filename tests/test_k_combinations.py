# SPDX-FileCopyrightText: 2026 NORCE Research AS
# SPDX-License-Identifier: MIT

"""Test the supported combinations for -g with -m data and -m plot"""

import pathlib
import shutil

from pyopmspe11.core.pyopmspe11 import main

testpth = pathlib.Path(__file__).parent


def test_k_combinations(tmp_path, monkeypatch):
    """Generate benchmark plots"""
    monkeypatch.chdir(tmp_path)
    tflags = {"a": "1", "b": "5", "c": "5"}
    for x in ("a", "b", "c"):
        t = "h" if x == "a" else "y"
        n = "1" if x == "a" else "5"
        for y, csvs, pngs in zip(
            [
                "performance-spatial",
                "dense",
                "sparse",
                "performance",
                "performance_sparse",
                "dense_performance",
                "dense_sparse",
                "dense_performance-spatial",
                "dense_performance_sparse",
            ],
            [
                [f"performance_spatial_map_0{t}", f"performance_spatial_map_{n}{t}"],
                [f"spatial_map_0{t}", f"spatial_map_{n}{t}"],
                ["time_series"],
                ["performance_time_series", "performance_time_series_detailed"],
                [
                    "time_series",
                    "performance_time_series",
                    "performance_time_series_detailed",
                ],
                [
                    f"spatial_map_0{t}",
                    f"spatial_map_{n}{t}",
                    "performance_time_series",
                    "performance_time_series_detailed",
                ],
                ["time_series", f"spatial_map_0{t}", f"spatial_map_{n}{t}"],
                [
                    f"spatial_map_0{t}",
                    f"spatial_map_{n}{t}",
                    f"performance_spatial_map_0{t}",
                    f"performance_spatial_map_{n}{t}",
                ],
                [
                    f"spatial_map_0{t}",
                    f"spatial_map_{n}{t}",
                    "performance_time_series",
                    "performance_time_series_detailed",
                ],
            ],
            [
                [
                    "arat_2dmaps",
                    "cvol_2dmaps",
                    "co2_max_norm_res_2dmaps",
                    "co2_mb_error_2dmaps",
                    "h2o_max_norm_res_2dmaps",
                    "h2o_mb_error_2dmaps",
                ],
                [
                    "gden_2dmaps",
                    "pressure_2dmaps",
                    "sgas_2dmaps",
                    "tco2_2dmaps",
                    "wden_2dmaps",
                    "xco2_2dmaps",
                    "xh2o_2dmaps",
                ],
                ["sparse_data"],
                ["performance", "performance_detailed"],
                ["sparse_data", "performance", "performance_detailed"],
                [
                    "gden_2dmaps",
                    "pressure_2dmaps",
                    "sgas_2dmaps",
                    "tco2_2dmaps",
                    "wden_2dmaps",
                    "xco2_2dmaps",
                    "xh2o_2dmaps",
                    "performance",
                    "performance_detailed",
                ],
                [
                    "gden_2dmaps",
                    "pressure_2dmaps",
                    "sgas_2dmaps",
                    "tco2_2dmaps",
                    "wden_2dmaps",
                    "xco2_2dmaps",
                    "xh2o_2dmaps",
                    "sparse_data",
                ],
                [
                    "gden_2dmaps",
                    "pressure_2dmaps",
                    "sgas_2dmaps",
                    "tco2_2dmaps",
                    "wden_2dmaps",
                    "xco2_2dmaps",
                    "xh2o_2dmaps",
                    "arat_2dmaps",
                    "cvol_2dmaps",
                    "co2_max_norm_res_2dmaps",
                    "co2_mb_error_2dmaps",
                    "h2o_max_norm_res_2dmaps",
                    "h2o_mb_error_2dmaps",
                ],
                [
                    "gden_2dmaps",
                    "pressure_2dmaps",
                    "sgas_2dmaps",
                    "tco2_2dmaps",
                    "wden_2dmaps",
                    "xco2_2dmaps",
                    "xh2o_2dmaps",
                    "performance",
                    "performance_detailed",
                    "sparse_data",
                ],
            ],
        ):
            run = tmp_path / f"data-{y}" / f"spe11{x}_corner-point"
            shutil.copytree(testpth / "flows" / f"spe11{x}_corner-point", run)
            cfg_name = str(testpth / "configs" / f"spe11{x}_corner-point.toml")
            flags = [
                "-o",
                f"data-{y}/spe11{x}_corner-point",
                "-g",
                y,
                "-m",
                "data",
                "-f",
                "0",
                "-i",
                cfg_name,
                "-t",
                tflags[x],
            ]
            main(flags)
            for file in csvs:
                data = run / f"spe11{x}_{file}.csv"
                assert data.is_file(), f"Missing {data}"
            flags = [
                "-o",
                f"data-{y}/spe11{x}_corner-point",
                "-g",
                y,
                "-m",
                "plot",
                "-f",
                "0",
                "-i",
                cfg_name,
                "-t",
                tflags[x],
            ]
            main(flags)
            if x in ["b", "c"] and "dense" in y:
                pngs += ["temp_2dmaps"]
            for file in pngs:
                data = run / f"spe11{x}_{file}.png"
                assert data.is_file(), f"Missing {data}"
