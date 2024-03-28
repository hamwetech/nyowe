
years = "SELECT year_created FROM cooperative_member_view GROUP BY year_created;"

member = """
SELECT 
month_created, 
gender, 
COUNT(DISTINCT id) as member_count 
FROM cooperative_member_view {} GROUP BY month_created, gender;
"""

collection_month = """
SELECT 
collection_year,
collection_month,
COUNT(DISTINCT id) as collection_count,
SUM(quantity) as weights_sum,
SUM(total_price) as amount_sum
FROM collection_view {} GROUP BY collection_year, collection_month;
"""

collection_product = """
SELECT 
collection_year,
product_name,
SUM(quantity) as weights_sum,
SUM(total_price) as amount_sum
FROM collection_view {} GROUP BY collection_year, product_name;
"""

orders_month = """
SELECT 
year_ordered,
month_ordered,
COUNT(DISTINCT id) as order_count,
SUM(total_item_cost) as amount_sum
FROM member_order_view {} GROUP BY year_ordered, month_ordered;
"""

orders_items = """
SELECT 
year_ordered,
item_name,
COUNT(DISTINCT id) as item_count,
SUM(total_item_cost) as amount_sum
FROM member_order_view {} GROUP BY year_ordered, item_name;
"""