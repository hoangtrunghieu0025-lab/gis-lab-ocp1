# Ngữ cảnh task: Hệ tọa độ & xử lý dữ liệu GIS khu OCP1

## 1. Tìm hiểu lý thuyết
- **Hệ tọa độ (CRS)**
  - WGS84 – EPSG:4326 (kinh/vĩ độ, đơn vị độ; mặc định của OSM/GPS)
  - UTM zone 48N – EPSG:32648 (hệ phẳng, đơn vị mét; phù hợp tính diện tích/khoảng cách khu vực miền Bắc VN)
  - VN-2000 (hệ quốc gia Việt Nam; ellipsoid WGS84 định vị lại, tham số chuyển đổi 7 tham số; các múi chiếu 3°/6° theo kinh tuyến trục từng tỉnh)
- **Mô hình dữ liệu**: vector (point, line, polygon) và raster (lưới pixel, độ phân giải, band)
- **Công cụ**: GeoPandas (Python), PostGIS (PostgreSQL extension), QGIS (desktop GIS)

## 2. Thực hành import dữ liệu
- Lấy dữ liệu OSM khu **OCP1** (Ocean Park 1 – Gia Lâm, Hà Nội)
- Import vào **QGIS** và **PostGIS**
- Chuyển CRS từ EPSG:4326 sang **EPSG:32648**

## 3. Viết test
- Test chuyển đổi CRS (4326 → 32648, kiểm tra tọa độ/đơn vị/sai số)
- Test làm sạch geometry (invalid, self-intersection, rỗng, trùng lặp, …)
- Kết quả xem được trên QGIS

## 4. Báo cáo
- Viết báo cáo tổng hợp lý thuyết, quy trình thực hiện, kết quả test, hình ảnh minh họa trên QGIS

## Tài liệu liên quan
- [THEORY.md](THEORY.md): báo cáo lý thuyết
- [REPORT.md](REPORT.md): báo cáo thực hành

## Tiến độ
- [x] 1. Tìm hiểu lý thuyết
- [x] 2. Import OSM OCP1 → QGIS, PostGIS, chuyển CRS
- [x] 3. Test chuyển CRS, làm sạch geometry
- [x] 4. Báo cáo
