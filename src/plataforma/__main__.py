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
    parser.add_argument("--retomar", help="Finalizar informes de una carga que ya construyó las tablas; vuelve a validarlas")
    parser.add_argument("--consulta", choices=["roll_up", "drill_down", "slice", "dice"], default="slice")
    parser.add_argument("--territorio", default="U:152")
    parser.add_argument("--fecha", default="2020-05-20")
    args = parser.parse_args()
    proyecto = Path(__file__).resolve().parents[2]
    if args.accion == "construir":
        from .pipeline import ejecutar, retomar
        if args.retomar:
            retomar(proyecto, args.retomar)
        else:
            ejecutar(proyecto, args)
        return
    import duckdb
    from .almacen import OLAP, trazar
    ruta_puntero = proyecto / "data/hito2_actual.json"
    if not ruta_puntero.exists():
        parser.error("No hay carga validada. Ejecuta primero: python src/ejecutar_hito2.py construir")
    puntero = json.loads(ruta_puntero.read_text(encoding="utf-8"))
    with duckdb.connect(str(proyecto / puntero["dw"]), read_only=True,
                        config={"threads": 1, "memory_limit": "128MB"}) as con:
        con.execute("SET threads=1")
        con.execute("SET memory_limit='128MB'")
        if args.accion == "validar":
            from .validacion import validar
            print(validar(con).to_string(index=False))
        elif args.accion == "consultar":
            print(con.execute(OLAP[args.consulta]).fetchdf().to_string(index=False))
        else:
            # Para un país: filas de los dos días que originan el acumulado y el delta.
            print(trazar(con, args.territorio, args.fecha).to_string(index=False))


if __name__ == "__main__":
    main()
