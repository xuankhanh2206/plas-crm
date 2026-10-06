# Pha Le Anh Sao — CRM / POS / Loyalty MVP

Đã import dữ liệu từ file kiểm kê PLAS:
- 682 mặt hàng thực tế
- PNT: 998 đơn vị
- NLB: 1.096 đơn vị
- HT: 8.687 đơn vị (được giữ riêng vì chưa xác định HT là cửa hàng hay kho)
- Giá vốn tồn theo bảng: 16.985.652.000 VNĐ
- Giá bán tồn theo bảng: 28.309.420.000 VNĐ

## Business rules đã code
- Định danh khách bằng số điện thoại; 1 số = 1 tài khoản.
- Khách không cung cấp số điện thoại vẫn có thể bán, nhưng không có Loyalty.
- Tích 1% trên GIÁ BÁN NIÊM YẾT, không phải giá sau giảm.
- 1 điểm = 1 VNĐ.
- Điểm không hết hạn.
- Không giới hạn số điểm sử dụng; có thể thanh toán 100% bằng điểm.
- Không dùng điểm đồng thời với voucher/khuyến mãi.
- Trả hàng/đổi hàng phải được xử lý bằng transaction, không sửa trực tiếp lịch sử.
- Điểm được ghi bằng Loyalty Ledger.
- Tồn kho tách PNT/NLB/HT.
- Hóa đơn lưu snapshot giá niêm yết.
- Không xóa dữ liệu giao dịch; có AuditLog.

## Chạy nhanh trên máy
1. Python 3.12+
2. `python -m venv .venv`
3. Windows: `.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. `python -m app.seed`
6. `uvicorn app.main:app --reload`
7. Mở `http://127.0.0.1:8000`
8. API docs: `http://127.0.0.1:8000/docs`

## PostgreSQL
Dùng `docker compose up --build`.
Trước khi đưa internet/public cần đổi SECRET_KEY, mật khẩu DB và bổ sung authentication/authorization production.

## Lưu ý dữ liệu nguồn
8 mặt hàng "Hàng phôi chưa mài" có giá bán niêm yết trống/0 trong file nguồn; hệ thống giữ nguyên dữ liệu, không tự bịa giá.


## Cập nhật v1.1 — Kho Hồng Tiến
HT đã được xác định là Hồng Tiến, kho tổng của hai cửa hàng.
- HT là kho, không phải cửa hàng bán lẻ.
- PNT và NLB là hai điểm bán.
- Có API điều chuyển HT→PNT, HT→NLB và PNT↔NLB.
- Mọi điều chuyển tạo InventoryTransaction và AuditLog.
- Giao diện nội bộ có tab Sản phẩm & tồn kho, Khách hàng, Điều chuyển kho.
- Có tài khoản seed `admin`, `sales_pnt`, `sales_nlb` để thực hành; mật khẩu đang là placeholder và phải đổi trước khi dùng thật.
