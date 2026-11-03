"""Lam sach geometry: bo rong, sua loi, giu dung kieu polygon, bo trung lap."""

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry


def remove_empty(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    bad = gdf.geometry.isna() | gdf.geometry.is_empty
    return gdf[~bad]


def fix_invalid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    mask = ~out.geometry.is_valid
    out.loc[mask, "geometry"] = shapely.make_valid(out.loc[mask, "geometry"].values)
    return out


def keep_polygons(geom: BaseGeometry) -> MultiPolygon | None:
    """Chi giu phan polygon (sau make_valid co the con LineString/Point)."""
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])

    polygons = []
    for part in getattr(geom, "geoms", []):
        if isinstance(part, Polygon):
            polygons.append(part)
        elif isinstance(part, MultiPolygon):
            polygons.extend(part.geoms)
    return MultiPolygon(polygons) if polygons else None


def remove_repeated_points(gdf: gpd.GeoDataFrame, tolerance: float = 0.0) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = shapely.remove_repeated_points(out.geometry.values, tolerance=tolerance)
    return out


def drop_duplicate_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    wkb = pd.Series(shapely.to_wkb(shapely.normalize(gdf.geometry.values)), index=gdf.index)
    return gdf[~wkb.duplicated(keep="first")]


def clean_geometries(gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    report = {
        "input": len(gdf),
        "invalid_before": sum(g is not None and not g.is_valid for g in gdf.geometry),
    }

    out = remove_empty(gdf)
    report["removed_empty"] = report["input"] - len(out)

    out = fix_invalid(out)
    out["geometry"] = out.geometry.apply(keep_polygons)
    n = len(out)
    out = remove_empty(out)
    report["removed_non_polygon"] = n - len(out)

    out = remove_repeated_points(out)

    n = len(out)
    out = drop_duplicate_geometries(out)
    report["removed_duplicates"] = n - len(out)

    report["invalid_after"] = int((~out.geometry.is_valid).sum())
    report["output"] = len(out)
    return out.reset_index(drop=True), report
