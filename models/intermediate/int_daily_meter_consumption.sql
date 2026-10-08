-- Grano: 1 fila por contador y dia.
-- Solo suma las lecturas validas (quality_flag = 'ok') y calcula cuan completo esta el dia.
 
select

    r.meter_id,
    r.reading_date,
    sum(case when r.quality_flag = 'ok' then r.kwh end) as kwh,
    count(*) as readings_received,
    count(*) filter (where r.quality_flag = 'ok') as readings_valid,
    round(count(*) filter (where r.quality_flag = 'ok') / 24.0, 4) as completeness_ratio

from {{ ref('int_meter_readings_deduplicated') }} as r

-- inner join: descarta las lecturas "huerfanas" de contadores que no existen
inner join {{ ref('stg_meters') }} as m
    on r.meter_id = m.meter_id
group by r.meter_id, r.reading_date
