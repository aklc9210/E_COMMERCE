# Đồ Án E-commerce Backend (Django + DRF + Celery)

## 🎯 Giới thiệu đồ án

Dự án là một ứng dụng backend thương mại điện tử sử dụng **Django** và **Django REST Framework** (DRF), tích hợp **Celery** để xử lý các tác vụ bất đồng bộ như gửi email xác nhận đơn hàng.

**Các tính năng chính:**
- Quản lý danh mục sản phẩm và sản phẩm
- Đặt hàng trực tuyến
- Quản lý đơn hàng
- Áp dụng mã giảm giá, khuyến mãi
- Thanh toán và gửi mail xác nhận

## 🛠 Công nghệ sử dụng

- Django
- Django REST Framework (DRF)
- Celery + Redis (xử lý tác vụ bất đồng bộ)
- MySQL (cơ sở dữ liệu)
- Python-dotenv (quản lý biến môi trường)

## ⚙️ Hướng dẫn cài đặt
### 1. Clone repository và vào thư mục dự án:
```python
git clone <url_repository>
cd ecommerce-backend
```

### 2. Tạo virtual environment và kích hoạt:
```python
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Cài đặt các thư viện cần thiết:
```python
pip install -r requirements.txt
```

### 4. Thiết lập file .env:
Tạo file .env trong thư mục gốc với nội dung sau:
```
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Cơ sở dữ liệu
```
DATABASE_URL=mysql://username:password@localhost:3306/dbname
```

#### Email (SMTP - Gmail)
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

#### Celery (Redis)
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
### 5. Tạo database và migrate:
```
python manage.py migrate
```
### 6. Khởi động Redis Server (cho Celery):
Chắc chắn Redis đang chạy ở địa chỉ localhost:6379.

### 7. Khởi động Celery worker:
```
celery -A ecommerce worker -l info --pool=threads
```

### 8. Khởi động Django server:
```
python manage.py runserver
```

### 🧑‍💻 Tác giả
Họ tên: Nguyễn Thị Minh Thư

MSSV: N21DCCN082

Trường: Học viện Công nghệ Bưu chính Viễn thông cơ sở tại TPHCM
