"""Chuyen doi he toa do (CRS) giua WGS84 (EPSG:4326) va UTM 48N (EPSG:32648)."""

from functools import lru_cache

import geopandas as gpd
from pyproj import Geod, Transformer
from shapely.geometry.base import BaseGeometry

WGS84 = 4326     # he dia ly, don vi do
UTM48N = 32648   # he chieu phang, don vi met, mui 48 (102°E - 108°E)

# Ellipsoid WGS84 de tinh dien tich/khoang cach "chuan" tren mat cong (khong qua phep chieu)
_GEOD = Geod(ellps="WGS84")


def validate_lonlat(lon: float, lat: float) -> None:
    """Bao loi ValueError neu (lon, lat) nam ngoai pham vi hop le.

    Ham nay cung giup bat loi DAO TRUC: neu ai do truyen (lat, lon) cua OCP1
    = (20.99, 105.94) thi lat = 105.94 > 90 -> phai bao loi.
    """
    if not -90 <= lat <= 90:
        raise ValueError(f"Vi do {lat} ngoai pham vi [-90, 90] (co the bi dao truc lon/lat?)")
    if not -180 <= lon <= 180:
        raise ValueError(f"Kinh do {lon} ngoai pham vi [-180, 180]")


@lru_cache(maxsize=None)
def get_transformer(src_epsg: int, dst_epsg: int) -> Transformer:
    """Tra ve Transformer chuyen tu src_epsg sang dst_epsg (co cache de dung lai)."""
    # always_xy=True: theo chuan EPSG, 4326 co thu tu truc (lat, lon). Co nay ep pyproj
    # luon dung (x, y) = (lon, lat) giong PostGIS/GeoJSON/QGIS.
    return Transformer.from_crs(src_epsg, dst_epsg, always_xy=True)


def to_utm48n(lon: float, lat: float) -> tuple[float, float]:
    """Chuyen mot diem (lon, lat) WGS84 sang (x, y) met trong UTM 48N."""
    validate_lonlat(lon, lat)
    transformer = get_transformer(WGS84, UTM48N)
    return transformer.transform(lon, lat)


def to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Chuyen mot diem (x, y) UTM 48N ve (lon, lat) WGS84. Nguoc lai cua to_utm48n."""
    transformer = get_transformer(UTM48N, WGS84)
    transformed_lon, transformed_lat = transformer.transform(x, y)
    # Kiem tra ca dau ra: (x, y) vo ly co the cho ra inf
    validate_lonlat(transformed_lon, transformed_lat)
    return transformed_lon, transformed_lat


def reproject_gdf(gdf: gpd.GeoDataFrame, epsg: int) -> gpd.GeoDataFrame:
    """Chuyen ca GeoDataFrame sang he epsg.

    Bao loi ValueError neu gdf chua khai bao CRS (khong biet chuyen tu dau).
    """
    if gdf.crs is None:
        raise ValueError("GeoDataFrame chua khai bao CRS (gdf.crs is None).")
    return gdf.to_crs(epsg=epsg)


def geodesic_area(geom_wgs84: BaseGeometry) -> float:
    """Dien tich (m²) tinh tren ellipsoid WGS84, dung lam gia tri 'chuan' de so sanh.

    Tuong duong ST_Area(geom::geography) trong PostGIS.
    """
    area, _perimeter = _GEOD.geometry_area_perimeter(geom_wgs84)
    return abs(area)
