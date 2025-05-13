from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import Category, Product, Order, ProductCategory
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    OrderCreateSerializer,
)
from app.tasks import send_order_confirmation_email

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, pk=None):
        """
        GET /api/categories/{pk}/products/
        - Lọc theo price_min, price_max, sort_by
        """
        category = self.get_object()

        # Lấy tất cả product thuộc category đó
        qs = Product.objects.filter(
            productcategory__category=category
        ).distinct()

        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        if price_min:
            qs = qs.filter(productvariant__price__gte=price_min)
        if price_max:
            qs = qs.filter(productvariant__price__lte=price_max)

        sort_by = request.query_params.get('sort_by')
        if sort_by:
            qs = qs.order_by(sort_by)
        else: 
            qs.order_by('id')

        page = self.paginate_queryset(qs.distinct())
        serializer = ProductSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        GET /api/products/search/?q=...&category_id=...&price_min=...&in_stock=...&sort_by=...
        - full-text search trên name & description
        - filter theo category, price, in_stock
        - sort & pagination
        """
        q = request.query_params.get('q')

        # lọc theo tên và description
        if q:
            qs = Product.objects.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )
        else: qs = Product.objects.all()

        # lọc theo category
        cat = request.query_params.get('category_id')
        if cat:
            qs = qs.filter(productcategory__category=cat)

        # lọc theo giá
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        if price_min:
            qs = qs.filter(productvariant__price__gte=price_min)
        if price_max:
            qs = qs.filter(productvariant__price__lte=price_max)

        # lọc theo tồn kho
        in_stock = request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() in ['true', '1']:
                qs = qs.filter(productvariant__inventory__quantity__gt=0)
            else:
                qs = qs.filter(productvariant__inventory__quantity__lte=0)

        # sort
        sort_by = request.query_params.get('sort_by')
        if sort_by:
            qs = qs.order_by(sort_by)
        else: qs.order_by('id')

        page = self.paginate_queryset(qs.distinct())
        serializer = ProductSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        POST /api/orders/
        - Tạo order, tạo payment record
        - Xếp job gửi email bất đồng bộ
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        headers = self.get_success_headers(serializer.data)

        data = {
            "message": "Đơn hàng đã được tạo thành công",
            "order_id": order.id
        }

        # dispatch async email task
        send_order_confirmation_email.delay(order.id)

        return Response(
            data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'], url_path='send-confirmation')
    def send_confirmation(self, request, pk=None):
        """
        POST /api/orders/{pk}/send-confirmation/
        - Gửi lại email xác nhận (nếu cần)
        """
        order = self.get_object()
        send_order_confirmation_email.delay(order.id)
        return Response(
            {'status': 'email_queued'},
            status=status.HTTP_202_ACCEPTED
        )
