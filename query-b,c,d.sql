-- Người dùng “assessment” với thông tin sau đã mua sản phẩm “KAPPA Women’s Sneakers” màu vàng, size 36, số lượng 1.
-- Viết truy vấn SQL để chèn đơn hàng này vào cơ sở dữ liệu.

-- ======== HÀM TÍNH KHOẢNG CÁCH TỪ GIỮA NGƯỜI MUA VÀ CỬA HÀNG GẦN NHẤT ========
DROP FUNCTION IF EXISTS haversine;
DELIMITER $$
CREATE FUNCTION haversine(
    lat1 DOUBLE, lon1 DOUBLE,
    lat2 DOUBLE, lon2 DOUBLE
) RETURNS DOUBLE DETERMINISTIC
BEGIN
  DECLARE r DOUBLE DEFAULT 6371;  -- bán kính Trái Đất (km)
  DECLARE dlat DOUBLE;
  DECLARE dlon DOUBLE;
  DECLARE a DOUBLE;
  DECLARE c_val DOUBLE;
  SET dlat = RADIANS(lat2 - lat1);
  SET dlon = RADIANS(lon2 - lon1);
  SET a = SIN(dlat/2)*SIN(dlat/2)
        + COS(RADIANS(lat1))*COS(RADIANS(lat2))*SIN(dlon/2)*SIN(dlon/2);
  SET c_val = 2 * ATAN2(SQRT(a), SQRT(1-a));
  RETURN r * c_val;
END$$
DELIMITER ;

-- ============ SP CHÈN DỮ LIỆU ORDER VÀO DB ==============
DROP PROCEDURE IF EXISTS sp_create_order_for_customer;
DELIMITER $$
CREATE PROCEDURE sp_create_order_for_customer(
	IN p_email           VARCHAR(150),
	IN p_product_name    VARCHAR(200),
	IN p_color           VARCHAR(50),
	IN p_size            VARCHAR(20),
	IN p_quantity        INT,
	IN p_voucher_code1    VARCHAR(50),
	IN p_voucher_code2    VARCHAR(50)
)
BEGIN
	DECLARE v_customer_id      INT;
	DECLARE v_variant_id       INT;
	DECLARE v_order_id         INT;
	DECLARE v_price_per_unit   DECIMAL(10,2);
	DECLARE v_total_amount     DECIMAL(12,2);
	DECLARE v_min_distance     DOUBLE;
	DECLARE v_store_id         INT;
	DECLARE v_user_lat         DECIMAL(9,6);
	DECLARE v_user_lon         DECIMAL(9,6);
	DECLARE v_vcid       INT;
	DECLARE v_disc_amt   DECIMAL(12,2);
	DECLARE v_amt DECIMAL(12,2);
	DECLARE v_pct DECIMAL(5,2);
	DECLARE v_amt2           DECIMAL(12,2); 
	DECLARE v_pct2           DECIMAL(5,2);

  -- Nếu có lỗi: rollback và báo ra ngoài
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- 1. Tìm customer_id
  SELECT c.id
    INTO v_customer_id
    FROM customers c
    JOIN accounts a ON a.id = c.account_id
   WHERE a.email = p_email
   LIMIT 1;
   
   SELECT CONCAT('customer_id=', v_customer_id) AS debug;

  -- 2. Tìm variant_id & price của sản phẩm
  SELECT pv.id, pv.price
    INTO v_variant_id, v_price_per_unit
    FROM product_variants pv
    JOIN products p ON p.id = pv.product_id
   WHERE p.name  = p_product_name
     AND pv.color = p_color
     AND pv.size  = p_size
   LIMIT 1;
   
   SELECT CONCAT('variant_id=', v_variant_id, ', price=', v_price_per_unit) AS debug;

  -- 3. Tính tổng tiền đơn: price × quantity
  SET v_total_amount = v_price_per_unit * p_quantity;
  

  -- 4. Lấy tọa độ của user_address 
  SELECT latitude, longitude
    INTO v_user_lat, v_user_lon
    FROM user_addresses
   WHERE customer_id = v_customer_id
   ORDER BY id DESC
   LIMIT 1;


  -- 5. Tìm kho gần nhất còn hàng & khoảng cách
  SELECT
    s.id,
    haversine(v_user_lat, v_user_lon, s.latitude, s.longitude) AS distance_km
  INTO v_store_id, v_min_distance
  FROM stores s
  JOIN inventory i ON i.store_id = s.id
  WHERE i.variant_id = v_variant_id
    AND i.quantity >= p_quantity
  ORDER BY distance_km
  LIMIT 1;
  
   SELECT CONCAT('nearest distance=', ROUND(v_min_distance,3)) AS debug;

  -- 6. Tạo order
  INSERT INTO orders
    (customer_id, status, total_amount, nearest_store_distance_km)
  VALUES
    (v_customer_id, 'pending', v_total_amount, ROUND(v_min_distance,3));
  SET v_order_id = LAST_INSERT_ID();
  
  SELECT CONCAT('total amount=', v_total_amount) AS debug;
  
    -- 7. Giảm số lượng tồn kho
  UPDATE inventory
     SET quantity = quantity - p_quantity
   WHERE store_id   = v_store_id
     AND variant_id = v_variant_id;


  -- 8. Tạo order_items
  INSERT INTO order_items
    (order_id, variant_id, quantity, price)
  VALUES
    (v_order_id, v_variant_id, p_quantity, v_price_per_unit);

  -- 9. Tính và tạo phí vận chuyển theo khung sát thực tế
  INSERT INTO order_fees
    (order_id, fee_type, amount)
  VALUES
    (
      v_order_id,
      'shipping',
      CASE
        WHEN v_min_distance <= 50   THEN 15000
        WHEN v_min_distance <= 200  THEN 20000
        WHEN v_min_distance <= 500  THEN 30000
        WHEN v_min_distance <= 1100 THEN 45000
        ELSE                           60000
      END
    );
    
	-- 10. Áp dụng mã giảm giá 1
	IF p_voucher_code1 IS NOT NULL THEN

	  SELECT id INTO v_vcid 
		FROM vouchers 
	   WHERE code = p_voucher_code1
	   LIMIT 1;

	  SELECT CONCAT('voucher1 id=', IFNULL(v_vcid,'NULL')) AS debug;

	  IF v_vcid IS NOT NULL THEN
		-- Lấy discount_amount và discount_percent
		SELECT discount_amount, discount_percent
		  INTO v_amt, v_pct
		  FROM vouchers 
		 WHERE id = v_vcid;

		SELECT CONCAT('voucher1 amt=', v_amt, ', pct=', v_pct) AS debug;

		SET v_disc_amt = IF(v_amt > 0, v_amt, v_total_amount * v_pct / 100);
		SELECT CONCAT('voucher1 disc_amt=', v_disc_amt) AS debug;

		INSERT INTO order_vouchers(order_id,voucher_id,discount_amount)
		VALUES(v_order_id, v_vcid, v_disc_amt);

		UPDATE orders
		   SET total_amount = total_amount - v_disc_amt
		 WHERE id = v_order_id;

		-- Load lại total_amount để debug
		SELECT total_amount AS debug_after_v1
		  FROM orders
		 WHERE id = v_order_id;

		UPDATE user_vouchers
		   SET used = TRUE
		 WHERE user_id = v_customer_id AND voucher_id = v_vcid;
	  END IF;
	END IF;

	-- 11. Áp mã giảm giá 2
	IF p_voucher_code2 IS NOT NULL THEN

	  SELECT CONCAT('before voucher2 total=', (SELECT total_amount FROM orders WHERE id = v_order_id)) AS debug;

	  SELECT id INTO v_vcid 
		FROM vouchers 
	   WHERE code = p_voucher_code2
	   LIMIT 1;

	  SELECT CONCAT('voucher2 id=', IFNULL(v_vcid,'NULL')) AS debug;

	  IF v_vcid IS NOT NULL THEN

		SELECT discount_amount, discount_percent
		  INTO v_amt2, v_pct2
		  FROM vouchers 
		 WHERE id = v_vcid;

		SELECT CONCAT('voucher2 amt=', v_amt2, ', pct=', v_pct2) AS debug;

		SET v_disc_amt = IF(v_amt2 > 0, v_amt2, v_total_amount * v_pct2 / 100);
		SELECT CONCAT('voucher2 disc_amt=', v_disc_amt) AS debug;

		INSERT INTO order_vouchers(order_id,voucher_id,discount_amount)
		VALUES(v_order_id, v_vcid, v_disc_amt);

		UPDATE orders
		   SET total_amount = total_amount - v_disc_amt
		 WHERE id = v_order_id;

		SELECT total_amount AS debug_after_v2
		  FROM orders
		 WHERE id = v_order_id;

		UPDATE user_vouchers
		   SET used = TRUE
		 WHERE user_id = v_customer_id AND voucher_id = v_vcid;
	  END IF;
	END IF;
  COMMIT;
END$$
DELIMITER ;

CALL sp_create_order_for_customer(
  'gu@gmail.com',
  'KAPPA Women''s Sneakers', 'yellow', '36', 1,
  'GIANGEEK10', 'FREESHIP'
);

-- =========== GIÁ TRỊ TRUNG BÌNH CỦA ORDER THEO THÁNG TRONG NĂM HIỆN TẠI ============
USE e_commerce;
SELECT 
	MONTH(created_at) as `month`,
	AVG(order_sum) as avg_order_value
	FROM (
		SELECT
			oi.order_id,
			SUM(oi.quantity * oi.price) AS order_sum,
			o.created_at
		FROM order_items oi
		JOIN orders o ON o.id = oi.order_id
		WHERE YEAR(o.created_at) = YEAR(CURDATE())
		GROUP BY oi.order_id
) AS t
GROUP BY MONTH(created_at)
ORDER BY `month`;


-- ============ ĐÁNH GIÁ TỶ LỆ RỜI BỎ CỦA KHÁCH HÀNG =============
WITH
  -- Khách hàng mua hàng trong khoảng thời gian 6–12 tháng
  prev_period AS (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
      AND created_at <  DATE_SUB(CURDATE(), INTERVAL  6 MONTH)
  ),

  -- Khách hàng mua hàng trong khoảng thời gian 6 tháng gần nhất
  recent_period AS (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
  )

SELECT
IFNULL(
	-- Số khách đã “churn”
	((SELECT COUNT(*) FROM prev_period p
		WHERE NOT EXISTS (
			 SELECT 1 FROM recent_period r
			 WHERE r.customer_id = p.customer_id
		)
	) * 100.0)
/ NULLIF(
	-- Tổng số khách trong prev_period (6-12 tháng)
	(SELECT COUNT(*) FROM prev_period), 0), 0
) AS churn_rate_percent;


