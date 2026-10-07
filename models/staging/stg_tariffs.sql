select
    energy_type,
    cast(valid_from as date) as valid_from,
    -- si no hay fecha de fin, la tarifa sigue vigente: usamos una fecha muy lejana
    coalesce(cast(valid_to as date), date '9999-12-31') as valid_to, -- coalesce da el primer valor que no sea NULL
    price_eur_kwh
from {{ source('raw', 'tariffs') }}
