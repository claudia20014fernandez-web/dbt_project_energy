select
    building_id,
    name as building_name,
    city,
    building_type,
    area_m2,
    owner_group
from {{ source('raw', 'buildings') }}
