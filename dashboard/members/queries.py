
years = "SELECT year_created FROM cooperative_member_view GROUP BY year_created;"

member = "SELECT month_created, gender, COUNT(DISTINCT id) as member_count FROM cooperative_member_view {} GROUP BY month_created, gender;"

collection = """
SELECT 
collection_year,
collection_month,
COUNT(DISTINCT id) as collection_count,
SUM(quantity) as weights_sum,
SUM(total_price * quantity) as amount_sum
FROM collection_view {} GROUP BY collection_year, collection_month;
"""

orders = "SELECT * FROM member_order_view {};"
