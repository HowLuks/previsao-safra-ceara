"""Variáveis de chuva por município e ano, a partir da chuva diária dos postos."""
from collections import defaultdict

DIA_CHUVOSO = 1.0  # mm; abaixo disso o dia conta como seco
MAX_FALHAS_MES = 5  # mês com mais dias sem nenhum posto válido vira falta


def serie_municipal(registros) -> dict:
    """{(municipio, ano, mes): [chuva média dos postos válidos por dia, ou None]}."""
    somas = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    for municipio, _posto, ano, mes, dias in registros:
        acc = somas[(municipio, ano, mes)]
        for i, v in enumerate(dias):
            if v is not None:
                acc[i][0] += v
                acc[i][1] += 1
    saida = {}
    for chave, acc in somas.items():
        n_dias = max(acc) + 1 if acc else 0
        saida[chave] = [acc[i][0] / acc[i][1] if i in acc and acc[i][1] else None for i in range(n_dias)]
    return saida


def maior_veranico(dias: list) -> int:
    """Maior sequência de dias secos seguidos; dia sem dado quebra a sequência (conservador)."""
    maior = atual = 0
    for v in dias:
        atual = atual + 1 if v is not None and v < DIA_CHUVOSO else 0
        maior = max(maior, atual)
    return maior


def _resumo(dias: list, sufixo: str) -> dict:
    validos = [v for v in dias if v is not None]
    return {f"chuva_{sufixo}": round(sum(validos), 1), f"dias_chuva_{sufixo}": sum(v >= DIA_CHUVOSO for v in validos),
            f"veranico_{sufixo}": maior_veranico(dias)}


def variaveis_ano(serie: dict, municipio: str, ano: int) -> dict | None:
    """Chuva de jan a jun por mês, resumo da quadra (fev-mai) e resumo só até março (previsão antecipada).
    None se faltar algum mês de jan a mai."""
    meses = {}
    for mes in range(1, 7):
        dias = serie.get((municipio, ano, mes))
        if dias is None or sum(v is None for v in dias) > MAX_FALHAS_MES:
            if mes <= 5:
                return None
            dias = None
        meses[mes] = dias
    nomes = ["jan", "fev", "mar", "abr", "mai", "jun"]
    saida = {f"chuva_{nomes[m - 1]}": round(sum(v for v in d if v is not None), 1) if d else None
             for m, d in meses.items()}
    saida |= _resumo(meses[2] + meses[3] + meses[4] + meses[5], "quadra")
    saida |= _resumo(meses[2] + meses[3], "fev_mar")
    return saida
