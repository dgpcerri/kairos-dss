"""
Motor econômico do Kairos — modelo linha a linha  (v5.0)

Novidades v5.0
--------------
- Filtro de linhas curtas (comprimento_minimo_linha) — exclui linhas com razão
  manobra/m plantado proibitiva. Linhas excluídas permanecem no DataFrame
  marcadas com `excluida_curta = True` e `viavel = False`.
- Fator de Encargos Trabalhistas (1.30–1.60) sobre salário operador/auxiliar.
- Cenários econômicos (Realista / Otimista / Pessimista) ajustam dinamicamente
  preço ATR, diesel e taxa de pegamento.
- Lucro Cessante — receita perdida nas falhas que NÃO serão replantadas
  até a próxima reforma (linhas inviáveis + linhas curtas).
- Framework VPL 5 anos: compara VPL da Reforma Total vs VPL do Replantio
  Pontual descontados a uma taxa WACC.

Tempo por linha (cinco componentes, igual v4.0)
-----------------------------------------------
  tempo_plantio_min      = soma_falhas / vel_plantio
  tempo_deslocamento_min = comp_saudavel / vel_deslocamento
  tempo_manobra_min      = tempo_manobra_fixo          (uma por linha)
  tempo_recarga_min      = (soma_falhas / capacidade_carga_m) × t_recarga
  tempo_transfer_min     = tempo_transferencia_talhao / n_linhas_talhao

Receita / Custo / IOI
---------------------
  preco_efetivo_ton  = atr_medio_kgton × preco_atr_rs_kg × cenario.atr_mult
  pegamento_eff      = min(taxa_pegamento × cenario.peg_mult, 100)
  diesel_eff         = preco_diesel × cenario.diesel_mult
  ganho_ajustado_tha = ganho_esperado_tha × fator_soca
  area_falha_ha      = soma_falhas × espacamento / 10 000
  receita_bruta      = area_falha_ha × ganho_ajustado × (pegamento_eff/100)
                       × preco_efetivo_ton
  receita_liquida    = receita_bruta × (1 − risco_climatico/100)
  custo_maquina      = custo_hora × (tempo_total_min / 60)
  custo_insumos      = area_falha_ha × (custo_muda_tha + custo_logistica_muda_ha)
  lucro              = receita_liquida − custo_maquina − custo_insumos
  ioi (R$/h)         = lucro / (tempo_total_min / 60)
  viavel             = (ioi >= ioi_minimo) AND (not excluida_curta)

Lucro Cessante (por linha)
--------------------------
Para linhas NÃO replantadas (inviáveis ou curtas), calcula-se a receita
incremental perdida nas próximas (anos_extensao) safras que o replantio
teria preservado:

  lucro_cessante = receita_liquida × anos_extensao

Ranking
-------
  Calculado dentro de cada talhão (não global).
"""

from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd


# ── Constantes ─────────────────────────────────────────────────────────────

FATOR_SOCA: dict[str, float] = {
    "Cana-planta": 1.00,
    "Soca 1":      0.90,
    "Soca 2":      0.80,
    "Soca 3":      0.70,
    "Soca 4+":     0.65,
}

# Cycle order — usado para projeção VPL de safras futuras
CICLO_ORDEM = ["Cana-planta", "Soca 1", "Soca 2", "Soca 3", "Soca 4+"]


# Multiplicadores por cenário econômico
SCENARIOS: dict[str, dict[str, float]] = {
    "Realista":   {"atr_mult": 1.00, "diesel_mult": 1.00, "pegamento_mult": 1.00},
    "Otimista":   {"atr_mult": 1.15, "diesel_mult": 0.85, "pegamento_mult": 1.10},
    "Pessimista": {"atr_mult": 0.85, "diesel_mult": 1.15, "pegamento_mult": 0.85},
}


def get_scenario(nome: str) -> dict[str, float]:
    return SCENARIOS.get(nome, SCENARIOS["Realista"])


# ── Custo por hora ──────────────────────────────────────────────────────────

def calcular_custo_hora(p: dict) -> float:
    """R$/hora total da máquina em operação.

    Aplica:
      * fator_encargos_trabalhistas (default 1.45) sobre operador + auxiliares
      * multiplicador de diesel do cenário (default 1.00)
    """
    cenario        = get_scenario(p.get("cenario_economico", "Realista"))
    diesel_mult    = cenario["diesel_mult"]
    fator_encargos = float(p.get("fator_encargos_trabalhistas", 1.45))

    custo_diesel = p["diesel_lh"] * p["preco_diesel"] * diesel_mult

    salario_total = (
        p["salario_operador"] + p["n_auxiliares"] * p["salario_auxiliar"]
    ) * fator_encargos
    custo_mao_obra = salario_total / p["horas_mes"]

    custo_manut = p["manutencao_mensal"] / p["horas_mes"]
    custo_depre = (p["depreciacao_anual"] / 12.0) / p["horas_mes"]

    return custo_diesel + custo_mao_obra + custo_manut + custo_depre


# ── Núcleo: cálculo por linha ──────────────────────────────────────────────

def calcular_linhas(
    gdf_candidatas: gpd.GeoDataFrame,
    params: dict,
) -> gpd.GeoDataFrame:
    """Aplica o modelo econômico a cada linha individualmente.

    Returns:
        GeoDataFrame com colunas econômicas + flags `excluida_curta` e
        `lucro_cessante`. Linhas curtas permanecem para serem visualizadas
        no mapa, mas têm `viavel = False`.
    """
    p              = params
    cenario        = get_scenario(p.get("cenario_economico", "Realista"))
    custo_h        = calcular_custo_hora(p)

    vmpm_p = p["velocidade_plantio_kmh"]      * 1000.0 / 60.0
    vmpm_d = p["velocidade_deslocamento_kmh"] * 1000.0 / 60.0
    tmf    = p["tempo_manobra_fixo_min"]
    esp    = p["espacamento"]

    # ── Ajustes por cenário ──────────────────────────────────────────────
    preco_efetivo_ton = (
        p["atr_medio_kgton"] * p["preco_atr_rs_kg"] * cenario["atr_mult"]
    )
    pegamento_eff = min(p["taxa_pegamento"] * cenario["pegamento_mult"], 100.0)

    fator_soca    = FATOR_SOCA.get(p.get("ciclo_soca", "Cana-planta"), 1.00)
    ganho_efetivo = p["ganho_esperado_tha"] * fator_soca

    ioi_min = float(p.get("ioi_minimo", 0.0))

    df = gdf_candidatas.copy()

    # ── Filtro de comprimento mínimo de linha ────────────────────────────
    comp_min_linha = float(p.get("comprimento_minimo_linha", 80.0))
    df["excluida_curta"] = df["comp_linha"] < comp_min_linha

    # ── Guard numérico ──────────────────────────────────────────────────
    df["soma_falhas"] = df["soma_falhas"].clip(upper=df["comp_linha"])
    comp_saudavel     = (df["comp_linha"] - df["soma_falhas"]).clip(lower=0)

    # ── Tempo (5 componentes) ───────────────────────────────────────────
    df["tempo_plantio_min"]      = df["soma_falhas"] / vmpm_p
    df["tempo_deslocamento_min"] = comp_saudavel / vmpm_d
    df["tempo_manobra_min"]      = tmf

    cap_m   = max(float(p.get("capacidade_carga_m", 400.0)), 1.0)
    t_carga = float(p.get("tempo_recarga_min", 20.0))
    df["tempo_recarga_min"] = (df["soma_falhas"] / cap_m) * t_carga

    t_transf = float(p.get("tempo_transferencia_talhao_min", 30.0))
    n_por_talhao = df.groupby("TALHAO")["FID"].transform("count").clip(lower=1)
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

    # ── Receita & custo ─────────────────────────────────────────────────
    df["area_falha_ha"] = df["soma_falhas"] * esp / 10_000

    df["receita_bruta"] = (
        df["area_falha_ha"]
        * ganho_efetivo
        * (pegamento_eff / 100.0)
        * preco_efetivo_ton
    )
    df["receita_liquida"] = df["receita_bruta"] * (1.0 - p["risco_climatico"] / 100.0)

    df["custo_maquina"] = custo_h * (df["tempo_total_min"] / 60.0)
    df["custo_insumos"] = df["area_falha_ha"] * (
        p["custo_muda_tha"] + p.get("custo_logistica_muda_ha", 0.0)
    )
    df["custo_total"] = df["custo_maquina"] + df["custo_insumos"]
    df["lucro"]       = df["receita_liquida"] - df["custo_total"]

    df["ioi"] = np.where(
        df["tempo_total_min"] > 0,
        df["lucro"] / (df["tempo_total_min"] / 60.0),
        -np.inf,
    )

    # ── Viabilidade: IOI + não curta ─────────────────────────────────────
    df["viavel"] = (df["ioi"] >= ioi_min) & (~df["excluida_curta"])

    # ── Lucro Cessante (oportunidade perdida) ────────────────────────────
    # Para linhas NÃO replantadas, projeta receita líquida perdida ao longo
    # dos próximos `anos_extensao` cortes (mantendo decaimento de soca).
    anos_extensao = float(p.get("anos_extensao_replantio", 1.5))
    df["lucro_cessante"] = np.where(
        ~df["viavel"],
        df["receita_liquida"] * anos_extensao,
        0.0,
    )

    # ── Ranking por talhão ──────────────────────────────────────────────
    df["ranking"] = (
        df.groupby("TALHAO")["ioi"]
        .rank(ascending=False, method="min")
        .fillna(9999)
        .astype(int)
    )

    return gpd.GeoDataFrame(df, geometry="geometry", crs=gdf_candidatas.crs)


# ── VPL / NPV ───────────────────────────────────────────────────────────────

def _vpl(fluxos: list[float], wacc_anual: float) -> float:
    """VPL descontado anualmente. fluxos[0] é caixa do ano 0 (presente)."""
    return float(sum(f / (1.0 + wacc_anual) ** t for t, f in enumerate(fluxos)))


def calcular_vpl_talhao(
    area_ha: float,
    custo_op_replantio: float,
    receita_liquida_replantio: float,
    custo_reforma_ha: float,
    produtividade_reforma_tha: float,
    ganho_esperado_tha: float,          # não usado no VPL — mantido por compatibilidade
    preco_efetivo_ton: float,
    pegamento_pct: float,
    risco_climatico_pct: float,
    soca_atual: str,
    anos_extensao_replantio: float,
    wacc_pct: float,
) -> dict[str, float | str]:
    """Análise diferencial: Reforma AGORA vs Replantio + Reforma Deferida.

    Premissa fundamental: após n = round(anos_extensao_replantio) anos, AMBOS
    os cenários possuem um talhão reformado idêntico. Os fluxos futuros comuns
    se cancelam — só os fluxos dentro da janela de n anos importam.

    Opção A — Reforma AGORA (janela de n anos):
        Ano 0 : −CAPEX  (area_ha × custo_reforma_ha)
        Anos 1..n : produção plena reformada (Cana-planta → soca crescente)
                    = area_ha × produtividade_reforma_tha × peg × preço × (1−risco)
                      × FATOR_SOCA[Cana-planta + t − 1]

    Opção B — Replantio Pontual + Reforma Deferida (janela de n anos):
        Ano 0 : −custo_op  (Kairos)
        Anos 1..n : produção atual (soca decaindo) + incremental das falhas
                    = area_ha × produtividade_reforma_tha × peg × preço × (1−risco)
                      × FATOR_SOCA[soca_atual + t − 1]
                    + receita_liquida_replantio / n
        Ano n (no fim): −CAPEX deferido  (entra no fluxo do ano n descontado)

    Resultado: VPL_A > VPL_B → Reforma vantajosa AGORA.
               VPL_B > VPL_A → Vale a pena adiar a reforma e replantar com o Kairos.

    Payback: custo_op / receita_anual_incremental  (retorno do investimento no Kairos).
    """
    wacc  = max(wacc_pct / 100.0, 0.0)
    peg   = pegamento_pct / 100.0
    risc  = 1.0 - risco_climatico_pct / 100.0
    capex = area_ha * custo_reforma_ha

    # Receita por ha/corte do talhão reformado (sem fator soca)
    receita_base_ha = produtividade_reforma_tha * peg * preco_efetivo_ton * risc

    n_anos = max(int(round(anos_extensao_replantio)), 1)  # janela de comparação

    try:
        idx_inicio = CICLO_ORDEM.index(soca_atual)
    except ValueError:
        idx_inicio = 0

    receita_anual_gap = receita_liquida_replantio / n_anos  # incremental Kairos/ano

    # ── Opção A: Reforma AGORA ─────────────────────────────────────────
    fluxos_reforma: list[float] = [-capex]
    for t in range(1, n_anos + 1):
        ciclo_idx = min(t - 1, len(CICLO_ORDEM) - 1)   # começa em Cana-planta
        fluxos_reforma.append(area_ha * receita_base_ha * FATOR_SOCA[CICLO_ORDEM[ciclo_idx]])
    vpl_reforma = _vpl(fluxos_reforma, wacc)

    # ── Opção B: Replantio + Reforma Deferida ─────────────────────────
    # O CAPEX deferido é embutido no fluxo do último ano da janela.
    fluxos_replantio: list[float] = [-custo_op_replantio]
    for t in range(1, n_anos + 1):
        idx  = min(idx_inicio + (t - 1), len(CICLO_ORDEM) - 1)
        rec_campo = area_ha * receita_base_ha * FATOR_SOCA[CICLO_ORDEM[idx]]
        capex_def = -capex if t == n_anos else 0.0      # paga o CAPEX no final da janela
        fluxos_replantio.append(rec_campo + receita_anual_gap + capex_def)
    vpl_replantio = _vpl(fluxos_replantio, wacc)

    # ── Decisão ────────────────────────────────────────────────────────
    if vpl_replantio <= 0 and vpl_reforma <= 0:
        decisao = "Nenhuma opção rentável"
    elif vpl_replantio > vpl_reforma:
        decisao = "REPLANTIO (VPL maior)"
    else:
        decisao = "REFORMA (VPL maior)"

    # Payback do Kairos: tempo para o incremento das falhas cobrir o custo op
    payback = None
    if custo_op_replantio > 0 and receita_anual_gap > 0:
        payback = custo_op_replantio / receita_anual_gap

    return {
        "vpl_reforma":   round(vpl_reforma, 2),
        "vpl_replantio": round(vpl_replantio, 2),
        "decisao_vpl":   decisao,
        "payback_anos":  round(payback, 2) if payback is not None else None,
    }


def calcular_vpl_por_talhao(
    gdf_linhas_eco: gpd.GeoDataFrame,
    gdf_contorno: gpd.GeoDataFrame | None,
    params: dict,
) -> pd.DataFrame:
    """Aplica calcular_vpl_talhao() a cada talhão do dataset.

    Retorna DataFrame com colunas: TALHAO, area_ha, vpl_reforma,
    vpl_replantio, decisao_vpl, payback_anos.
    """
    if gdf_contorno is None or len(gdf_contorno) == 0:
        return pd.DataFrame(columns=[
            "TALHAO", "area_ha", "vpl_reforma", "vpl_replantio",
            "decisao_vpl", "payback_anos",
        ])

    # Área por talhão (do contorno)
    campo_t = [c for c in gdf_contorno.columns if c != "geometry"][0]
    contorno = gdf_contorno[[campo_t, "geometry"]].copy()
    contorno["area_ha"] = contorno.geometry.area / 10_000
    contorno = contorno.rename(columns={campo_t: "TALHAO"})
    contorno["TALHAO"] = contorno["TALHAO"].astype(str)

    # Agregados por talhão (somente linhas viáveis = serão replantadas)
    viaveis = gdf_linhas_eco[gdf_linhas_eco["viavel"] == True].copy()
    if len(viaveis) > 0:
        agg = (
            viaveis
            .groupby("TALHAO", sort=True)
            .agg(
                custo_op       = ("custo_maquina",   "sum"),
                receita_liq    = ("receita_liquida", "sum"),
            )
            .reset_index()
        )
        agg["TALHAO"] = agg["TALHAO"].astype(str)
    else:
        agg = pd.DataFrame(columns=["TALHAO", "custo_op", "receita_liq"])

    base = contorno[["TALHAO", "area_ha"]].merge(agg, on="TALHAO", how="left").fillna(0.0)

    # Parâmetros econômicos uniformes
    cenario = get_scenario(params.get("cenario_economico", "Realista"))
    preco_efetivo_ton = (
        params["atr_medio_kgton"] * params["preco_atr_rs_kg"] * cenario["atr_mult"]
    )
    pegamento_eff = min(params["taxa_pegamento"] * cenario["pegamento_mult"], 100.0)

    resultados = []
    for _, row in base.iterrows():
        r = calcular_vpl_talhao(
            area_ha                    = row["area_ha"],
            custo_op_replantio         = row["custo_op"],
            receita_liquida_replantio  = row["receita_liq"],
            custo_reforma_ha           = float(params.get("custo_reforma_ha", 14000.0)),
            produtividade_reforma_tha  = float(params.get("produtividade_reforma_tha", 90.0)),
            ganho_esperado_tha         = params["ganho_esperado_tha"],
            preco_efetivo_ton          = preco_efetivo_ton,
            pegamento_pct              = pegamento_eff,
            risco_climatico_pct        = params["risco_climatico"],
            soca_atual                 = params.get("ciclo_soca", "Cana-planta"),
            anos_extensao_replantio    = params.get("anos_extensao_replantio", 1.5),
            wacc_pct                   = params.get("wacc_pct", 12.0),
        )
        resultados.append({"TALHAO": row["TALHAO"], "area_ha": row["area_ha"], **r})

    return pd.DataFrame(resultados)
