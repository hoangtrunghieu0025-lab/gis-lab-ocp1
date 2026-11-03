# Backlog lab — 03/11/2026 (1 ngày)

Mục tiêu: học nhanh CRS và dữ liệu không gian, làm trọn một vòng OSM → QGIS/PostGIS → chuyển CRS → test → báo cáo lab.
Tổng thời gian: khoảng 8h, chia thành các khối ngắn.

## Timeline

| Giờ | Khối | Việc | Đầu ra |
|---|---|---|---|
| 08:30 – 09:00 | Setup | Kiểm tra/cài QGIS, PostGIS (hoặc Docker `postgis/postgis`), môi trường Python | `postgis_full_version()` chạy, `import geopandas` ok |
| 09:00 – 10:30 | Lý thuyết | Đọc về EPSG:4326, EPSG:32648, VN-2000; vector vs raster; vai trò GeoPandas/PostGIS/QGIS | Ghi chú ngắn + bảng so sánh 3 hệ tọa độ |
| 10:30 – 11:30 | Lab 1 | Tải OSM khu OCP1 (QuickOSM hoặc osmnx): buildings, roads, POI | `data/ocp1_4326.gpkg` |
| 11:30 – 12:00 | Lab 2 | Mở dữ liệu trên QGIS, xem CRS của layer và project | Ảnh chụp QGIS |
| 13:30 – 14:30 | Lab 3 | Import vào PostGIS (ogr2ogr hoặc `to_postgis`), `ST_Transform` sang 32648 | Bảng `*_32648`, `ST_SRID = 32648` |
| 14:30 – 15:00 | Lab 4 | Mở lớp 32648 trong QGIS, so sánh chồng khớp với lớp 4326; so diện tích tính ở 2 hệ | Ảnh chụp + vài con số |
| 15:00 – 16:15 | Lab 5 | Viết test pytest: chuyển CRS (điểm mốc, round-trip, đơn vị mét) và làm sạch geometry (bowtie, rỗng, trùng) | `tests/` chạy pass |
| 16:15 – 16:45 | Lab 6 | Làm sạch dữ liệu thật (`ST_MakeValid`/`make_valid`), đếm lỗi trước/sau, xem trên QGIS | Bảng số lỗi + ảnh trước/sau |
| 16:45 – 17:30 | Báo cáo | Điền báo cáo lab theo [REPORT_OUTLINE.md](REPORT_OUTLINE.md) | `REPORT.md` |

## Checklist
- [ ] Setup môi trường
- [ ] Ghi chú lý thuyết
- [ ] Lab 1 – Tải OSM OCP1
- [ ] Lab 2 – Xem trên QGIS
- [ ] Lab 3 – PostGIS + chuyển CRS
- [ ] Lab 4 – So sánh 4326 vs 32648
- [ ] Lab 5 – Test CRS & làm sạch geometry
- [ ] Lab 6 – Làm sạch dữ liệu thật
- [ ] Báo cáo lab

## Nếu bị kẹt
- PostGIS cài lâu → dùng Docker, hoặc làm tạm bằng GeoPandas rồi bổ sung PostGIS sau
- VN-2000 chỉ cần nắm lý thuyết, không cần thực hành hôm nay
