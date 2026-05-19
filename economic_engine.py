"""
Motor econômico do Kairos — modelo linha a linha.

Regra operacional
-----------------
O trator entra em uma linha, percorre seu comprimento COMPLETO dentro do
talhão até a cabeceira, executa a manobra de cabeceira e segue para a
próxima linha. Nunca cruza linhas pelo meio do talhão.

Tempo por linha
---------------
  tempo_plantio_min      = soma_falhas / vel_plantio
      → trechos de FALHA percorridos em velocidade de plantio

  tempo_deslocamento_min = (comp_linha − soma_falhas) / vel_deslocamento
      → trechos SEM FALHA percorridos em velocidade de deslocamento

  tempo_manobra_min      = tempo_manobra_fixo
      → uma manobra de cabeceira por linha

  tempo_total_min        = plantio + deslocamento + manobra

  eficiencia_pct         = tempo_plantio / tempo_total × 100

Receita / Custo / IOI
---------------------
  area_falha_ha    = soma_falhas × espacamento / 10 000
  receita_bruta    = area_falha_ha × ganho_tha × (taxa_pegamento/100) × preco_t
  receita_liquida  = receita_bruta × (1 − risco_climatico/100)
  custo_maquina    = custo_hora × (tempo_total_min / 60)
  custo_insumos    = area_falha_ha × custo_muda_tha
  lucro            = receita_liquida − custo_maquina − custo_insumos
  ioi (R$/h)       = lucro / (tempo_total_min / 60)
  viavel           = ioi >= ioi_minimo
"""

import geopandas as gpd
import numpy as np


def calcular_custo_hora(p: dict) -> float:
    """R$/hora total da máquina em operação."""
    custo_diesel   = p["diesel_lh"] * p["preco_diesel"]
    custo_mao_obra = (p["salario_operador"] + p["n_auxiliares"] * p["salario_auxiliar"]) / p["horas_mes"]
    custo_manut    = p["manutencao_mensal"] / p["horas_mes"]
    custo_depre    = (p["depreciacao_anual"] / 12.0) / p["horas_mes"]
    return custo_diesel + custo_mao_obra + custo_manut + custo_depre


def calcular_linhas(
    gdf_candidatas: gpd.GeoDataFrame,
    params: dict,
) -> gpd.GeoDataFrame:
    """
    Aplica o modelo econômico a cada linha individualmente.

    Args:
        gdf_candidatas: GDF com colunas soma_falhas, comp_linha, TALHAO, FID.
        params:         Dicionário com todos os parâmetros do sidebar.

    Returns:
        GeoDataFrame com todas as colunas econômicas adicionadas por linha.
    """
    p       = params
    custo_h = calcular_custo_hora(p)

    vmpm_p  = p["velocidade_plantio_kmh"]      * 1000.0 / 60.0  # km/h → m/min
    vmpm_d  = p["velocidade_deslocamento_kmh"] * 1000.0 / 60.0
    tmf     = p["tempo_manobra_fixo_min"]
    ioi_min = p.get("ioi_minimo", 0.0)
    esp     = p["espacamento"]

    df = gdf_candidatas.copy()

    comp_saudavel = (df["comp_linha"] - df["soma_falhas"]).clip(lower=0)

    df["tempo_plantio_min"]      = df["soma_falhas"] / vmpm_p
    df["tempo_deslocamento_min"] = comp_saudavel / vmpm_d
    df["tempo_manobra_min"]      = tmf
    df["tempo_total_min"]        = (
        df["tempo_plantio_min"]
        + df["tempo_deslocamento_min"]
        + df["tempo_manobra_min"]
    )
    df["eficiencia_pct"] = np.where(
        df["tempo_total_min"] > 0,
        df["tempo_plantio_min"] / df["tempo_total_min"] * 100,
        0.0,
    )

    df["area_falha_ha"]   = df["soma_falhas"] * esp / 10_000
    df["receita_bruta"]   = (
        df["area_falha_ha"]
        * p["ganho_esperado_tha"]
        * (p["taxa_pegamento"] / 100.0)
        * p["preco_tonelada"]
    )
    df["receita_liquida"] = df["receita_bruta"] * (1.0 - p["risco_climatico"] / 100.0)
    df["custo_maquina"]   = custo_h * (df["tempo_total_min"] / 60.0)
    df["custo_insumos"]   = df["area_falha_ha"] * p["custo_muda_tha"]
    df["custo_total"]     = df["custo_maquina"] + df["custo_insumos"]
    df["lucro"]           = df["receita_liquida"] - df["custo_total"]
    df["ioi"]             = np.where(
        df["tempo_total_min"] > 0,
        df["lucro"] / (df["tempo_total_min"] / 60.0),
        -np.inf,
    )
    df["viavel"]  = df["ioi"] >= ioi_min
    df["ranking"] = (
        df["ioi"].rank(ascending=False, method="min").astype(int)
    )

    return gpd.GeoDataFrame(df, geometry="geometry", crs=gdf_candidatas.crs)
