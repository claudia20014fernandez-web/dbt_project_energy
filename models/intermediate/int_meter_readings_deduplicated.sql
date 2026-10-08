-- Grano: 1 fila por contador y hora (meter_id + reading_ts).
-- Problema de origen: algunas lecturas se recargan al dia siguiente con un valor corregido.
-- Solucion: nos quedamos con la ultima carga de cada lectura usando una window function.
 
with ranked as (
 
    select
        *,
        row_number() over (
            partition by meter_id, reading_ts
            order by loaded_at desc
        ) as row_num
    from {{ ref('stg_meter_readings') }}
 
),
 
latest as (
 
    select
        meter_id,
        reading_ts,
        reading_date,
        kwh,
        loaded_at
    from ranked
    where row_num = 1
 
)
 
select
    *,
    case
        when kwh is null then 'missing'
        when kwh < 0 then 'negative'
        else 'ok'
    end as quality_flag
from latest
