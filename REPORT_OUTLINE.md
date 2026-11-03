# Khung báo cáo lab

**Lab:** Hệ tọa độ và xử lý dữ liệu OSM khu Ocean Park 1 (OCP1)
**Ngày:** 03/11/2026

## 1. Mục tiêu
- 3–4 gạch đầu dòng: hiểu CRS, import OSM, chuyển sang EPSG:32648, test và làm sạch geometry

## 2. Môi trường
- Phiên bản QGIS, PostgreSQL/PostGIS, Python, GeoPandas

## 3. Lý thuyết tóm tắt
- Bảng so sánh WGS84 (4326) / UTM 48N (32648) / VN-2000: loại, đơn vị, khi nào dùng
- Vector vs raster: 3–4 dòng
- GeoPandas / PostGIS / QGIS: mỗi công cụ 1–2 dòng + hàm chính đã dùng

## 4. Các bước thực hiện
Mỗi lab ghi: lệnh/code chính → kết quả → ảnh chụp
- Lab 1: Tải OSM OCP1
- Lab 2: Xem trên QGIS
- Lab 3: Import PostGIS + `ST_Transform` sang 32648
- Lab 4: So sánh 4326 vs 32648 (chồng khớp, diện tích)
- Lab 5: Test chuyển CRS và làm sạch geometry (output pytest)
- Lab 6: Làm sạch dữ liệu thật (số lỗi trước/sau)

## 5. Kết quả & nhận xét
- Điều rút ra, vì sao phải dùng hệ phẳng (mét) khi đo đạc
- Lỗi gặp phải và cách xử lý

## 6. Tham khảo
