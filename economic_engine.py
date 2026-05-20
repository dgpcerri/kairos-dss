"""
Motor econômico do Kairos — modelo linha a linha  (v4.0)

Regra operacional
-----------------
O trator percorre cada linha completa dentro do talhão até a cabeceira,
executa a manobra de cabeceira e segue para a próxima linha.

Tempo por linha
---------------
  tempo_plantio_min      = soma_falhas / vel_plantio
  tempo_deslocamento_min = comp_saudavel / vel_deslocamento
  tempo_manobra_min      = tempo_manobra_fixo          (uma por linha)
  tempo_recarga_min      = (soma_falhas / capacidade_carga_m) × t_recarga
      → paradas para recarregamento proporcional ao total de falhas plantadas
  tempo_transfer_min     = tempo_transferencia_talhao / n_linhas_talhao
      → custo de deslocamento entre talhões amortizado por linha

  tempo_total_min = Σ dos cinco componentes

Receita / Custo / IOI
---------------------
  preco_efetivo_ton  = atr_medio_kgton × preco_atr_rs_kg        [R$/ton]
  ganho_ajustado_tha = ganho_esperado_tha × fator_soca
  area_falha_ha      = soma_falhas × espacamento / 10 000
  receita_bruta      = area_falha_ha × ganho_ajustado × (pegamento/100)
                       × preco_efetivo_ton
  receita_liquida    = receita_bruta × (1 − risco_climatico/100)
  custo_maquina      = custo_hora × (tempo_total_min / 60)
  custo_insumos      = area_falha_ha × (custo_muda_tha + custo_logistica_muda_ha)
  lucro              = receita_liquida − custo_maquina − custo_insumos
  ioi (R$/h)         = lucro / (tempo_total_min / 60)
  viavel             = ioi >= ioi_minimo

Ranking
-------
  Calculado dentro de cada talhão (não global), para refletir a ordem
  real de prioridade de campo por área de operação.
"""

import geopandas as gpd
import numpy as np


FATOR_SOCA = {
    "Cana-planta": 1.00,
    "Soca 1":      0.90,
    "Soca 2":      0.80,
    "Soca 3":      0.70,
    "Soca 4+":     0.65,
}


def calcular_custo_hora(p: dict) -> float:
    """R$/hora total da máquina em operação."""
    custo_diesel   = p["diesel_lh"] * p["preco_diesel"]
    custo_mao_obra = (
        p["salario_operador"] + p["n_auxiliares"] * p["salario_auxiliar"]
    ) / p["horas_mes"]
    custo_manut = p["manutencao_mensal"] / p["horas_mes"]
    custo_depre = (p["depreciacao_anual"] / 12.0) / p["horas_mes"]
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

    vmpm_p = p["velocidade_plantio_kmh"]      * 1000.0 / 60.0  # m/min
    vmpm_d = p["velocidade_deslocamento_kmh"] * 1000.0 / 60.0
    tmf    = p["tempo_manobra_fixo_min"]
    esp    = p["espacamento"]

    # ATR-based effective price (R$/ton)
    preco_efetivo_ton = p["atr_medio_kgton"] * p["preco_atr_rs_kg"]

    # Soca multiplier on expected yield
    fator_soca    = FATOR_SOCA.get(p.get("ciclo_soca", "Cana-planta"), 1.00)
    ganho_efetivo = p["ganho_esperado_tha"] * fator_soca

    ioi_min = p.get("ioi_minimo", 0.0)

    df = gdf_candidatas.copy()

    # Guard: soma_falhas cannot exceed comp_linha (floating-point safety)
    df["soma_falhas"] = df["soma_falhas"].clip(upper=df["comp_linha"])
    comp_saudavel     = (df["comp_linha"] - df["soma_falhas"]).clip(lower=0)

    # ── Time components ───────────────────────────────────────────────────
    df["tempo_plantio_min"]      = df["soma_falhas"] / vmpm_p
    df["tempo_deslocamento_min"] = comp_saudavel / vmpm_d
    df["tempo_manobra_min"]      = tmf

    # Reload time: proportional to gap length planted per line
    cap_m   = max(p.get("capacidade_carga_m", 400.0), 1.0)
    t_carga = p.get("tempo_recarga_min", 20.0)
    df["tempo_recarga_min"] = (df["soma_falhas"] / cap_m) * t_carga

    # Inter-talhão transfer: amortized over lines per talhão
    t_transf = p.get("tempo_transferencia_talhao_min", 30.0)
    n_por_talhao = df.groupby("TALHAO")["FID"].transform("count")
    df["tempo_transfer_min"] = t_transf / n_por_talhao

    df["tempo_total_min"] = (
        df["tempo_plantio_min"]
        + df["tempo_deslocamento_min"]
        + df["tempo_manobra_min"]
        + df["tempo_recarga_min"]
        + df["tempo_transfer_min"]
    )

    df["eficiencia_pct"] = np.where(
        df["tempo_total_min"] > 0,
        df["tempo_plantio_min"] / df["tempo_total_min"] * 100,
        0.0,
    )

    # ── Revenue & cost ────────────────────────────────────────────────────
    df["area_falha_ha"] = df["soma_falhas"] * esp / 10_000

    df["receita_bruta"] = (
        df["area_falha_ha"]
        * ganho_efetivo
        * (p["taxa_pegamento"] / 100.0)
        * preco_efetivo_ton
    )
    df["receita_liquida"] = df["receita_bruta"] * (1.0 - p["risco_climatico"] / 100.0)
    df["custo_maquina"]   = custo_h * (df["tempo_total_min"] / 60.0)
    df["custo_insumos"]   = df["area_falha_ha"] * (
        p["custo_muda_tha"] + p.get("custo_logistica_muda_ha", 0.0)
    )
    df["custo_total"] = df["custo_maquina"] + df["custo_insumos"]
    df["lucro"]       = df["receita_liquida"] - df["custo_total"]

    df["ioi"] = np.where(
        df["tempo_total_min"] > 0,
        df["lucro"] / (df["tempo_total_min"] / 60.0),
        -np.inf,
    )
    df["viavel"] = df["ioi"] >= ioi_min

    # Ranking within each talhão (not global)
    df["ranking"] = (
        df.groupby("TALHAO")["ioi"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    return gpd.GeoDataFrame(df, geometry="geometry", crs=gdf_candidatas.crs)
