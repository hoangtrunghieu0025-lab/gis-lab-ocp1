"""Test chuyen CRS 4326 <-> 32648.

Y tuong: chon nhung diem BIET TRUOC dap an tu dinh nghia cua UTM, roi so sanh.
Dung pytest.approx(gia_tri, abs=sai_so) de so sanh so thuc (khong dung == voi float).

"""

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


# ---------------------------------------------------------------- dinh nghia UTM

def test_central_meridian_on_equator():
    """(105°E, 0°) la giao cua kinh tuyen truc mui 48 va xich dao.

    Theo dinh nghia UTM: x = false easting = 500 000 m, y = 0 (ban cau Bac).
    """
    x, y = to_utm48n(105.0, 0.0)
    assert x == pytest.approx(500_000, abs=0.001)
    assert y == pytest.approx(0, abs=0.001)


def test_symmetric_about_central_meridian():
    """Hai diem cach deu kinh tuyen truc 105°E (104°E va 106°E, cung vi do 21°N)
    phai doi xung qua duong x = 500 000.
    """
    x1, y1 = to_utm48n(104.0, 21.0)
    x2, y2 = to_utm48n(106.0, 21.0)
    assert x1 + x2 == pytest.approx(1_000_000, abs=0.001)
    assert y1 == pytest.approx(y2, abs=0.001)
    assert x1 < 500_000 < x2


def test_ocp1_point_matches_postgis(ocp1_lonlat):
    """Diem OCP1 phai ra dung toa do PostGIS da tinh bang ST_Transform.

    Lay dap an bang SQL (chay trong DB Manager):
        SELECT ST_X(p), ST_Y(p)
        FROM (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(105.945, 20.995), 4326), 32648) p) t;
    """
    expected_x, expected_y = 598219.3313589817, 2321884.4992228644  # ket qua SQL o tren
    x, y = to_utm48n(*ocp1_lonlat)
    assert x == pytest.approx(expected_x, abs=0.01)
    assert y == pytest.approx(expected_y, abs=0.01)


# ---------------------------------------------------------------- do chinh xac

@pytest.mark.parametrize("lon, lat", [(105.945, 20.995), (102.5, 8.5), (107.9, 23.3)])
def test_round_trip(lon, lat):
    """4326 -> 32648 -> 4326 phai quay ve dung diem ban dau.

    parametrize: pytest chay test nay 3 lan, moi lan voi mot cap (lon, lat).
    Cac diem gom: OCP1, gan bien Tay-Nam mui 48, gan bien Dong-Bac mui 48.
    """
    x, y = to_utm48n(lon, lat)
    lon2, lat2 = to_wgs84(x, y)
    assert lon2 == pytest.approx(lon, abs=1e-9)
    assert lat2 == pytest.approx(lat, abs=1e-9)


def test_area_preserved_in_utm(ocp1_lonlat):
    """O vuong 100 m x 100 m dung o OCP1 (ve trong he 32648) co dien tich 10 000 m².

    So voi dien tich 'chuan' tinh tren ellipsoid (geodesic_area), UTM chi lech < 0.1%
    (lab da do: toa nha id 542 lech -0.06%).
    """
    x, y = to_utm48n(*ocp1_lonlat)
    square_utm = gpd.GeoDataFrame(geometry=[box(x, y, x + 100, y + 100)], crs=UTM48N)
    square_4326 = reproject_gdf(square_utm, WGS84)
    area_true = geodesic_area(square_4326.geometry.iloc[0])
    rel_error = abs(10_000 - area_true) / area_true
    print(f"\nDien tich that: {area_true:.2f} m², UTM: 10000 m², sai so: {rel_error:.4%}")
    assert rel_error < 0.001


def test_area_in_degrees_is_meaningless(ocp1_lonlat):
    """Minh hoa cho bao cao: .area tren he 4326 cho ra 'do²', khong phai m²."""
    x, y = to_utm48n(*ocp1_lonlat)
    square_utm = gpd.GeoDataFrame(geometry=[box(x, y, x + 100, y + 100)], crs=UTM48N)
    gdf_4326 = reproject_gdf(square_utm, WGS84)
    with pytest.warns(UserWarning, match="geographic CRS"):
        area_deg2 = gdf_4326.geometry.area.iloc[0]
    print(f"\nO vuong 10 000 m² tinh tren 4326 = {area_deg2:.3e} do²")
    assert area_deg2 < 1e-6


# ---------------------------------------------------------------- kiem tra dau vao

def test_swapped_axis_is_rejected(ocp1_lonlat):
    """Truyen nham (lat, lon) thay vi (lon, lat) phai bi bao loi."""
    lon, lat = ocp1_lonlat
    # lat nhan gia tri 105.945 > 90 -> validate_lonlat bao loi
    with pytest.raises(ValueError, match="dao truc"):
        to_utm48n(lat, lon)


@pytest.mark.parametrize("lon, lat", [(0, 95), (0, -90.1), (181, 0), (-180.5, 0)])
def test_out_of_range_is_rejected(lon, lat):
    """Kinh/vi do ngoai pham vi phai bi validate_lonlat bao ValueError."""
    with pytest.raises(ValueError):
        validate_lonlat(lon, lat)


def test_reproject_requires_crs():
    """GeoDataFrame chua khai bao CRS thi reproject_gdf phai bao loi, khong duoc doan."""
    gdf_no_crs = gpd.GeoDataFrame(geometry=[Point(105.945, 20.995)])  # khong co crs=
    with pytest.raises(ValueError):
        reproject_gdf(gdf_no_crs, UTM48N)


def test_reproject_sets_crs(ocp1_lonlat):
    """Sau reproject_gdf, CRS cua ket qua phai la EPSG dich va toa do phai doi sang met."""
    gdf = gpd.GeoDataFrame(geometry=[Point(*ocp1_lonlat)], crs=WGS84)
    out = reproject_gdf(gdf, UTM48N)
    assert out.crs.to_epsg() == 32648
    assert out.crs.axis_info[0].unit_name == "metre"
    assert gdf.crs.to_epsg() == 4326  # gdf goc khong bi sua
