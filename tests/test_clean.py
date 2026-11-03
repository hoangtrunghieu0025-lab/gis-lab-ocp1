"""Test lam sach geometry voi cac ca loi tu tao (xem SAMPLE_WKT trong conftest.py).

Moi test kiem tra MOT ham trong src/clean.py. Test cuoi ghi ket qua ra
output/test_results.gpkg de mo tren QGIS va nhin truc tiep truoc/sau.
"""

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
    """Lay geometry cua dong co cot name = name."""
    return gdf.loc[gdf["name"] == name, "geometry"].iloc[0]


# ---------------------------------------------------------------- tung buoc

def test_sample_cases_are_really_invalid(sample_geoms):
    """Kiem tra du lieu mau dung nhu mo ta (test cua chinh fixture). Da viet san."""
    for name in ["bowtie", "hole_outside", "spike", "collapsed"]:
        assert not sample_geoms[name].is_valid, name
    for name in ["repeated", "ok"]:
        assert sample_geoms[name].is_valid, name


def test_remove_empty(sample_gdf):
    """Dong 'empty' (POLYGON EMPTY) va 'null' (None) phai bi loai, cac dong khac giu nguyen."""
    out = remove_empty(sample_gdf)
    assert "empty" not in out["name"].values
    assert "null" not in out["name"].values
    assert len(out) == len(sample_gdf) - 2


def test_fix_invalid_bowtie(sample_gdf):
    """Bowtie (hinh so 8) sau khi sua: hop le, la MultiPolygon gom 2 tam giac, moi tam giac 25 m²."""
    fixed = fix_invalid(remove_empty(sample_gdf))
    g = _row(fixed, "bowtie")
    assert g.is_valid
    assert g.geom_type == "MultiPolygon"
    assert len(g.geoms) == 2
    for part in g.geoms:
        assert part.area == pytest.approx(25)


def test_fix_invalid_keeps_valid_unchanged(sample_gdf):
    """Geometry von da hop le ('ok') KHONG duoc bi thay doi.

    Day la test quan trong nhat: code lam sach khong duoc lam hong du lieu tot.
    """
    fixed = fix_invalid(remove_empty(sample_gdf))
    assert _row(fixed, "ok").equals_exact(_row(sample_gdf, "ok"), tolerance=0)


def test_keep_polygons_from_collection(sample_geoms):
    """'spike' sau make_valid la GeometryCollection(Polygon, LineString).
    keep_polygons phai bo LineString, chi giu MultiPolygon dien tich 100 m².
    """
    collection = shapely.make_valid(sample_geoms["spike"])
    assert collection.geom_type == "GeometryCollection"  # tien de, da kiem tra
    result = keep_polygons(collection)
    assert isinstance(result, MultiPolygon)
    assert result.area == pytest.approx(100)


def test_keep_polygons_returns_none_without_area(sample_geoms):
    """'collapsed' sau make_valid chi con LineString -> keep_polygons tra ve None."""
    assert keep_polygons(shapely.make_valid(sample_geoms["collapsed"])) is None


def test_remove_repeated_points(sample_gdf):
    """'repeated' co dinh (0 0) lap 2 lan lien tiep -> sau khi xu ly so dinh giam 1."""
    original = _row(sample_gdf, "repeated")
    out = remove_repeated_points(remove_empty(sample_gdf))
    cleaned = _row(out, "repeated")
    assert shapely.get_num_coordinates(cleaned) == shapely.get_num_coordinates(original) - 1
    assert cleaned.area == pytest.approx(original.area)


def test_drop_duplicate_geometries(sample_gdf):
    """'duplicate_of_ok' giong het 'ok' nhung bat dau tu dinh khac -> phai bi loai, 'ok' duoc giu."""
    out = drop_duplicate_geometries(remove_empty(sample_gdf))
    assert "ok" in out["name"].values
    assert "duplicate_of_ok" not in out["name"].values


# ---------------------------------------------------------------- ca quy trinh

def test_clean_geometries_pipeline(sample_gdf):
    """Chay ca quy trinh: ket qua phai toan geometry hop le, toan MultiPolygon, khong rong."""
    out, report = clean_geometries(sample_gdf)
    print(f"\n{report}")
    assert out.geometry.is_valid.all()
    assert (out.geom_type == "MultiPolygon").all()
    assert report["invalid_before"] == 4  # bowtie, hole_outside, spike, collapsed
    assert report["invalid_after"] == 0
    # 9 dong - empty - null - collapsed (khong con dien tich) - duplicate_of_ok = 5
    assert report["output"] == 5
    assert set(out["name"]) == {"bowtie", "hole_outside", "spike", "repeated", "ok"}


def test_export_for_qgis(sample_gdf, output_dir, tmp_path):
    """Ghi 2 lop 'before' va 'after' ra GeoPackage de xem tren QGIS (CRS 32648, nam o OCP1).

    Ghi va kiem tra o thu muc tam (tmp_path) truoc, roi moi chep sang output/.
    Neu QGIS dang mo output/test_results.gpkg (Windows khoa file) thi chi canh bao,
    khong lam test FAIL, vi ban than viec ghi file van dung.
    """
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
