/* Database views -> Required to facilitate faster querying of Dashboard data.*/
/* cooperative_member view */
DROP VIEW IF EXISTS cooperative_member_view;
create view cooperative_member_view as
SELECT
cm.id as id,
cm.cooperative_id as cooperative_id,
cm.farmer_group_id as farmer_group,
cm.gender as gender,
cm.coop_role as coop_role,
YEAR(cm.create_date) as year_created,
MONTH(cm.create_date) as month_created,
r.id as region_id,
cm.district_id as district_id
FROM cooperative_member cm
LEFT JOIN district d on cm.district_id=d.id
LEFT JOIN region r on d.region_id=r.id;


/* collection view */
DROP VIEW IF EXISTS collection_view;
create view collection_view as
SELECT
cl.id as id,
cl.cooperative_id as cooperative_id,
cl.farmer_group_id as farmer_group,
cl.member_id as member_id,
cl.product_id as product_id,
cl.unit_price as unit_price,
cl.quantity as quantity,
(cl.unit_price * cl.quantity) as total_price,
YEAR(cl.collection_date) as collection_year,
MONTH(cl.collection_date) as collection_month,
r.id as region_id,
cm.district_id as district_id
FROM collection cl
INNER JOIN cooperative_member cm on cm.id=cl.member_id
LEFT JOIN district d on cm.district_id=d.id
LEFT JOIN region r on d.region_id=r.id;


/* member_order view */
DROP VIEW IF EXISTS member_order_view;
create view member_order_view as
SELECT
mo.id as id,
mo.cooperative_id as cooperative_id,
mo.member_id as member_id,
it.name as item_name,
oi.quantity as quantity,
oi.unit_price as unit_price,
(oi.unit_price * oi.quantity) as total_item_cost,
mo.status as order_status,
YEAR(mo.order_date) as year_ordered,
MONTH(mo.order_date) as month_ordered,
YEAR(mo.accept_date) as year_accepted,
MONTH(mo.accept_date) as month_accepted,
YEAR(mo.create_date) as year_created,
MONTH(mo.create_date) as month_created,
r.id as region_id,
cm.district_id as district_id
FROM member_order mo
INNER JOIN cooperative_member cm on cm.id=mo.member_id
LEFT JOIN order_item oi on mo.id=oi.order_id
LEFT JOIN item it on oi.item_id=it.id
LEFT JOIN district d on cm.district_id=d.id
LEFT JOIN region r on d.region_id=r.id;
