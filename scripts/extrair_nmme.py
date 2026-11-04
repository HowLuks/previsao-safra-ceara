"""Grava dados/nmme_ceara.csv: previsão de chuva do NMME feita em março para abril e maio, nas células de 1° sobre o
Ceará, de 1991 a 2020 (rodadas retroativas).

  python scripts/extrair_nmme.py

Os dois arquivos brutos (22 MB cada, o globo inteiro) são baixados uma vez em dados/brutos/. As previsões reais de
2021 em diante não estão no servidor público do CPC, só a do ano corrente.
"""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from safra.fontes import URL_NMME, baixar, ler_cpt  # noqa: E402

BRUTOS = RAIZ / "dados" / "brutos"


def main():
    abr, mai = (ler_cpt(baixar(URL_NMME.format(inicio="Mar", mes=m), BRUTOS / f"nmme_mar_{m}.txt")) for m in (4, 5))
    destino = RAIZ / "dados" / "nmme_ceara.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ano", "lat", "lon", "nmme_abr", "nmme_mai"])  # mm/dia; lon de -180 a 180
        for ano in sorted(abr):
            for (y, x), v in sorted(abr[ano].items()):
                w.writerow([ano, y, x - 360, round(v, 3), round(mai[ano][(y, x)], 3)])
    print(f"{len(abr)} anos em {destino}")


if __name__ == "__main__":
    main()
