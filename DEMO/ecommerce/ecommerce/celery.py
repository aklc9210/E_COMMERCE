import os
from celery import Celery

# Thiết lập biến môi trường Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

app = Celery('ecommerce')

# Lấy cấu hình từ Django settings, prefix tất cả key bắt đầu bằng CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm tasks.py trong tất cả app
app.autodiscover_tasks()