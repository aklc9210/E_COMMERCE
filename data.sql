-- 1. provinces
INSERT INTO provinces (name) VALUES
('Bắc Kạn'),('Hà Nội'),('Hồ Chí Minh'),('Đà Nẵng');

-- 2. districts
INSERT INTO districts (province_id,name) VALUES
(1,'Ba Bể'),(2,'Hoàn Kiếm'),(2,'Ba Đình'),(3,'Quận 1'),(3,'Quận 3'),(4,'Hải Châu');

-- 3. communes
INSERT INTO communes (district_id,name) VALUES
(1,'Phúc Lộc'),(2,'Phúc Tân'),(3,'Cống Vị'),(4,'Bến Nghé'),(5,'Vĩnh Trung');

-- 4. accounts
INSERT INTO accounts (email, password_hash, role, created_at, updated_at)
VALUES 
  ('tranva@example.com','$2b$12$def...','employee', NOW(), NOW()),
  ('lethanh@xyz.com','$2b$12$ghi...','customer', NOW(), NOW()),
  ('nguyenvan@xyz.com','$2b$12$jkl...','employee', NOW(), NOW());

-- 5. customers
INSERT INTO customers (account_id,full_name,phone,housing_type) VALUES
(2,'Lê Thanh','0912345678','company');

-- 6. employees
INSERT INTO employees (account_id,full_name,position,department) VALUES
(1,'Trần Văn A','Sale Manager','Sales'),
(3,'Nguyễn Văn B','Warehouse Staff','Logistics');

-- 7. user_addresses
INSERT INTO user_addresses (customer_id,province_id,district_id,commune_id,address_line,latitude,longitude) VALUES
(1,3,4,4,'123 Nguyễn Huệ',10.773454,106.700983);

-- 8. stores
INSERT INTO stores (name,location,latitude,longitude) VALUES
('Warehouse A','Hà Nội, Quận Hoàn Kiếm',21.028511,105.804817),
('Warehouse B','Hồ Chí Minh, Quận 1',10.776530,106.700981),
('Warehouse C','Đà Nẵng, Hải Châu',16.054407,108.202164);

-- 9. categories
INSERT INTO categories (name,description,parent_id) VALUES
('Giày','Danh mục giày dép',NULL),
('Sneakers','Giày thể thao',1),
('Boots','Giày cổ cao',1),
('Adidas','Thương hiệu Adidas',NULL),
('Nike','Thương hiệu Nike',NULL);

-- 10. products
INSERT INTO products (name,description) VALUES
('KAPPA Women''s Sneakers','Giày bata nữ màu vàng'),
('Adidas Ultraboost','Giày thể thao Adidas Ultraboost'),
('Nike Air Max','Giày Nike Air Max'),
('Timberland Boots','Giày boots cổ cao Timberland');

-- 11. product_categories
INSERT INTO product_categories (product_id,category_id) VALUES
(1,2),(2,2),(3,2),(4,3),(2,4),(3,5);

-- 12. product_variants
INSERT INTO product_variants (product_id,color,size,price) VALUES
(1,'yellow','36',980000.00),
(1,'black','37',990000.00),
(2,'white','40',2500000.00),
(3,'red','42',2300000.00),
(4,'brown','41',3200000.00);

-- 13. inventory
INSERT INTO inventory (store_id,variant_id,quantity) VALUES
(1,1,5),(1,2,3),(2,3,10),(2,4,7),(3,5,4);

-- 14. fee_types
INSERT INTO fee_types (code,name,description) VALUES
('shipping','Shipping Fee','Phí giao hàng theo km'),
('insurance','Insurance Fee','Phí bảo hiểm hàng hóa'),
('gift_wrap','Gift Wrap','Phí gói quà');

-- 15. orders
INSERT INTO orders (customer_id,status,total_amount,nearest_store_distance_km, created_at, updated_at) VALUES
(1,'confirmed',2500000.00,2.50, NOW(), now());

-- 16. order_items
INSERT INTO order_items (order_id,variant_id,quantity,price) VALUES
(1,3,2,2500000.00);

-- 17. order_fees
INSERT INTO order_fees (order_id,fee_type,amount) VALUES
(1,'shipping',15000.00),(1,'gift_wrap',10000.00);

-- 18. vouchers
INSERT INTO vouchers (code,description,discount_amount,discount_percent,valid_from,valid_to,voucher_type) VALUES
('GIANGEEK10','Giảm 10% cho đơn ≥ 1 triệu',0.00,10.00,'2025-06-01','2025-06-30','discount'),
('FREESHIP','Miễn phí vận chuyển',0.00,0.00,'2025-05-01','2025-05-31','shipping'),
('ADIDISCOUNT','Giảm 5% cho Adidas',0.00,5.00,'2025-07-01','2025-07-31','discount');

-- 19. order_vouchers
INSERT INTO order_vouchers (order_id,voucher_id,discount_amount) VALUES
(1,3,125000.00);

-- 20. payments
INSERT INTO payments (order_id,is_online,method,status,transaction_id,amount,paid_at) VALUES
(1,FALSE,'COD','pending',NULL,2525000.00,now());

-- 21. user_vouchers
INSERT INTO user_vouchers (user_id, voucher_id, used, assigned_at)
VALUES
  (1, 1, FALSE, CURRENT_TIMESTAMP),   -- GIANGEEK10
  (1, 2, FALSE, CURRENT_TIMESTAMP)  -- FREESHIP