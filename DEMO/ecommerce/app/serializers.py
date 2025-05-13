# serializers.py
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import *
from .services import haversine, select_stores_for_order
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description']

class ProductDetailSerializer(serializers.ModelSerializer):
    variants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    categories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'variants', 'categories']

class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    color = serializers.CharField(max_length=50)
    size = serializers.CharField(max_length=20)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    shipping_address_id = serializers.IntegerField(write_only=True)
    payment_method      = serializers.CharField(write_only=True)
    shipping_fee_type   = serializers.CharField(write_only=True)
    voucher_code1       = serializers.CharField(write_only=True, required=False, allow_null=True)
    voucher_code2       = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'customer',
            'items',
            'shipping_address_id',
            'payment_method',
            'shipping_fee_type',
            'voucher_code1',
            'voucher_code2',
        ]

    def create(self, validated_data):
        with transaction.atomic():

            # 1. Lấy raw items từ front-end
            raw_items  = validated_data.pop('items')
            addr_id    = validated_data.pop('shipping_address_id')
            method     = validated_data.pop('payment_method')
            fee_code   = validated_data.pop('shipping_fee_type')
            v1         = validated_data.pop('voucher_code1', None)
            v2         = validated_data.pop('voucher_code2', None)
            customer   = validated_data['customer']

            # 2. Lấy toạ độ
            try:
                addr = UserAddress.objects.get(id=addr_id, customer=customer)
            except UserAddress.DoesNotExist:
                raise ValidationError("Địa chỉ giao hàng không tồn tại")
            lat, lon = addr.latitude, addr.longitude

            # 3. Chuyển raw_items thành items chứa variant, quantity, price
            items = []
            for i, raw in enumerate(raw_items, start=1):
                prod_id = raw.get('product_id')
                color   = raw.get('color')
                size    = raw.get('size')
                qty     = raw.get('quantity', 0)

                if not (prod_id and color is not None and size is not None):
                    raise ValidationError(f"Item #{i} thiếu thông tin product_id/color/size")
                if qty <= 0:
                    raise ValidationError(f"Số lượng của item #{i} phải lớn hơn 0")

                variant = ProductVariant.objects.filter(
                    product_id=prod_id,
                    color=color,
                    size=size
                ).first()

                if not variant:
                    raise ValidationError(
                        f"Không tìm thấy variant cho sản phẩm {prod_id} "
                        f"(color={color}, size={size})"
                    )

                items.append({
                    'variant': variant,
                    'quantity': qty,
                    'price': variant.price,
                })

            # 4. Chọn store(s) phù hợp
            allocations = select_stores_for_order(items, lat, lon)
            max_dist    = max(a['distance'] for a in allocations)

            # 5. Tạo Order mới
            order = Order.objects.create(
                customer=customer,
                status='pending',
                total_amount=Decimal('0.00'),
                nearest_store_distance_km=round(max_dist, 3)
            )

            # 6. Tạo OrderItem & cập nhật tồn kho, tính tổng tiền hàng
            total = Decimal('0.00')
            for alloc in allocations:
                store = alloc['store']
                for vid in alloc['variants']:
                    it = next(i for i in items if i['variant'].id == vid)
                    oi = OrderItem.objects.create(
                        order=order,
                        variant=it['variant'],
                        quantity=it['quantity'],
                        price=it['price']
                    )
                    total += oi.quantity * oi.price
                    inv = Inventory.objects.get(store=store, variant=it['variant'])
                    inv.quantity -= it['quantity']
                    inv.save()

            # 7. Tính phí vận chuyển
            try:
                ft = FeeType.objects.get(code=fee_code)
            except FeeType.DoesNotExist:
                raise ValidationError("Mã phí vận chuyển không hợp lệ")

            if max_dist <= 50:
                ship_amt = Decimal('15000')
            elif max_dist <= 200:
                ship_amt = Decimal('20000')
            elif max_dist <= 500:
                ship_amt = Decimal('30000')
            else:
                ship_amt = Decimal('45000')

            OrderFee.objects.create(order=order, fee_type=ft, amount=ship_amt)
            total += ship_amt

            # 8. Áp voucher: chỉ có 1 voucher cho ship và 1 voucher cho order
            for code in (v1, v2):
                if not code:
                    continue
                try:
                    v = Voucher.objects.get(
                        code=code,
                        valid_from__lte=timezone.localdate(),
                        valid_to__gte=timezone.localdate()
                    )
                except Voucher.DoesNotExist:
                    raise ValidationError(f"Voucher `{code}` không hợp lệ")
                uv = UserVoucher.objects.filter(user=customer, voucher=v, used=False).first()
                if not uv:
                    raise ValidationError(f"Voucher `{code}` đã dùng hoặc không phù hợp")

                disc = v.discount_amount or (total * v.discount_percent / Decimal('100'))
                disc = min(disc, total)
                OrderVoucher.objects.create(order=order, voucher=v, discount_amount=disc)
                total -= disc
                uv.used = True
                uv.save()

            # 9. Cập nhật tổng tiền và tạo bản ghi thanh toán
            order.total_amount = total
            order.save()

            Payment.objects.create(
                order=order,
                is_online=True,
                method=method,
                status='pending',
                amount=total
            )

            return order

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
