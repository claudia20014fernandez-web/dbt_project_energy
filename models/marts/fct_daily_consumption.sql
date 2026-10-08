{{
    config(
        materialized='incremental',
        unique_key=['meter_id', 'reading_date'],
        incremental_strategy='delete+insert'
    )
}}
 
-- Grano: 1 fila por contador y dia. Incluye el coste en euros segun la tarifa vigente ese dia.
 
with daily as (
 
    select * from {{ ref('int_daily_meter_consumption') }}
 
    {% if is_incremental() %}
    -- Solo reprocesamos los ultimos 3 dias (por si llegan lecturas tarde)
    where reading_date >= (select max(reading_date) - interval 3 day from {{ this }})
    {% endif %}
 
)
 
select
    d.meter_id,
    m.building_id,
    m.energy_type,
    d.reading_date,
    d.kwh,
    d.kwh * t.price_eur_kwh as cost_eur,
    d.completeness_ratio
from daily as d
inner join {{ ref('stg_meters') }} as m
    on d.meter_id = m.meter_id
left join {{ ref('stg_tariffs') }} as t
    on m.energy_type = t.energy_type
    and d.reading_date between t.valid_from and t.valid_to
