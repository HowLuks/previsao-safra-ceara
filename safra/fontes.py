"""Download e leitura das fontes: produção agrícola do IBGE, chuva diária dos postos da FUNCEME e índices do oceano da
NOAA."""
import io
import json
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

URL_FUNCEME = "https://cdn.funceme.br/calendario/postos/postos.zip"
URL_SIDRA = "https://apisidra.ibge.gov.br/values/t/1612/n6/in%20n3%2023/v/109,216,214/p/{anos}/c81/2711,2702?formato=json"
PRODUTOS = {"2711": "milho", "2702": "feijao"}
VARIAVEIS = {"109": "area_plantada", "216": "area_colhida", "214": "producao"}
SEM_DADO, DIA_INEXISTENTE = 999.0, 888.0
# Temperatura da superfície do mar (anomalia, °C): Pacífico (El Niño 3.4) e Atlântico tropical norte e sul
URL_NOAA = "https://psl.noaa.gov/data/correlation/{}.data"
INDICES_NOAA = {"nino34": "nina34.anom", "tna": "tna", "tsa": "tsa"}


def normalizar(nome: str) -> str:
    """Nome de município comparável entre as fontes: sem acento, minúsculo, sem o ' - CE' do IBGE."""
    nome = nome.split(" - ")[0]
    nome = "".join(c for c in unicodedata.normalize("NFD", nome) if unicodedata.category(c) != "Mn")
    return " ".join(nome.lower().replace("-", " ").replace("'", " ").split())


def baixar(url: str, destino: Path) -> Path:
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=300) as r:
            destino.write_bytes(r.read())
    return destino


def valor_ibge(v: str):
    """Valor do SIDRA: '-' é zero de verdade (convenção do IBGE); '...', '..' e 'X' são falta de dado e viram None."""
    if v == "-":
        return 0.0
    return float(v) if v.replace(".", "").isdigit() else None


def ler_ibge(caminho: Path) -> dict:
    """{(cod_ibge, ano, produto): {"municipio", "area_plantada", "area_colhida", "producao"}}, valores por valor_ibge."""
    linhas = json.loads(caminho.read_text())[1:]  # a primeira linha é o cabeçalho
    saida = {}
    for l in linhas:
        chave = (l["D1C"], int(l["D3C"]), PRODUTOS[l["D4C"]])
        reg = saida.setdefault(chave, {"municipio": l["D1N"].split(" - ")[0]})
        reg[VARIAVEIS[l["D2C"]]] = valor_ibge(l["V"])
    return saida


def ler_funceme(caminho: Path, meses=range(1, 7)):
    """Gera (municipio, posto, ano, mes, [chuva por dia]) dos meses pedidos; dia sem dado = None, dia inexistente sai."""
    with zipfile.ZipFile(caminho) as z:
        for nome in z.namelist():
            texto = io.TextIOWrapper(z.open(nome), encoding="utf-8")
            next(texto)  # cabeçalho
            for linha in texto:
                c = linha.rstrip("\n").split(";")
                if len(c) < 38 or int(c[5]) not in meses:
                    continue
                dias = []
                for v in c[7:38]:
                    f = float(v) if v else SEM_DADO
                    if f == DIA_INEXISTENTE:
                        continue
                    dias.append(None if f == SEM_DADO or f < 0 else f)
                yield c[0], c[1], int(c[4]), int(c[5]), dias


def ler_noaa(caminho: Path) -> dict:
    """{(ano, mes): valor} de um índice mensal da NOAA PSL; -99.99 é falta e fica de fora."""
    linhas = caminho.read_text().splitlines()
    inicio, fim = map(int, linhas[0].split())
    saida = {}
    for linha in linhas[1:]:
        c = linha.split()
        if len(c) != 13 or not c[0].isdigit() or not inicio <= int(c[0]) <= fim:
            continue  # rodapé com unidade e fonte
        for mes, v in enumerate(c[1:], 1):
            if float(v) > -99:
                saida[(int(c[0]), mes)] = float(v)
    return saida
