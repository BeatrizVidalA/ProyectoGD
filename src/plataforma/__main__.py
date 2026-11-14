import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Plataforma COVID-19 — Hito 2")
    parser.add_argument("accion", choices=["construir", "validar", "consultar", "traza"])
    parser.add_argument("--original", type=Path)
    parser.add_argument("--sin-red", action="store_true")
    parser.add_argument("--solo-cache", action="store_true", help="No consultar el clon JHU")
    parser.add_argument("--sin-banco-mundial", action="store_true")
    parser.add_argument("--consulta", choices=["roll_up", "drill_down", "slice", "dice"], default="slice")
    parser.add_argument("--territorio", default="U:152")
    parser.add_argument("--fecha", default="2020-05-20")
    args = parser.parse_args()
    proyecto = Path(__file__).resolve().parents[2]
    if args.accion == "construir":
        from .pipeline import ejecutar
        ejecutar(proyecto, args)
        return
    import duckdb
    from .almacen import OLAP
    puntero = json.loads((proyecto / "data/hito2_actual.json").read_text(encoding="utf-8"))
    with duckdb.connect(str(proyecto / puntero["dw"]), read_only=True) as con:
        if args.accion == "validar":
            from .validacion import validar
            print(validar(con).to_string(index=False))
        elif args.accion == "consultar":
            print(con.execute(OLAP[args.consulta]).fetchdf().to_string(index=False))
        else:
            # Para un país: filas de los dos días que originan el acumulado y el delta.
            print(con.execute("""SELECT l.* FROM v_linaje l JOIN dim_territorio d USING(territorio_id)
              WHERE (l.territorio_id=? OR d.pais_id=?) AND l.fecha_reporte BETWEEN CAST(? AS DATE)-1 AND CAST(? AS DATE)
              ORDER BY l.fecha_reporte,l.archivo_origen,l.fila_origen""", [args.territorio, args.territorio, args.fecha, args.fecha]).fetchdf().to_string(index=False))


if __name__ == "__main__":
    main()
