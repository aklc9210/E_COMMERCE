# app/tasks.py

import datetime
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from django.conf import settings
from .models import Order

@shared_task
def send_order_confirmation_email(order_id):
    try:
        # Lấy order kèm các quan hệ cần thiết
        order = (
            Order.objects
            .select_related('customer__account')
            .prefetch_related('orderitem_set__variant__product',
                              'ordervoucher_set__voucher',
                              'payment_set')
            .get(id=order_id)
        )

        # Tiêu đề
        subject = f"Xác nhận đơn hàng #{order.id}"

        # 1. Chi tiết sản phẩm
        items = order.orderitem_set.all()
        lines = []
        for item in items:
            prod = item.variant.product
            lines.append(
                f"- {prod.name} (Màu: {item.variant.color}, Size: {item.variant.size}) "
                f"x{item.quantity} @ {item.price:,}₫ = {item.quantity * item.price:,}₫"
            )
        items_detail = "\n".join(lines)

        # 2. Thông tin voucher (nếu có)
        vouchers = order.ordervoucher_set.all()
        if vouchers:
            vlines = []
            for ov in vouchers:
                code = ov.voucher.code
                amt  = ov.discount_amount
                vlines.append(f"{code}: -{amt:,}₫")
            vouchers_detail = "\n".join(vlines)
        else:
            vouchers_detail = "Không có"

        # 3. Thông tin thanh toán
        payment = order.payment_set.last()
        payment_detail = (
            f"Phương thức: {payment.method}\n"
            f"Trạng thái: {payment.status}\n"
            f"Số tiền: {payment.amount:,}₫"
        )

        # 4. Ước tính thời gian giao hàng
        dist = order.nearest_store_distance_km or 0

        # tùy khoảng cách <100km → 2 ngày, còn lại 3 ngày
        days = 2 if dist <= 100 else 3
        eta_date = timezone.localdate() + datetime.timedelta(days=days)
        eta_detail = f"Ước tính giao hàng trong {days} ngày (trước {eta_date})"

        # 5. Trạng thái đơn hàng
        status_detail = f"Trạng thái hiện tại: {order.status}"

        # Nội dung email
        message = (
            f"Xin chào {order.customer.full_name or order.customer.account.email},\n\n"
            f"Bạn vừa đặt thành công đơn hàng #{order.id} vào {order.created_at:%d/%m/%Y %H:%M}.\n\n"
            f"--- Chi tiết đơn hàng ---\n"
            f"{items_detail}\n\n"
            f"Voucher áp dụng:\n{vouchers_detail}\n\n"
            f"--- Thông tin thanh toán ---\n"
            f"{payment_detail}\n\n"
            f"{eta_detail}\n"
            f"{status_detail}\n\n"
            f"Cảm ơn bạn đã tin tưởng và sử dụng dịch vụ của chúng tôi!\n"
        )

        # Gửi mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.account.email],
            fail_silently=False,
        )
        return True

    except Order.DoesNotExist:
        return False

