"""Test tren du lieu that trong PostGIS (bang building_4326, building_32648).

Can container ocp1-postgis dang chay. Neu khong, fixture db_engine se skip ca file.
Chay rieng nhom nay: pytest -m postgis
"""

import geopandas as gpd
import pytest
from sqlalchemy import text

from src.clean import clean_geometries
from src.crs import UTM48N, reproject_gdf

pytestmark = pytest.mark.postgis  # gan nhan postgis cho moi test trong file


def test_tables_exist_with_right_srid(db_engine):
    """Hai bang phai ton tai va cot geom co SRID dung. Da viet san lam mau."""
    with db_engine.connect() as conn:
        srid_4326 = conn.execute(text("SELECT Find_SRID('public', 'building_4326', 'geom')")).scalar()
        srid_32648 = conn.execute(text("SELECT Find_SRID('public', 'building_32648', 'geom')")).scalar()
    assert srid_4326 == 4326
    assert srid_32648 == 32648


def test_row_counts_match(db_engine):
    """ST_Transform khong duoc lam mat dong: hai bang phai co cung so dong (1819)."""
    with db_engine.connect() as conn:
        n_4326 = conn.execute(text("SELECT count(*) FROM building_4326")).scalar()
        n_32648 = conn.execute(text("SELECT count(*) FROM building_32648")).scalar()
    assert n_4326 == n_32648 == 1819


def test_pyproj_matches_st_transform(db_engine):
    """pyproj (PROJ 9.x tren may) va ST_Transform (PROJ 7.2 trong container) phai cho cung ket qua.

    So sanh tam (centroid) cua cung toa nha trong 2 cach chuyen, chenh lech < 1 mm.
    """
    src = gpd.read_postgis("SELECT id, geom FROM building_4326", db_engine, geom_col="geom")
    ref = gpd.read_postgis("SELECT id, geom FROM building_32648", db_engine, geom_col="geom")

    ours = reproject_gdf(src, UTM48N).set_index("id").geometry.centroid
    theirs = ref.set_index("id").geometry.centroid
    distance = ours.distance(theirs.loc[ours.index])

    print(f"\nChenh lech lon nhat pyproj vs ST_Transform: {distance.max():.2e} m")
    assert len(distance) == 1819
    assert distance.max() < 0.001


def test_real_data_after_cleaning(db_engine):
    """Lam sach du lieu that OCP1: sau khi sach khong con loi, khong rong, toan MultiPolygon."""
    gdf = gpd.read_postgis("SELECT id, building, geom FROM building_32648", db_engine, geom_col="geom")
    gdf = gdf.rename_geometry("geometry")  # clean_geometries dung cot ten "geometry"

    out, report = clean_geometries(gdf)
    print(f"\n{report}")
    assert report["invalid_after"] == 0
    assert (out.geom_type == "MultiPolygon").all()
    # OCP1 co 0 geometry loi, 0 rong; chi co the mat dong neu OSM ve trung toa nha
    assert report["output"] == report["input"] - report["removed_duplicates"]


def test_postgis_validity_agrees_with_shapely(db_engine):
    """ST_IsValid (PostGIS) va is_valid (shapely) cung dung GEOS -> phai dong y voi nhau."""
    with db_engine.connect() as conn:
        invalid_postgis = conn.execute(
            text("SELECT count(*) FILTER (WHERE NOT ST_IsValid(geom)) FROM building_32648")
        ).scalar()
    gdf = gpd.read_postgis("SELECT geom FROM building_32648", db_engine, geom_col="geom")
    invalid_shapely = int((~gdf.geometry.is_valid).sum())
    assert invalid_postgis == invalid_shapely
