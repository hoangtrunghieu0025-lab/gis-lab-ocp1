import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from src.crs import (
    UTM48N,
    WGS84,
    geodesic_area,
    reproject_gdf,
    to_utm48n,
    to_wgs84,
    validate_lonlat,
)


def test_central_meridian_on_equator():
    x, y = to_utm48n(105.0, 0.0)
    assert x == pytest.approx(500_000, abs=0.001)
    assert y == pytest.approx(0, abs=0.001)


def test_symmetric_about_central_meridian():
    x1, y1 = to_utm48n(104.0, 21.0)
    x2, y2 = to_utm48n(106.0, 21.0)
    assert x1 + x2 == pytest.approx(1_000_000, abs=0.001)
    assert y1 == pytest.approx(y2, abs=0.001)
    assert x1 < 500_000 < x2


def test_ocp1_point_matches_postgis(ocp1_lonlat):
    # SELECT ST_Transform(ST_SetSRID(ST_MakePoint(105.945, 20.995), 4326), 32648)
    expected_x, expected_y = 598219.3313589817, 2321884.4992228644
    x, y = to_utm48n(*ocp1_lonlat)
    assert x == pytest.approx(expected_x, abs=0.01)
    assert y == pytest.approx(expected_y, abs=0.01)


@pytest.mark.parametrize("lon, lat", [(105.945, 20.995), (102.5, 8.5), (107.9, 23.3)])
def test_round_trip(lon, lat):
    x, y = to_utm48n(lon, lat)
    lon2, lat2 = to_wgs84(x, y)
    assert lon2 == pytest.approx(lon, abs=1e-9)
    assert lat2 == pytest.approx(lat, abs=1e-9)


def test_area_preserved_in_utm(ocp1_lonlat):
    x, y = to_utm48n(*ocp1_lonlat)
    square_utm = gpd.GeoDataFrame(geometry=[box(x, y, x + 100, y + 100)], crs=UTM48N)
    square_4326 = reproject_gdf(square_utm, WGS84)
    area_true = geodesic_area(square_4326.geometry.iloc[0])
    rel_error = abs(10_000 - area_true) / area_true
    print(f"\nDien tich that: {area_true:.2f} m², UTM: 10000 m², sai so: {rel_error:.4%}")
    assert rel_error < 0.001


def test_area_in_degrees_is_meaningless(ocp1_lonlat):
    x, y = to_utm48n(*ocp1_lonlat)
    square_utm = gpd.GeoDataFrame(geometry=[box(x, y, x + 100, y + 100)], crs=UTM48N)
    gdf_4326 = reproject_gdf(square_utm, WGS84)
    with pytest.warns(UserWarning, match="geographic CRS"):
        area_deg2 = gdf_4326.geometry.area.iloc[0]
    print(f"\nO vuong 10 000 m² tinh tren 4326 = {area_deg2:.3e} do²")
    assert area_deg2 < 1e-6


def test_swapped_axis_is_rejected(ocp1_lonlat):
    lon, lat = ocp1_lonlat
    with pytest.raises(ValueError, match="dao truc"):
        to_utm48n(lat, lon)


@pytest.mark.parametrize("lon, lat", [(0, 95), (0, -90.1), (181, 0), (-180.5, 0)])
def test_out_of_range_is_rejected(lon, lat):
    with pytest.raises(ValueError):
        validate_lonlat(lon, lat)


def test_reproject_requires_crs():
    gdf_no_crs = gpd.GeoDataFrame(geometry=[Point(105.945, 20.995)])
    with pytest.raises(ValueError):
        reproject_gdf(gdf_no_crs, UTM48N)


def test_reproject_sets_crs(ocp1_lonlat):
    gdf = gpd.GeoDataFrame(geometry=[Point(*ocp1_lonlat)], crs=WGS84)
    out = reproject_gdf(gdf, UTM48N)
    assert out.crs.to_epsg() == 32648
    assert out.crs.axis_info[0].unit_name == "metre"
    assert gdf.crs.to_epsg() == 4326
