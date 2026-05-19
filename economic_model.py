import geopandas as gpd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def midpoint_classe(classe: str) -> float:
    """
    Retorna o ponto médio percentual de um bin de classe.

    "4-6"  → 5.0  |  ">20" → 22.0  |  "0-2" → 1.0
    Usado para estimar a severidade média dentro de cada bin.
    """
    classe = str(classe).strip()
    if ">" in classe:
        return 22.0
    try:
        partes = classe.split("-")
        if len(partes) == 2:
            return (float(partes[0]) + float(partes[1])) / 2.0
    except (ValueError, IndexError):
        pass
    return 0.0


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------

def aplicar_modelo_economico(
    gdf: gpd.GeoDataFrame,
    diesel: float,
    operador: float,
    manutencao: float,
    muda: float,
    maquina: float,
    produtividade: float,
    preco: float,
    espacamento: float,
    manobra: float,
    deslocamento: float,
    abastecimento: float,
) -> gpd.GeoDataFrame:
    """
    Aplica o modelo econômico a todas as linhas do GeoDataFrame.

    Parâmetros de custo (R$/ha): diesel, operador, manutencao, muda, maquina
    Produção: produtividade (t/ha), preco (R$/t)
    Operacional: espacamento (m), manobra + deslocamento + abastecimento (min, somados como custo fixo por linha)

    Colunas adicionadas:
      area_ha           — área equivalente da linha em hectares
      perc_classe       — ponto médio do bin 'classe' (%)
      valor_recuperavel — receita estimada pela replantia (R$)
      custo             — custo total de replantia (R$)
      lucro             — valor_recuperavel - custo (R$)
      viavel            — True se lucro > 0

    Fórmulas (conforme modelo HTML):
      area_ha            = (comp_linha × espacamento) / 10.000
      valor_recuperavel  = produtividade × preco × (perc_classe/100) × area_ha × 0.8
      custo              = custo_ha × area_ha + tempo_op
      lucro              = valor_recuperavel - custo
    """
    custo_ha = diesel + operador + manutencao + muda + maquina
    tempo_op = manobra + deslocamento + abastecimento
    valor_ha = produtividade * preco

    gdf = gdf.copy()

    gdf["area_ha"] = (gdf["comp_linha"] * espacamento) / 10_000
    gdf["perc_classe"] = gdf["classe"].apply(midpoint_classe)
    gdf["valor_recuperavel"] = (
        valor_ha * (gdf["perc_classe"] / 100) * gdf["area_ha"] * 0.8
    )
    gdf["custo"] = custo_ha * gdf["area_ha"] + tempo_op
    gdf["lucro"] = gdf["valor_recuperavel"] - gdf["custo"]
    gdf["viavel"] = gdf["lucro"] > 0

    return gdf
