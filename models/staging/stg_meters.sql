select
    meter_id,
    building_id,
    energy_type,
    cast(installed_at as date) as installed_at -- se transforma al tipo date
from {{ source('raw', 'meters') }}
