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
from plataforma.almacen import construir_estrella


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


if __name__ == "__main__":
    unittest.main()
