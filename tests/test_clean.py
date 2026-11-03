import shutil
import warnings

import geopandas as gpd
import pytest
import shapely
from shapely.geometry import MultiPolygon

from src.clean import (
    clean_geometries,
    drop_duplicate_geometries,
    fix_invalid,
    keep_polygons,
    remove_empty,
    remove_repeated_points,
)


def _row(gdf: gpd.GeoDataFrame, name: str):
    return gdf.loc[gdf["name"] == name, "geometry"].iloc[0]


def test_sample_cases_are_really_invalid(sample_geoms):
    for name in ["bowtie", "hole_outside", "spike", "collapsed"]:
        assert not sample_geoms[name].is_valid, name
    for name in ["repeated", "ok"]:
        assert sample_geoms[name].is_valid, name


def test_remove_empty(sample_gdf):
    out = remove_empty(sample_gdf)
    assert "empty" not in out["name"].values
    assert "null" not in out["name"].values
    assert len(out) == len(sample_gdf) - 2


def test_fix_invalid_bowtie(sample_gdf):
    fixed = fix_invalid(remove_empty(sample_gdf))
    g = _row(fixed, "bowtie")
    assert g.is_valid
    assert g.geom_type == "MultiPolygon"
    assert len(g.geoms) == 2
    for part in g.geoms:
        assert part.area == pytest.approx(25)


def test_fix_invalid_keeps_valid_unchanged(sample_gdf):
    fixed = fix_invalid(remove_empty(sample_gdf))
    assert _row(fixed, "ok").equals_exact(_row(sample_gdf, "ok"), tolerance=0)


def test_keep_polygons_from_collection(sample_geoms):
    collection = shapely.make_valid(sample_geoms["spike"])
    assert collection.geom_type == "GeometryCollection"
    result = keep_polygons(collection)
    assert isinstance(result, MultiPolygon)
    assert result.area == pytest.approx(100)


def test_keep_polygons_returns_none_without_area(sample_geoms):
    assert keep_polygons(shapely.make_valid(sample_geoms["collapsed"])) is None


def test_remove_repeated_points(sample_gdf):
    original = _row(sample_gdf, "repeated")
    out = remove_repeated_points(remove_empty(sample_gdf))
    cleaned = _row(out, "repeated")
    assert shapely.get_num_coordinates(cleaned) == shapely.get_num_coordinates(original) - 1
    assert cleaned.area == pytest.approx(original.area)


def test_drop_duplicate_geometries(sample_gdf):
    out = drop_duplicate_geometries(remove_empty(sample_gdf))
    assert "ok" in out["name"].values
    assert "duplicate_of_ok" not in out["name"].values


def test_clean_geometries_pipeline(sample_gdf):
    out, report = clean_geometries(sample_gdf)
    print(f"\n{report}")
    assert out.geometry.is_valid.all()
    assert (out.geom_type == "MultiPolygon").all()
    assert report["invalid_before"] == 4
    assert report["invalid_after"] == 0
    assert report["output"] == 5
    assert set(out["name"]) == {"bowtie", "hole_outside", "spike", "repeated", "ok"}


def test_export_for_qgis(sample_gdf, output_dir, tmp_path):
    out, _ = clean_geometries(sample_gdf)
    path = tmp_path / "test_results.gpkg"
    remove_empty(sample_gdf).to_file(path, layer="before", driver="GPKG")
    out.to_file(path, layer="after", driver="GPKG")

    layers = set(gpd.list_layers(path)["name"])
    assert layers == {"before", "after"}
    assert gpd.read_file(path, layer="after").crs.to_epsg() == 32648

    try:
        shutil.copyfile(path, output_dir / "test_results.gpkg")
    except PermissionError:
        warnings.warn("output/test_results.gpkg dang duoc mo (QGIS?) -> khong cap nhat file nay")
