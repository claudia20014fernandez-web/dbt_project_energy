# dbt_project_energy
# Mini proyecto dbt de analitica energetica
 
Proyecto de aprendizaje con dbt Core + DuckDB que modela el consumo energetico de un
portfolio de edificios (electricidad y gas) en capas, con tests, documentacion,
snapshots, cargas incrementales y una capa semantica de metricas.
 
> **Datos sinteticos.** Los datos los genera `scripts/load_raw_data.py` e incluyen
> problemas de calidad plantados a proposito (duplicados, nulos, negativos y lecturas
> de contadores inexistentes). No son datos reales de ningun cliente.
 
## Arquitectura
 
```
raw (DuckDB)  ->  staging  ->  intermediate  ->  marts  ->  semantic layer (MetricFlow)
 buildings        stg_*        int_*              dim_*      total_kwh
 meters                                           fct_*      total_cost_eur
 meter_readings                                   mart_*     cost_per_kwh
 tariffs
```
 
| Capa | Materializacion | Que hace |
|---|---|---|
| staging | view | Renombra, castea tipos. Un modelo por tabla de origen. Sin logica de negocio |
| intermediate | view | Deduplica lecturas, marca calidad, agrega a diario |
| marts | table / incremental | Dimensiones, hechos y tablas listas para negocio |
 
## Decisiones de diseno
 
- **Deduplicacion con `row_number()`**: algunas lecturas se recargan con valor corregido; se queda la ultima carga.
- **Flag de calidad** (`ok`, `missing`, `negative`) en lugar de borrar filas: el dato malo queda trazable.
- **Hechos incrementales** con ventana de 3 dias para absorber lecturas tardias.
- **Tarifas con vigencia**: el coste se calcula con el precio vigente cada dia (join por rango de fechas).
- **Test con `severity: warn`** para las lecturas huerfanas: es un problema conocido del origen que no debe parar el pipeline.
- **Snapshot (SCD tipo 2)** de edificios para conservar el historico de cambios de propietario y superficie.
 
## Como ejecutarlo
 
```bash
python -m venv venv
source venv/bin/activate          # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/load_raw_data.py   # carga los datos en bruto
dbt deps                          # instala dbt_utils
dbt build                         # seeds + modelos + tests + snapshot
dbt docs generate && dbt docs serve
mf query --metrics total_kwh,total_cost_eur --group-by metric_time__month
```
 
## Limitaciones
 
- Datos sinteticos y de pequeño volumen.
- DuckDB local: en produccion se usaria un warehouse (Snowflake, BigQuery...) y un orquestador.
- La capa semantica cubre un unico modelo semantico.

