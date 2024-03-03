
years = "SELECT year_created FROM cooperative_member_view GROUP BY year_created;"

member = "SELECT gender FROM cooperative_member_view {} GROUP BY gender;"

collection = "SELECT * FROM collection_view {};"

orders = "SELECT * FROM member_order_view {};"
