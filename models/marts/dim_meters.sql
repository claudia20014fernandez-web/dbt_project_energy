select
    meter_id,
    building_id,
    energy_type,
    installed_at
from {{ ref('stg_meters') }}
