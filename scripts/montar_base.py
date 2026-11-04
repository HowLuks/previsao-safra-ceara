"""Monta dados/base.csv: uma linha por município, ano e produto (milho, feijão), com produção do IBGE e chuva da FUNCEME.

  python scripts/montar_base.py

Os arquivos brutos são baixados uma vez em dados/brutos/ (fora do git).
"""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from safra.chuva import serie_municipal, variaveis_ano  # noqa: E402
from safra.fontes import (INDICES_NOAA, URL_FUNCEME, URL_NOAA, URL_SIDRA, baixar, ler_funceme, ler_ibge,  # noqa: E402
                          ler_noaa, normalizar)

ANOS = range(1990, 2026)  # a FUNCEME cobre os 184 municípios a partir de 1990; o IBGE vai até 2025
BRUTOS = RAIZ / "dados" / "brutos"
# Nomes que diferem entre as fontes além de acento e caixa (normalizados), FUNCEME -> IBGE
APELIDOS: dict[str, str] = {}


def oceano_ano(indices: dict, ano: int) -> dict | None:
    """Índices do oceano já conhecidos no fim de março: El Niño de dezembro a fevereiro e Atlântico de janeiro a
    fevereiro. O dipolo (norte menos sul) quente ao norte costuma trazer seca ao Ceará."""
    try:
        nino = [indices["nino34"][(ano - 1, 12)], indices["nino34"][(ano, 1)], indices["nino34"][(ano, 2)]]
        tna = [indices["tna"][(ano, m)] for m in (1, 2)]
        tsa = [indices["tsa"][(ano, m)] for m in (1, 2)]
    except KeyError:
        return None
    return {"nino34_djf": round(sum(nino) / 3, 2), "tna_jf": round(sum(tna) / 2, 2), "tsa_jf": round(sum(tsa) / 2, 2),
            "dipolo_jf": round((sum(tna) - sum(tsa)) / 2, 2)}


def main():
    ibge = ler_ibge(baixar(URL_SIDRA.format(anos=",".join(map(str, ANOS))), BRUTOS / "ibge_pam_1612.json"))
    print("lendo chuva da FUNCEME...")
    serie = serie_municipal(ler_funceme(baixar(URL_FUNCEME, BRUTOS / "funceme_postos.zip")))
    indices = {nome: ler_noaa(baixar(URL_NOAA.format(arq), BRUTOS / f"noaa_{arq}.data"))
               for nome, arq in INDICES_NOAA.items()}

    cod_por_nome = {normalizar(r["municipio"]): cod for (cod, _, _), r in ibge.items()}
    nome_funceme = {}
    for municipio, _, _ in serie:
        n = normalizar(municipio)
        n = APELIDOS.get(n, n)
        if n in cod_por_nome:
            nome_funceme[cod_por_nome[n]] = municipio
    sem_par = sorted(set(cod_por_nome) - {normalizar(ibge_nome) for ibge_nome in
                                          [r["municipio"] for (c, _, _), r in ibge.items() if c in nome_funceme]})
    if sem_par:
        print("municípios do IBGE sem chuva da FUNCEME:", sem_par)

    linhas = []
    for (cod, ano, produto), r in sorted(ibge.items()):
        if cod not in nome_funceme or not r.get("area_plantada"):
            continue  # sem chuva ou sem plantio nesse ano
        chuva = variaveis_ano(serie, nome_funceme[cod], ano)
        oceano = oceano_ano(indices, ano)
        if chuva is None or oceano is None:
            continue
        producao, area_colhida = r.get("producao"), r.get("area_colhida")
        if producao is None or area_colhida is None:
            continue  # IBGE sem dado ('...'): não é perda total, então não vira zero
        linhas.append({"cod_ibge": cod, "municipio": r["municipio"], "ano": ano, "produto": produto,
                       "area_plantada": r["area_plantada"], "area_colhida": area_colhida,
                       "producao": producao,
                       "rendimento": round(producao * 1000 / r["area_plantada"], 1),  # kg por ha plantado
                       **chuva, **oceano})
    destino = RAIZ / "dados" / "base.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"{len(linhas)} linhas em {destino}")


if __name__ == "__main__":
    main()
