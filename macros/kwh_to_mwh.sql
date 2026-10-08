{% macro kwh_to_mwh(column_name, decimals=2) %}
    round({{ column_name }} / 1000.0, {{ decimals }})
{% endmacro %}
