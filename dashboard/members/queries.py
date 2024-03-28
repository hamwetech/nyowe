
years = "SELECT year_created FROM cooperative_member_view GROUP BY year_created;"

member = "SELECT month_created, gender, COUNT(DISTINCT id) as member_count FROM cooperative_member_view {} GROUP BY month_created, gender;"

collection = "SELECT * FROM collection_view {};"

orders = "SELECT * FROM member_order_view {};"
