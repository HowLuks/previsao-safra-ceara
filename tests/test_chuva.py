"""Testes das variáveis de chuva (sem rede). Rodar com: python tests/test_chuva.py  (ou pytest)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from safra.chuva import maior_veranico, serie_municipal, variaveis_ano  # noqa: E402
from safra.fontes import normalizar  # noqa: E402


def test_veranico():
    assert maior_veranico([0, 0, 5, 0, 0, 0, 0.5, 2]) == 4
    assert maior_veranico([0, None, 0]) == 1  # dia sem dado quebra a sequência
    assert maior_veranico([]) == 0


def test_serie_media_dos_postos_validos():
    reg = [("A", "p1", 2000, 2, [10.0, None, 0.0]), ("A", "p2", 2000, 2, [20.0, 4.0, None])]
    assert serie_municipal(reg)[("A", 2000, 2)] == [15.0, 4.0, 0.0]


def test_variaveis_ano():
    serie = {("A", 2000, m): [2.0] * 28 for m in range(1, 6)}
    v = variaveis_ano(serie, "A", 2000)
    assert v["chuva_fev"] == 56.0 and v["chuva_quadra"] == 224.0 and v["dias_chuva_fev_mar"] == 56
    assert v["chuva_jun"] is None and v["veranico_quadra"] == 0
    serie[("A", 2000, 3)] = [None] * 10 + [2.0] * 18  # mais de 5 dias sem dado: ano descartado
    assert variaveis_ano(serie, "A", 2000) is None


def test_normalizar():
    assert normalizar("Santana do Acaraú - CE") == normalizar("SANTANA DO ACARAU") == "santana do acarau"
    assert normalizar("Itapajé") == "itapaje"


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
    print("ok")
