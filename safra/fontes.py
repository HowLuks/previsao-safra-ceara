"""Download e leitura das duas fontes: produção agrícola do IBGE e chuva diária dos postos da FUNCEME."""
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


def ler_ibge(caminho: Path) -> dict:
    """{(cod_ibge, ano, produto): {"municipio", "area_plantada", "area_colhida", "producao"}}; '-' e '...' viram None."""
    linhas = json.loads(caminho.read_text())[1:]  # a primeira linha é o cabeçalho
    saida = {}
    for l in linhas:
        chave = (l["D1C"], int(l["D3C"]), PRODUTOS[l["D4C"]])
        reg = saida.setdefault(chave, {"municipio": l["D1N"].split(" - ")[0]})
        reg[VARIAVEIS[l["D2C"]]] = float(l["V"]) if l["V"].replace(".", "").isdigit() else None
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
