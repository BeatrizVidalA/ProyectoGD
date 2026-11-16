"""Pruebas de decisiones peligrosas con registros reales y errores simulados."""
import io
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import duckdb
import pandas as pd
from plataforma.ingesta import Entradas, descargar, sha256
from plataforma.normalizacion import normalizar, clasificar, ESQUEMAS
from plataforma.almacen import construir_estrella, divulgacion, metricas_divulgacion, cargar_externas, trazar
from plataforma.externas import integrar
from plataforma.auditoria import balance_filas, detalle_balance


class PlataformaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = ROOT.parent / "COVID-19/csse_covid_19_data"
        cls.temporales = ROOT / "data/quality/pruebas_unitarias"
        cls.temporales.mkdir(parents=True, exist_ok=True)

    def test_cinco_esquemas_y_rechazo_de_columnas_inesperadas(self):
        for etapa, columnas in ESQUEMAS.items():
            self.assertEqual(clasificar(columnas), etapa)
        with self.assertRaises(ValueError):
            clasificar(ESQUEMAS[5] | {"campo_desconocido"})

    def test_fips_y_timestamp_se_preservan(self):
        p = self.original / "csse_covid_19_daily_reports/03-22-2020.csv"
        d, _ = normalizar(p, sha256(p))
        raw = pd.read_csv(p, dtype="string", keep_default_na=False)
        self.assertEqual(d.fips.iloc[0], raw.FIPS.iloc[0])
        self.assertEqual(d.ultima_actualizacion_original.iloc[0], raw.Last_Update.iloc[0])
        self.assertEqual(str(d.fecha_reporte.iloc[0]), "2020-03-22")

    def test_cache_invalido_no_se_sobrescribe_y_sin_red_no_omite(self):
        with TemporaryDirectory(dir=self.temporales) as tmp:
            e = Entradas(tmp, ROOT / "clon_ausente", sin_red=True)
            with self.assertRaises(FileNotFoundError):
                e.obtener("01-22-2020.csv", "diario")
            p = Path(tmp) / "data/raw/daily_reports/01-22-2020.csv"
            p.parent.mkdir(parents=True)
            p.write_bytes(b"")
            with self.assertRaises(ValueError):
                e.obtener(p.name, "diario")
            self.assertEqual(p.read_bytes(), b"")

    def test_404_falla_sin_reintentar_y_sin_crear_archivo(self):
        with TemporaryDirectory(dir=self.temporales) as tmp:
            p = Path(tmp) / "nunca.csv"
            with patch("plataforma.ingesta.urlopen", side_effect=HTTPError("https://ejemplo", 404, "not found", None, io.BytesIO())) as request:
                with self.assertRaises(HTTPError):
                    descargar("https://ejemplo", p)
                self.assertEqual(request.call_count, 1)
            self.assertFalse(p.exists())

    def test_supresion_no_confunde_diarios_nulos_con_conteos_pequenos(self):
        with duckdb.connect() as con:
            con.execute("CREATE TABLE dim_territorio(territorio_id VARCHAR,pais_id VARCHAR,poblacion DOUBLE,nivel VARCHAR,pais VARCHAR)")
            con.execute("INSERT INTO dim_territorio VALUES ('A','PA',3000,'condado','US'),('B','PB',3000,'condado','Chile')")
            con.execute("""CREATE TABLE fact_covid AS SELECT * FROM (VALUES
              ('A',DATE '2020-01-22',1.0,NULL::DOUBLE,NULL::DOUBLE,NULL::DOUBLE),
              ('A',DATE '2020-01-23',10.0,0.0,9.0,0.0),
              ('B',DATE '2020-01-22',0.0,0.0,NULL::DOUBLE,NULL::DOUBLE))
              t(territorio_id,fecha,confirmados,fallecidos,casos_nuevos,fallecidos_nuevos)""")
            con.execute("CREATE TABLE fact_pais AS SELECT pais_id,fecha,confirmados,fallecidos FROM fact_covid JOIN dim_territorio USING(territorio_id)")
            divulgacion(con)
            self.assertEqual(con.execute("SELECT suprimir FROM v_control_divulgacion WHERE territorio_id='B'").fetchone()[0], False)
            self.assertEqual(con.execute("SELECT confirmados FROM v_publica_segura WHERE territorio_id='B'").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(confirmados) FROM v_publica_segura WHERE territorio_id='A'").fetchone()[0], 0)
            self.assertEqual(metricas_divulgacion(con)["celdas_1a4"], 1)

    def test_subtotal_dependencia_no_se_suma_con_sus_condados(self):
        uid = pd.read_csv(self.original / "UID_ISO_FIPS_LookUp_Table.csv", dtype="string", keep_default_na=False)
        uid["fila_uid"] = range(1, len(uid) + 1)
        pr = uid[(uid.Country_Region == "US") & (uid.Province_State == "Puerto Rico")]
        elegidos = pd.concat([pr[pr.Admin2.eq("")].head(1), pr[pr.Admin2.ne("")].head(2)])
        self.assertEqual(len(elegidos), 3)
        with TemporaryDirectory(dir=self.temporales) as tmp:
            registros = []
            for (i, r), casos in zip(elegidos.iterrows(), [100, 60, 40]):
                registros.append({"FIPS": r.FIPS, "Admin2": r.Admin2, "Province_State": r.Province_State,
                    "Country_Region": "US", "Last_Update": "2020-03-22 23:45:00", "Lat": r.Lat,
                    "Long_": r.Long_, "Confirmed": str(casos), "Deaths": "0", "Recovered": "0",
                    "Active": str(casos), "Combined_Key": r.Combined_Key})
            archivo = Path(tmp) / "03-22-2020.csv"
            pd.DataFrame(registros).to_csv(archivo, index=False)
            d, _ = normalizar(archivo, sha256(archivo))
            d.to_parquet(Path(tmp) / "diarios_pr.parquet", index=False)
            with duckdb.connect() as con:
                construir_estrella(con, tmp, uid)
                self.assertEqual(con.execute("SELECT confirmados FROM fact_pais WHERE pais_id='U:840'").fetchone()[0], 100)
                self.assertEqual(con.execute("SELECT count(*) FROM v_rollup_territorial WHERE incluido").fetchone()[0], 1)
                plan = con.execute("EXPLAIN SELECT * FROM v_rollup_territorial").fetchone()[1]
                self.assertNotIn("BLOCKWISE_NL_JOIN", plan)
                traza = trazar(con, "U:840", "2020-03-22")
                self.assertEqual(len(traza), 3)
                self.assertEqual(int(traza.incluido_total_pais.sum()), 1)

    def test_owid_funciona_sin_banco_mundial_y_sin_multiplicar(self):
        with TemporaryDirectory(dir=self.temporales) as tmp:
            cache = Path(tmp) / "data/raw/external"
            cache.mkdir(parents=True)
            pd.DataFrame([{"location": "Chile", "iso_code": "CHL", "date": "2021-01-01", "people_vaccinated": 100,
                "people_fully_vaccinated": 1, "people_vaccinated_per_hundred": 0.0005,
                "people_fully_vaccinated_per_hundred": 0.00001}]).to_csv(cache / "owid_vaccinations.csv", index=False)
            dim = pd.DataFrame([{"territorio_id": "U:152", "iso3": "CHL", "pais": "Chile"}])
            vac, bm, cruces = integrar(Entradas(tmp, ROOT / "sin_clon", sin_red=True), Path(tmp), dim, incluir_bm=False)
            self.assertTrue(bm.empty)
            serie = pd.DataFrame([{"pais_id": "U:152", "fecha": vac.fecha.iloc[0], "confirmados": 100, "fallecidos": 0}])
            with duckdb.connect() as con:
                con.register("d", dim)
                con.execute("CREATE TABLE dim_pais AS SELECT * FROM d")
                con.register("f", serie)
                con.execute("CREATE TABLE fact_pais AS SELECT * FROM f")
                cargar_externas(con, serie, pd.DataFrame({"archivo_origen": pd.Series(dtype="string")}), vac, bm, cruces)
                self.assertEqual(con.execute("SELECT count(*) FROM v_pais_vacunacion").fetchone()[0], 1)
                self.assertEqual(con.execute("SELECT count(*) FROM v_pais_indicador").fetchone()[0], 1)
                self.assertIsNone(con.execute("SELECT porcentaje_65plus FROM v_pais_indicador").fetchone()[0])

    def test_chile_granularidad_conflictos_y_correcciones(self):
        with TemporaryDirectory(dir=self.temporales) as tmp:
            for i, nombre in enumerate(["01-23-2020.csv", "03-22-2020.csv", "05-19-2020.csv", "05-20-2020.csv", "05-22-2022.csv", "05-23-2022.csv"]):
                p = self.original / "csse_covid_19_daily_reports" / nombre
                df, _ = normalizar(p, sha256(p))
                df.to_parquet(Path(tmp) / f"diarios_{i}.parquet", index=False)
            uid = pd.read_csv(self.original / "UID_ISO_FIPS_LookUp_Table.csv", dtype="string", keep_default_na=False)
            uid["fila_uid"] = range(1, len(uid) + 1)
            with duckdb.connect() as con:
                construir_estrella(con, tmp, uid)
                self.assertEqual(con.execute("SELECT confirmados FROM fact_pais WHERE pais_id='U:152' AND fecha='2020-05-20'").fetchone()[0], 53617)
                self.assertEqual(con.execute("SELECT casos_nuevos FROM fact_pais WHERE pais_id='U:152' AND fecha='2020-05-20'").fetchone()[0], 4038)
                self.assertEqual(con.execute("SELECT count(*) FROM fact_covid WHERE territorio_id LIKE 'U:152%' AND fecha='2020-05-20' AND casos_nuevos IS NOT NULL").fetchone()[0], 0)
                self.assertLess(con.execute("SELECT casos_nuevos FROM fact_pais WHERE pais_id='U:152' AND fecha='2022-05-23'").fetchone()[0], 0)
                self.assertGreater(con.execute("SELECT count(*) FROM grupos_observados WHERE versiones>1").fetchone()[0], 0)
                self.assertEqual(con.execute("SELECT count(*) FROM fact_covid f JOIN grupos_observados g USING(territorio_id,fecha) WHERE g.versiones>1").fetchone()[0], 0)
                self.assertEqual(con.execute("SELECT count(*) FROM grupos_observados WHERE n_fuentes=2 AND versiones=1 AND fecha='2020-01-23'").fetchone()[0], 1)
                balance = balance_filas(con)
                self.assertEqual(int(balance.filas_origen.sum()), con.execute('SELECT count(*) FROM unificada').fetchone()[0])
                self.assertEqual(int(balance.hechos_dw.sum()), con.execute('SELECT count(*) FROM fact_covid').fetchone()[0])
                detalle = detalle_balance(con)
                self.assertTrue(detalle.observacion_id.is_unique)
                self.assertEqual(len(detalle), con.execute('SELECT sum(n_fuentes) FROM grupos_observados WHERE n_fuentes>1').fetchone()[0])

    def test_supresion_limites_poblacion_y_conteos(self):
        with duckdb.connect() as con:
            con.execute("CREATE TABLE dim_territorio(territorio_id VARCHAR,pais_id VARCHAR,poblacion DOUBLE,nivel VARCHAR,pais VARCHAR)")
            con.execute("CREATE TABLE fact_covid(territorio_id VARCHAR,fecha DATE,confirmados DOUBLE,fallecidos DOUBLE,casos_nuevos DOUBLE,fallecidos_nuevos DOUBLE)")
            esperados = []
            for i, poblacion in enumerate([4999,5000,None]):
                for j, conteo in enumerate([None,-1,0,1,4,5]):
                    tid = f'{i}:{j}'
                    con.execute("INSERT INTO dim_territorio VALUES (?,?,?,'condado','US')", [tid,tid,poblacion])
                    con.execute("INSERT INTO fact_covid VALUES (?,DATE '2020-01-22',?,NULL,NULL,NULL)", [tid,conteo])
                    esperados.append((tid,(poblacion is None or poblacion<5000) and conteo in [1,4]))
            con.execute('CREATE TABLE fact_pais AS SELECT territorio_id pais_id,fecha,confirmados,fallecidos FROM fact_covid')
            divulgacion(con)
            for tid, esperado in esperados:
                with self.subTest(territorio=tid):
                    self.assertEqual(con.execute('SELECT suprimir FROM v_control_divulgacion WHERE territorio_id=?',[tid]).fetchone()[0],esperado)
            self.assertEqual(metricas_divulgacion(con)['filas_supresion_primaria'],4)


if __name__ == "__main__":
    unittest.main()
