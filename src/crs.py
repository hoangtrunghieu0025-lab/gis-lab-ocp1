"""Chuyen doi CRS giua WGS84 (EPSG:4326) va UTM 48N (EPSG:32648)."""

from functools import lru_cache

import geopandas as gpd
from pyproj import Geod, Transformer
from shapely.geometry.base import BaseGeometry

WGS84 = 4326
UTM48N = 32648

_GEOD = Geod(ellps="WGS84")


def validate_lonlat(lon: float, lat: float) -> None:
    if not -90 <= lat <= 90:
        raise ValueError(f"Vi do {lat} ngoai pham vi [-90, 90] (co the bi dao truc lon/lat?)")
    if not -180 <= lon <= 180:
        raise ValueError(f"Kinh do {lon} ngoai pham vi [-180, 180]")


@lru_cache(maxsize=None)
def get_transformer(src_epsg: int, dst_epsg: int) -> Transformer:
    return Transformer.from_crs(src_epsg, dst_epsg, always_xy=True)


def to_utm48n(lon: float, lat: float) -> tuple[float, float]:
    validate_lonlat(lon, lat)
    return get_transformer(WGS84, UTM48N).transform(lon, lat)


def to_wgs84(x: float, y: float) -> tuple[float, float]:
    lon, lat = get_transformer(UTM48N, WGS84).transform(x, y)
    validate_lonlat(lon, lat)
    return lon, lat


def reproject_gdf(gdf: gpd.GeoDataFrame, epsg: int) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("GeoDataFrame chua khai bao CRS (gdf.crs is None).")
    return gdf.to_crs(epsg=epsg)


def geodesic_area(geom_wgs84: BaseGeometry) -> float:
    """Dien tich (m²) tren ellipsoid WGS84, tuong duong ST_Area(geom::geography)."""
    area, _ = _GEOD.geometry_area_perimeter(geom_wgs84)
    return abs(area)
