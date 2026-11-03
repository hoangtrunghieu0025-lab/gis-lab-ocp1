import os
from pathlib import Path

import geopandas as gpd
import pytest
import shapely
from dotenv import load_dotenv
from shapely import affinity

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

SAMPLE_ORIGIN_UTM = (598_000.0, 2_321_000.0)

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
    return (105.945, 20.995)


@pytest.fixture
def sample_geoms() -> dict:
    return {name: shapely.from_wkt(wkt) for name, wkt in SAMPLE_WKT.items()}


@pytest.fixture
def sample_gdf() -> gpd.GeoDataFrame:
    names, geoms = [], []
    for i, (name, wkt) in enumerate(SAMPLE_WKT.items()):
        g = affinity.translate(shapely.from_wkt(wkt), SAMPLE_ORIGIN_UTM[0] + i * 40, SAMPLE_ORIGIN_UTM[1])
        names.append(name)
        geoms.append(g)

    ok_geom = geoms[names.index("ok")]
    names += ["empty", "null", "duplicate_of_ok"]
    geoms += [shapely.from_wkt("POLYGON EMPTY"), None, shapely.Polygon(list(ok_geom.exterior.coords)[2:-1] + list(ok_geom.exterior.coords)[:3])]

    return gpd.GeoDataFrame({"name": names}, geometry=geoms, crs=32648)


@pytest.fixture(scope="session")
def output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture(scope="session")
def db_engine():
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
    except Exception as exc:
        pytest.skip(f"Khong ket noi duoc PostGIS: {exc}")
    yield engine
    engine.dispose()
