"""Lam sach geometry: bo rong, sua loi, giu dung kieu polygon, bo trung lap."""

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry


def remove_empty(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Bo cac dong co geometry la None (null) hoac rong (EMPTY)."""
    bad = gdf.geometry.isna() | gdf.geometry.is_empty
    return gdf[~bad]


def fix_invalid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Sua cac geometry khong hop le bang make_valid. Geometry da hop le giu nguyen."""
    out = gdf.copy()
    mask = ~out.geometry.is_valid
    # Chi sua dong loi -> geometry von hop le giu nguyen tung bit (tuong duong ST_MakeValid)
    out.loc[mask, "geometry"] = shapely.make_valid(out.loc[mask, "geometry"].values)
    return out


def keep_polygons(geom: BaseGeometry) -> MultiPolygon | None:
    """Chi giu phan polygon cua geometry, tra ve MultiPolygon (hoac None neu khong con gi).

    Sau make_valid, mot polygon loi co the thanh GeometryCollection lan ca
    LineString/Point (vi du phan "gai" bi bep thanh duong). Bang building chi
    chap nhan MultiPolygon nen phai loc bo phan khong phai polygon.
    """
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])

    # GeometryCollection hoac Multi* khac: gom cac Polygon ben trong
    polygons = []
    for part in getattr(geom, "geoms", []):
        if isinstance(part, Polygon):
            polygons.append(part)
        elif isinstance(part, MultiPolygon):
            polygons.extend(part.geoms)
    return MultiPolygon(polygons) if polygons else None


def remove_repeated_points(gdf: gpd.GeoDataFrame, tolerance: float = 0.0) -> gpd.GeoDataFrame:
    """Bo cac dinh trung lien tiep (hai dinh canh nhau cung toa do)."""
    out = gdf.copy()
    out["geometry"] = shapely.remove_repeated_points(out.geometry.values, tolerance=tolerance)
    return out


def drop_duplicate_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Bo cac dong co geometry trung nhau, giu dong dau tien."""
    # Hai polygon giong het nhung bat dau tu dinh khac nhau van la "trung"
    # -> chuan hoa (normalize) truoc, roi so sanh dang nhi phan WKB
    wkb = pd.Series(shapely.to_wkb(shapely.normalize(gdf.geometry.values)), index=gdf.index)
    return gdf[~wkb.duplicated(keep="first")]


def clean_geometries(gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    """Chay toan bo quy trinh lam sach, tra ve (gdf da sach, bao cao so lieu)."""
    report = {
        "input": len(gdf),
        "invalid_before": sum(g is not None and not g.is_valid for g in gdf.geometry),
    }

    out = remove_empty(gdf)
    report["removed_empty"] = report["input"] - len(out)

    out = fix_invalid(out)
    out["geometry"] = out.geometry.apply(keep_polygons)
    n = len(out)
    out = remove_empty(out)  # keep_polygons co the tra ve None
    report["removed_non_polygon"] = n - len(out)

    out = remove_repeated_points(out)

    n = len(out)
    out = drop_duplicate_geometries(out)
    report["removed_duplicates"] = n - len(out)

    report["invalid_after"] = int((~out.geometry.is_valid).sum())
    report["output"] = len(out)
    return out.reset_index(drop=True), report
