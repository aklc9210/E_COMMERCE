from django.db import models

class Province(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'provinces'

class District(models.Model):
    id = models.AutoField(primary_key=True)
    province = models.ForeignKey(Province, on_delete=models.RESTRICT)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'districts'
        unique_together = (('province', 'name'),)

class Commune(models.Model):
    id = models.AutoField(primary_key=True)
    district = models.ForeignKey(District, on_delete=models.RESTRICT)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'communes'
        unique_together = (('district', 'name'),)

class Account(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    ROLE_CHOICES = [
        ('customer', 'customer'),
        ('employee', 'employee'),
        ('admin', 'admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts'

class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    HOUSING_TYPE_CHOICES = [
        ('company', 'company'),
        ('home', 'home'),
        ('other', 'other'),
    ]
    housing_type = models.CharField(max_length=10, choices=HOUSING_TYPE_CHOICES, null=True, blank=True)

    class Meta:
        db_table = 'customers'

class Employee(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'employees'

class UserAddress(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    province = models.ForeignKey(Province, on_delete=models.RESTRICT)
    district = models.ForeignKey(District, on_delete=models.RESTRICT)
    commune = models.ForeignKey(Commune, on_delete=models.RESTRICT)
    address_line = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'user_addresses'

class Store(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'stores'

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'categories'

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'products'

class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_categories'
        unique_together = (('product', 'category'),)

class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=20, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'product_variants'

class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory'
        unique_together = (('store', 'variant'),)

class FeeType(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'fee_types'

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('pending','pending'),
        ('confirmed','confirmed'),
        ('shipped','shipped'),
        ('delivered','delivered'),
        ('cancelled','cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nearest_store_distance_km = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'

class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'

class OrderFee(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE, db_column='fee_type')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_fees'

class Voucher(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    VOUCHER_TYPE_CHOICES = [
        ('shipping','shipping'),
        ('discount','discount'),
    ]
    voucher_type = models.CharField(max_length=10, choices=VOUCHER_TYPE_CHOICES)

    class Meta:
        db_table = 'vouchers'

class UserVoucher(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='user_id')
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_vouchers'

class OrderVoucher(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_vouchers'
        unique_together = (('order', 'voucher'),)

class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    is_online = models.BooleanField()
    method = models.CharField(max_length=50)
    STATUS_CHOICES = [
        ('pending','pending'),
        ('completed','completed'),
        ('failed','failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
