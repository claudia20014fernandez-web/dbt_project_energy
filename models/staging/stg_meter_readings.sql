select
    meter_id,
    cast(reading_ts as timestamp) as reading_ts,
    cast(reading_ts as date) as reading_date, -- se divide el valor en dos, uno para la fecha y otro para la hora
    cast(kwh as double) as kwh,
    cast(loaded_at as timestamp) as loaded_at
from {{ source('raw', 'meter_readings') }}
