# Previsão de safra de sequeiro no Ceará

Dá para prever em abril, antes da colheita, quanto cada município do Ceará vai colher de milho e feijão? Quase toda
essa lavoura é de sequeiro: depende só da chuva da quadra chuvosa (fevereiro a maio). Quando a safra quebra, o
Garantia-Safra paga o agricultor familiar que perdeu 50% ou mais da produção, então saber cedo onde vai faltar tem uso
para o estado, para cooperativas e para quem planeja o abastecimento.

Este projeto junta a chuva diária dos postos da FUNCEME com a produção municipal do IBGE (1990–2025) e treina modelos
para prever o rendimento de cada município.

## Dados

| Fonte | O que vem | Período |
|---|---|---|
| [IBGE, Produção Agrícola Municipal](https://sidra.ibge.gov.br/tabela/1612) (tabela 1612) | área plantada, área colhida e produção de milho e feijão por município | anual, 1974–2025 |
| [FUNCEME, postos pluviométricos](https://chuvas.funceme.br/) | chuva diária de 844 postos | 1973–hoje; os 184 municípios a partir de 1990 |

`python scripts/montar_base.py` baixa as duas fontes e grava `dados/base.csv`, com uma linha por município, ano e
produto (13.162 linhas). Cada linha traz:

- **Produção:** `area_plantada` (ha), `area_colhida` (ha), `producao` (t) e o alvo `rendimento`, em kg por hectare
  **plantado**. Usar a área plantada, e não a colhida, faz a perda aparecer: quando a safra quebra, parte da área nem é
  colhida. Quando o IBGE marca `-` (zero), a produção entra como 0: são perdas totais, como as 19 linhas da seca de
  2012–2016. Linha marcada `...` (sem dado) sai da base, para não confundir falta de dado com perda.
- **Chuva do município:** média dos postos válidos de cada dia. Mês com mais de 5 dias sem nenhum posto válido vira
  falta, e o ano sem janeiro a maio completo sai da base.
  - `chuva_jan` … `chuva_jun`: total do mês (mm).
  - `chuva_quadra`, `dias_chuva_quadra`, `veranico_quadra`: total, dias com chuva (≥ 1 mm) e maior sequência de dias
    secos de fevereiro a maio.
  - `chuva_fev_mar`, `dias_chuva_fev_mar`, `veranico_fev_mar`: o mesmo só até março, para a previsão antecipada.

As secas conhecidas aparecem nos dados. Em 1993, a mediana dos municípios teve 300 mm na quadra e 28 kg/ha de milho;
o mesmo se vê em 1998 e na seca de 2012–2016. O ano mais chuvoso, 2009 (mediana de 1.001 mm), também teve rendimento
baixo, o que indica que a relação com a chuva não é linear.

## Próximos passos

- Baseline (média do município) e modelos (regressão linear, LightGBM) com validação temporal.
- Previsão antecipada com dados só até março.
- Mapa do Ceará com a previsão por município, notebook e dataset no Kaggle.

## Como rodar

```bash
python scripts/montar_base.py   # Python 3.10+, sem dependências
python tests/test_chuva.py
```
