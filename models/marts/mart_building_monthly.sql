-- Grano: 1 fila por edificio y mes.
 
with monthly as (
 
    select
        building_id,
        date_trunc('month', reading_date) as month,
        sum(kwh) filter (where energy_type = 'electricity') as electricity_kwh,
        sum(kwh) filter (where energy_type = 'gas') as gas_kwh,
        sum(kwh) as total_kwh,
        sum(cost_eur) as total_cost_eur
    from {{ ref('fct_daily_consumption') }}
    group by building_id, date_trunc('month', reading_date)
 
),
 
enriched as (
 
    select
        m.*,
        b.building_name,
        b.building_type,
        b.area_m2,
        m.total_kwh / b.area_m2 as kwh_per_m2
    from monthly as m
    inner join {{ ref('dim_buildings') }} as b
        on m.building_id = b.building_id
 
)
 
select
    *,
    {{ kwh_to_mwh('total_kwh') }} as total_mwh,
    -- variacion respecto al mes anterior del mismo edificio
    total_kwh - lag(total_kwh) over (partition by building_id order by month)
        as kwh_change_vs_prev_month,
    round(
        (
            total_kwh
            / nullif(lag(total_kwh) over (partition by building_id order by month), 0)
            - 1
        ) * 100,
        2
    ) as pct_change_vs_prev_month,
    -- ranking de eficiencia dentro de su tipo de edificio (1 = menos kWh por m2)
    rank() over (partition by building_type, month order by kwh_per_m2)
        as efficiency_rank_in_type
from enriched
