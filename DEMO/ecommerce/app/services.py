import math
from typing import List, Dict, Any
from django.db.models import F
from .models import Store, Inventory
from rest_framework.exceptions import ValidationError


def haversine(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách giữa hai điểm (lat1, lon1) và (lat2, lon2) theo công thức Haversine.
    Trả về khoảng cách (km).

    Tham số:
      lat1, lon1: toạ độ điểm thứ nhất (radian)
      lat2, lon2: toạ độ điểm thứ hai (radian)
    """
    # Bán kính Trái đất ~ 6_371 km
    R = 6371.0

    # Chuyển độ sang radian
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Công thức haversine
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def select_stores_for_order(items_data: List[Dict[str, Any]], user_lat: float, user_lon: float):
    """
    Chọn store(s) phù hợp để lấy toàn bộ items_data.
    1. Kiểm tra xem có store nào chứa đủ tất cả variant hay không.
    2. Nếu không, dùng giải pháp greedy:
       - Sắp xếp các store theo khoảng cách tăng dần.
       - Lần lượt chọn store gần nhất có ít nhất một variant còn thiếu.
       - Dừng khi đã bao phủ tất cả variant.
    Trả về danh sách các dict:
      [
        {
          'store': Store instance,
          'distance': float,
          'variants': set(variant_ids)
        },
        ...
      ]
    """
    # Tập variant cần lấy
    all_variants = {item['variant'].id for item in items_data}

    # 1. Map store -> set variants it can cover
    store_cover = {}
    for store in Store.objects.all():
        covered = set()
        for item in items_data:
            exists = Inventory.objects.filter(
                store=store,
                variant=item['variant'],
                quantity__gte=item['quantity']
            ).exists()
            if exists:
                covered.add(item['variant'].id)
        if covered:
            store_cover[store.id] = {
                'store': store,
                'variants': covered,
                'distance': haversine(user_lat, user_lon, store.latitude, store.longitude)
            }

    # 2. Xem nếu có store đơn lẻ cover all
    for info in store_cover.values():
        if info['variants'] >= all_variants:
            return [{
                'store': info['store'],
                'distance': info['distance'],
                'variants': all_variants
            }]

    # 3. Greedy cover: sort stores by distance
    sorted_stores = sorted(store_cover.values(), key=lambda x: x['distance'])
    uncovered = set(all_variants)
    selected = []
    for info in sorted_stores:
        cover = info['variants'] & uncovered
        if cover:
            selected.append({
                'store': info['store'],
                'distance': info['distance'],
                'variants': cover
            })
            uncovered -= cover
            if not uncovered:
                break

    if uncovered:
        missing = []
        for vid in uncovered:
            var = next(item['variant'] for item in items_data if item['variant'].id == vid)
            missing.append(f"{var.product.name} - {var.size} - {var.color}")
        raise ValidationError(f"Không đủ tồn kho cho: {', '.join(missing)}")

    return selected
