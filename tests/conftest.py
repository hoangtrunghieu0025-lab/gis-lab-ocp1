"""Du lieu mau va fixture dung chung cho moi file test.

Fixture = ham chuan bi du lieu, pytest tu goi va truyen vao test theo TEN tham so.
Vi du: def test_x(ocp1_lonlat): ...  -> pytest goi fixture ocp1_lonlat() roi dua ket qua vao.
"""

import os
from pathlib import Path

import geopandas as gpd
import pytest
import shapely
from dotenv import load_dotenv
from shapely import affinity

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

# Goc dat cac ca loi mau: mot diem trong khu OCP1 (he 32648, met).
# Nho vay khi mo output/test_results.gpkg tren QGIS, cac hinh mau nam ngay tren OCP1.
SAMPLE_ORIGIN_UTM = (598_000.0, 2_321_000.0)

# Cac ca geometry mau (toa do cuc bo, don vi met, se duoc dich toi SAMPLE_ORIGIN_UTM).
# Da kiem tra bang shapely 2.2:
#   ten          | is_valid | ly do (is_valid_reason)              | make_valid tra ve
#   bowtie       | False    | Self-intersection [5 5]              | MultiPolygon 2 tam giac, area 50
#   hole_outside | False    | Hole lies outside shell              | MultiPolygon 2 phan, area 125
#   spike        | False    | Ring Self-intersection [10 10]       | GeometryCollection(Polygon, LineString)
#   collapsed    | False    | Too few points in geometry component | LineString (khong con dien tich)
#   repeated     | True     | Valid (nhung co dinh trung)          | giu nguyen
#   ok           | True     | Valid                                | giu nguyen
SAMPLE_WKT = {
    "bowtie": "POLYGON ((0 0, 10 10, 10 0, 0 10, 0 0))",
    "hole_outside": "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (15 15, 20 15, 20 20, 15 20, 15 15))",
    "spike": "POLYGON ((0 0, 10 0, 10 10, 10 20, 10 10, 0 10, 0 0))",
    "collapsed": "POLYGON ((0 0, 10 10, 0 0, 0 0))",
    "repeated": "POLYGON ((0 0, 0 0, 10 0, 10 10, 0 10, 0 0))",
    "ok": "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))",
}


@pytest.fixture
def ocp1_lonlat() -> tuple[float, float]:
    """Mot diem giua khu OCP1 (Ho Ngoc Trai), thu tu (lon, lat)."""
    return (105.945, 20.995)


@pytest.fixture
def sample_geoms() -> dict:
    """Dict ten -> geometry shapely (toa do cuc bo, chua dich)."""
    return {name: shapely.from_wkt(wkt) for name, wkt in SAMPLE_WKT.items()}


@pytest.fixture
def sample_gdf() -> gpd.GeoDataFrame:
    """GeoDataFrame chua moi ca mau + 1 dong rong + 1 dong None + 1 dong trung voi 'ok'.

    Moi ca duoc dich sang canh nhau (cach 40 m) quanh SAMPLE_ORIGIN_UTM, CRS = 32648.
    """
    names, geoms = [], []
    for i, (name, wkt) in enumerate(SAMPLE_WKT.items()):
        g = affinity.translate(shapely.from_wkt(wkt), SAMPLE_ORIGIN_UTM[0] + i * 40, SAMPLE_ORIGIN_UTM[1])
        names.append(name)
        geoms.append(g)

    ok_geom = geoms[names.index("ok")]
    names += ["empty", "null", "duplicate_of_ok"]
    # Trung voi 'ok' nhung bat dau tu dinh khac -> chi bat duoc khi da normalize
    geoms += [shapely.from_wkt("POLYGON EMPTY"), None, shapely.Polygon(list(ok_geom.exterior.coords)[2:-1] + list(ok_geom.exterior.coords)[:3])]

    return gpd.GeoDataFrame({"name": names}, geometry=geoms, crs=32648)


@pytest.fixture(scope="session")
def output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture(scope="session")
def db_engine():
    """Ket noi SQLAlchemy toi PostGIS (thong tin lay tu .env). Skip neu khong ket noi duoc."""
    from sqlalchemy import create_engine, text

    load_dotenv(ROOT / ".env")
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@localhost:{os.environ.get('HOST_PORT', '5433')}/{os.environ['POSTGRES_DB']}"
    )
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception as exc:  # Docker tat, sai mat khau...
        pytest.skip(f"Khong ket noi duoc PostGIS: {exc}")
    yield engine
    engine.dispose()
