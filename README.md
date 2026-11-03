# Lab GIS: Hệ tọa độ và xử lý dữ liệu OSM khu Ocean Park 1 (OCP1)

Bài lab gồm bốn phần: tìm hiểu các hệ tọa độ **WGS84 (EPSG:4326)**, **UTM 48N (EPSG:32648)** và **VN-2000**; import dữ liệu OpenStreetMap của khu Vinhomes Ocean Park 1 (Gia Lâm, Hà Nội) vào **QGIS** và **PostGIS**; chuyển dữ liệu sang EPSG:32648; viết **test** cho phần chuyển CRS và làm sạch geometry bằng GeoPandas.

**Kết quả chính:** 1819 tòa nhà đã được chuyển sang EPSG:32648. Bộ test có **30 test, tất cả đều pass**. Số liệu đo trên dữ liệu thật như sau:

| Phép so sánh | Kết quả |
|---|---|
| Diện tích tính trên 32648 so với giá trị chuẩn (tính trên ellipsoid) | −0,06% |
| Diện tích tính trên 3857 so với giá trị chuẩn | +15,3% |
| Cùng tòa nhà, giữa datum WGS84 và datum VN-2000 | lệch khoảng 224 m |

> **⚠️ Lưu ý về dữ liệu dùng để test phần làm sạch geometry.** Dữ liệu OSM thật của OCP1 **khá sạch**: cả 1819 polygon đều có `ST_IsValid = true`, không có geometry rỗng, không có bản ghi trùng. Chạy code làm sạch trên dữ liệu này thì **không có gì để sửa**, nên không chứng minh được code đúng. Vì vậy phải **tự thêm nhiễu**, tức tự tạo các ca geometry lỗi trong [tests/conftest.py](tests/conftest.py):
> - **4 ca không hợp lệ:** `bowtie` (tự cắt), `hole_outside` (lỗ nằm ngoài), `spike` (gai), `collapsed` (bẹp, diện tích bằng 0).
> - **1 ca hợp lệ nhưng có đỉnh lặp:** `repeated`.
> - **1 ca chuẩn:** `ok`.
> - **3 dòng nhiễu thêm:** geometry rỗng, giá trị `None`, và một bản sao của `ok` bắt đầu từ đỉnh khác.
>
> Các ca này được đặt ngay trong khu OCP1 (hệ EPSG:32648), nên mở `output/test_results.gpkg` trên QGIS sẽ thấy trực tiếp kết quả trước và sau khi làm sạch. Code làm sạch cũng được chạy trên dữ liệu thật để kiểm tra rằng nó **không làm hỏng** dữ liệu vốn đã hợp lệ (trước 1819, sau 1819).

---

## Thứ tự đọc gợi ý (dành cho mentor)

| # | File | Nội dung | Thời gian đọc |
|---|---|---|---|
| 1 | [THEORY.md](THEORY.md) | **Báo cáo lý thuyết.** Datum, ba kiểu tọa độ, CRS = datum + cách biểu diễn, mã EPSG, WGS84/UTM/VN-2000, vector/raster, tính hợp lệ geometry, GeoPandas/PostGIS/QGIS. Có sơ đồ, biểu đồ vẽ từ dữ liệu thật, và ảnh chụp QGIS | ~30 phút |
| 2 | [REPORT.md](REPORT.md) | **Báo cáo thực hành.** Các bước import, chuyển CRS, sự cố gặp phải và cách xử lý, kết quả test, ảnh chụp từng bước | ~15 phút |
| 3 | [src/](src/) và [tests/](tests/) | **Code và bộ test** (pytest) | ~15 phút |
| 4 | [TASK.md](TASK.md) | Mô tả nhiệm vụ ban đầu | 2 phút |

Nếu chỉ có 5 phút, hãy xem các phần sau trong [THEORY.md](THEORY.md):
- **mục 4**: bảng datum × kiểu tọa độ;
- **mục 8.2**: hình minh họa lệch datum 224 m;
- **mục 9.1**: so sánh diện tích giữa các hệ.

---

## Cấu trúc thư mục

```text
.
├── README.md               ← file này
├── THEORY.md               ← báo cáo lý thuyết
├── REPORT.md               ← báo cáo thực hành (import, CRS, test)
├── TASK.md                 ← mô tả nhiệm vụ
│
├── figures/                ← hình cho THEORY.md
│   ├── svg_*.svg           sơ đồ khái niệm
│   ├── fig_*.png           biểu đồ tính từ dữ liệu OCP1 (pyproj, shapely, matplotlib)
│   └── shot_*.png          ảnh chụp QGIS
├── report/
│   ├── img/                ảnh chụp từng bước cho REPORT.md
│   └── evidence/           output dạng văn bản: kết quả pytest, truy vấn PostGIS
│
├── src/
│   ├── crs.py              chuyển CRS (4326 ↔ 32648), kiểm tra lon/lat, diện tích trắc địa
│   └── clean.py            làm sạch geometry: bỏ rỗng, make_valid, chỉ giữ polygon, bỏ điểm lặp, bỏ trùng
├── tests/
│   ├── conftest.py         dữ liệu mẫu (gồm các ca geometry lỗi tự tạo), kết nối PostGIS
│   ├── test_crs.py         test chuyển CRS: điểm mốc, round-trip, diện tích, đảo trục
│   ├── test_clean.py       test làm sạch geometry: bowtie, rỗng, trùng, điểm lặp, xuất file cho QGIS
│   └── test_postgis.py     test trên dữ liệu thật trong PostGIS (tự skip nếu DB không chạy)
│
├── data/ocp1_4326.gpkg     dữ liệu OSM gốc: 1819 tòa nhà, EPSG:4326
├── output/test_results.gpkg kết quả test, mở bằng QGIS để xem trước và sau khi làm sạch
├── ocp.qgz                 project QGIS
│
├── docker-compose.yml      PostGIS 17 + PostGIS 3.5, cổng 5433
├── .env.example            mẫu cấu hình DB (copy thành .env)
├── requirements.txt
└── pytest.ini
```

---

## Môi trường đã dùng

| Thành phần | Phiên bản |
|---|---|
| QGIS | 3.44.15 + plugin QuickOSM 2.5.4 |
| PostgreSQL / PostGIS | 17.5 / 3.5.2 (Docker image `postgis/postgis:17-3.5`) |
| Python | 3.13, geopandas 1.2, shapely 2.2, pyproj 3.8 (PROJ 9.8), pytest |

## Ghi chú

- **Bảo mật:** file `.env` chứa mật khẩu database nên **không được đưa lên git**. Repo chỉ có file mẫu `.env.example`.
- **Cần đối chiếu:** bộ 7 tham số chuyển đổi VN-2000 trong THEORY.md mục 7.2 lấy theo PROJ/EPSG. Dấu và quy ước xoay cần đối chiếu với Thông tư 973/2001/TT-TCĐC.
- **Nguồn dữ liệu:** © OpenStreetMap contributors, phát hành theo giấy phép ODbL.
