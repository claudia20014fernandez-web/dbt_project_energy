select
    b.building_id,
    b.building_name,
    b.city,
    b.building_type,
    g.building_type_label,
    g.sector_group,
    b.area_m2,
    b.owner_group
from {{ ref('stg_buildings') }} as b

left join {{ ref('building_type_groups') }} as g
    on b.building_type = g.building_type
