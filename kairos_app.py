"""
Kairos — Sistema de Apoio à Decisão para Replantio de Cana-de-Açúcar
Agricef Kairos  |  Versão 4.0

Pipeline linha a linha:
  gis_pipeline.py    → classificação espacial por percentual de falha
  economic_engine.py → IOI por linha (Índice Operacional Integrado = R$/h)
  export_utils.py    → exportação de SHP por talhão (linhas viáveis)
"""

import os

import base64
import pathlib
import streamlit as st


def _get_logo_b64() -> str:
    import base64
    p = pathlib.Path(__file__).parent / "agricef_logo.png"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""


# ---------------------------------------------------------------------------
# Authentication — runs before any heavy import or UI rendering
# ---------------------------------------------------------------------------

def _login_gate() -> None:
    """Exibe formulário de login e bloqueia o app se não autenticado."""
    if st.session_state.get("logged_in"):
        return

    st.set_page_config(
        page_title="Kairos DSS — Acesso Restrito",
        page_icon="🔒",
        layout="centered",
    )

    st.markdown(
        f'<div style="text-align:center">'
        f'<img src="data:image/png;base64,{_get_logo_b64()}" width="220"></div>'
        '<p style="text-align:center;color:#666;margin-top:12px">'
        'Sistema de Apoio à Decisão — Replantio de Cana-de-Açúcar</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    with st.form("form_login"):
        st.subheader("Acesso restrito")
        usuario = st.text_input("Usuário")
        senha   = st.text_input("Senha", type="password")
        entrar  = st.form_submit_button("Entrar", use_container_width=True, type="primary")

    if entrar:
        try:
            usuarios_auth: dict = dict(st.secrets["usuarios"])
        except Exception as e:
            import traceback, pathlib
            secrets_path = pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml"
            st.error(
                f"**Erro ao ler credenciais:** `{type(e).__name__}: {e}`\n\n"
                f"Arquivo esperado: `{secrets_path}`\n\n"
                f"Arquivo existe: `{secrets_path.exists()}`"
            )
            st.stop()

        if usuario in usuarios_auth and usuarios_auth[usuario] == senha:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos. Tente novamente.")

    st.stop()


_login_gate()


# ---------------------------------------------------------------------------
# Deferred imports — only reached after successful authentication
# ---------------------------------------------------------------------------

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
from streamlit_folium import st_folium

import economic_engine as eco
import export_utils
import gis_pipeline


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLASSE_CORES: dict = {
    "0-2":   "#1a9850",
    "2-4":   "#66bd63",
    "4-6":   "#a6d96a",
    "6-8":   "#d9ef8b",
    "8-10":  "#fee08b",
    "10-12": "#fdae61",
    "12-14": "#f46d43",
    "14-16": "#d73027",
    "16-18": "#a50026",
    "18-20": "#7f0000",
    ">20":   "#4d0000",
}

# IOI tiers for viable-line layer coloring
IOI_FAIXAS = [
    (0,    100,  "#a5d6a7", "0 – 100"),
    (100,  250,  "#4caf50", "100 – 250"),
    (250,  500,  "#1b5e20", "250 – 500"),
    (500,  1000, "#1565c0", "500 – 1.000"),
    (1000, None, "#7b1fa2", "> 1.000"),
]


def _ioi_cor(ioi_val: float) -> str:
    for lo, hi, cor, _ in IOI_FAIXAS:
        if hi is None or ioi_val < hi:
            return cor
    return IOI_FAIXAS[-1][2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_gis():
    for key in ("gdf_gis", "avisos_gis", "gdf_contorno", "gdf_linhas_eco"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> dict:
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{_get_logo_b64()}" width="180">',
        unsafe_allow_html=True,
    )
    st.sidebar.title("Kairos DSS")
    st.sidebar.caption("Sistema de Apoio à Decisão — Replantio de Cana")

    # ── Arquivos ──────────────────────────────────────────────────────────
    with st.sidebar.expander("📂 Arquivos de Entrada", expanded=True):
        f_contorno = st.file_uploader(
            "Contorno dos Talhões (.zip)", type=["zip"],
            key="up_contorno", on_change=_reset_gis,
        )
        f_linhas = st.file_uploader(
            "Linhas de Plantio (.zip)", type=["zip"],
            key="up_linhas", on_change=_reset_gis,
        )
        f_falhas = st.file_uploader(
            "Falhas de Drone (.zip)", type=["zip"],
            key="up_falhas", on_change=_reset_gis,
        )
        campo_talhao = st.text_input("Campo identificador do Talhão", value="TALHAO")

    # ── Parâmetros GIS ────────────────────────────────────────────────────
    with st.sidebar.expander("📐 Parâmetros GIS", expanded=False):
        buffer_falha = st.number_input(
            "Buffer nas falhas (m)", value=0.30, min_value=0.01, step=0.05,
            format="%.2f", on_change=_reset_gis,
        )
        min_falha = st.number_input(
            "Comprimento mínimo de falha (m)", value=1.50, min_value=0.10,
            step=0.10, format="%.2f", on_change=_reset_gis,
        )
        espacamento = st.number_input(
            "Espaçamento entre linhas (m)", value=1.50, min_value=0.50,
            step=0.10, format="%.2f", on_change=_reset_gis,
        )
        perc_falha_minimo = st.number_input(
            "% Falha mínima para entrar no modelo (%)",
            value=5.0, min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
            help="Linhas com % de falha abaixo deste valor são ignoradas antes do "
                 "cálculo econômico.",
        )

    # ── Filtros de Viabilidade ────────────────────────────────────────────
    with st.sidebar.expander("🎯 Filtros de Viabilidade", expanded=False):
        ioi_minimo = st.number_input(
            "IOI mínimo para viabilidade (R$/h)",
            value=50.0, min_value=0.0, step=10.0, format="%.0f",
            help="Linhas com IOI abaixo deste valor são marcadas como inviáveis. "
                 "Use 0 para aceitar qualquer IOI positivo.",
        )
        comprimento_minimo_linha = st.number_input(
            "Comprimento Mínimo de Linha (m)",
            value=80.0, min_value=0.0, step=10.0, format="%.0f",
            help="Linhas mais curtas que este limite são automaticamente excluídas "
                 "(razão manobra/m plantado proibitiva). Aparecem em cinza tracejado "
                 "no mapa para inspeção visual.",
        )

    # ── Cenário Econômico ─────────────────────────────────────────────────
    with st.sidebar.expander("🎲 Cenário Econômico", expanded=False):
        cenario_economico = st.radio(
            "Cenário",
            options=["Otimista", "Realista", "Pessimista"],
            index=1,
            help="Otimista: +15% ATR, −15% diesel, +10% pegamento. "
                 "Pessimista: −15% ATR, +15% diesel, −15% pegamento.",
            horizontal=True,
        )

    # ── Custos por hora ───────────────────────────────────────────────────
    with st.sidebar.expander("💰 Custos por Hora (Máquina)", expanded=False):
        diesel_lh         = st.number_input("Consumo diesel (L/h)",              value=8.0,     min_value=0.1,  step=0.5,    format="%.1f")
        preco_diesel      = st.number_input("Preço do diesel (R$/L)",             value=6.50,    min_value=0.01, step=0.10,   format="%.2f")
        salario_operador  = st.number_input("Salário do operador (R$/mês)",       value=3500.0,  min_value=0.0,  step=100.0,  format="%.2f")
        n_auxiliares      = st.number_input("Número de auxiliares",               value=1,       min_value=0,    step=1)
        salario_auxiliar  = st.number_input("Salário por auxiliar (R$/mês)",      value=2500.0,  min_value=0.0,  step=100.0,  format="%.2f")
        manutencao_mensal = st.number_input("Manutenção fixa mensal (R$/mês)",    value=800.0,    min_value=0.0,  step=50.0,    format="%.2f")
        depreciacao_anual = st.number_input("Depreciação anual (R$/ano)",         value=100000.0, min_value=0.0,  step=5000.0,  format="%.2f",
            help="Plantadora nova em uso severo: 80–120 k/ano. Calcule (preço − residual) ÷ vida útil.")
        horas_mes         = st.number_input("Horas trabalhadas por mês (h/mês)",  value=176.0,    min_value=1.0,  step=8.0,     format="%.0f")
        fator_encargos_trabalhistas = st.slider(
            "Fator de Encargos Trabalhistas",
            min_value=1.30, max_value=1.60, value=1.45, step=0.01, format="%.2f",
            help="Multiplicador sobre salário bruto para refletir INSS patronal (20%), "
                 "FGTS (8%), 13º, férias e adicionais. Padrão 1.45 = 45% de encargos.",
        )

    # ── Velocidade & Eficiência ───────────────────────────────────────────
    with st.sidebar.expander("⚡ Velocidade & Eficiência", expanded=False):
        velocidade_plantio_kmh = st.number_input(
            "Velocidade de Plantio — na falha (km/h)",
            value=2.5, min_value=0.5, step=0.5, format="%.1f",
            help="Velocidade da máquina durante o plantio dentro da linha de falha.",
        )
        velocidade_deslocamento_kmh = st.number_input(
            "Velocidade de Deslocamento — entre falhas (km/h)",
            value=7.0, min_value=0.5, step=0.5, format="%.1f",
            help="Velocidade da máquina percorrendo trechos sem falha dentro da linha.",
        )
        tempo_manobra_fixo_min = st.number_input(
            "Tempo de manobra de cabeceira por linha (min)",
            value=2.0, min_value=0.0, step=0.5, format="%.1f",
        )

    # ── Produção Agronômica ───────────────────────────────────────────────
    with st.sidebar.expander("🌾 Produção Agronômica", expanded=False):
        ciclo_soca = st.selectbox(
            "Ciclo / Soca",
            list(eco.FATOR_SOCA.keys()),
            index=0,
            help="Afeta o ganho esperado: socas mais velhas têm menor produtividade.",
        )
        ganho_esperado_tha = st.number_input(
            "Ganho esperado por replantio (t/ha de falha)",
            value=50.0, min_value=1.0, step=5.0, format="%.1f",
            help="Toneladas de cana recuperadas por hectare de área replantada. "
                 "Será multiplicado pelo fator do ciclo selecionado.",
        )
        atr_medio_kgton = st.number_input(
            "ATR médio da variedade (kg ATR / ton cana)",
            value=130.0, min_value=80.0, max_value=180.0, step=1.0, format="%.0f",
            help="Teor de Açúcar Total Recuperável da variedade plantada.",
        )
        preco_atr_rs_kg = st.number_input(
            "Preço do ATR (R$/kg ATR)",
            value=1.10, min_value=0.10, step=0.05, format="%.2f",
            help="Preço pago pela usina por kg de ATR. "
                 "Preço efetivo por tonelada = ATR × Preço ATR.",
        )
        st.caption(
            f"Preço efetivo: **R$ {atr_medio_kgton * preco_atr_rs_kg:.2f}/ton** "
            f"(ATR {atr_medio_kgton:.0f} × R${preco_atr_rs_kg:.2f}/kg)"
        )
        taxa_pegamento  = st.number_input("Taxa de pegamento / germinação (%)", value=85.0,  min_value=1.0, step=1.0,  format="%.1f")
        custo_muda_tha  = st.number_input("Custo de muda (R$/ha de falha)",     value=400.0, min_value=0.0, step=25.0, format="%.2f")
        custo_logistica_muda_ha = st.number_input(
            "Custo de logística de muda (R$/ha de falha)",
            value=80.0, min_value=0.0, step=10.0, format="%.2f",
            help="Frete + mão de obra de abastecimento do carretel no campo. "
                 "Adicionado ao custo de muda por hectare de falha.",
        )

    # ── Logística Operacional ─────────────────────────────────────────────
    with st.sidebar.expander("🚜 Logística Operacional", expanded=False):
        capacidade_carga_m = st.number_input(
            "Capacidade de carga (m de linha por carregamento)",
            value=400.0, min_value=50.0, step=50.0, format="%.0f",
            help="Metros de falha que a máquina planta antes de precisar recarregar mudas.",
        )
        tempo_recarga_min = st.number_input(
            "Tempo de recarga de mudas (min)",
            value=20.0, min_value=1.0, step=1.0, format="%.0f",
            help="Tempo parado para reabastecimento do carretel de mudas.",
        )
        tempo_transferencia_talhao_min = st.number_input(
            "Tempo de transferência entre talhões (min)",
            value=30.0, min_value=0.0, step=5.0, format="%.0f",
            help="Deslocamento médio do trator entre um talhão e outro (carreador, porteira, estrada interna).",
        )
        custo_reforma_ha = st.number_input(
            "Custo Médio da Reforma (R$/ha)",
            value=14000.0, min_value=1000.0, step=500.0, format="%.2f",
            help="Custo total estimado de reformar o talhão inteiro (preparo, mudas, plantio) por hectare.",
        )
        limite_custo_reforma_pct = st.number_input(
            "Limite de Custo Operacional para Reforma (%)",
            value=80.0, min_value=10.0, max_value=200.0, step=5.0, format="%.0f",
            help="Se o custo operacional total do Kairos naquele talhão ultrapassar este % "
                 "do custo de reforma total, sugere-se reforma em vez de replantio.",
        )

    # ── Riscos ────────────────────────────────────────────────────────────
    with st.sidebar.expander("⚠️ Riscos", expanded=False):
        risco_climatico = st.number_input(
            "Desconto de risco climático (%)",
            value=10.0, min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
            help="Percentual de redução da receita por risco de janela climática.",
        )

    # ── Análise Financeira (VPL) ──────────────────────────────────────────
    with st.sidebar.expander("📈 Análise Financeira (VPL)", expanded=False):
        wacc_pct = st.number_input(
            "Taxa de Desconto / WACC (% a.a.)",
            value=12.0, min_value=0.0, max_value=40.0, step=0.5, format="%.1f",
            help="Custo médio ponderado de capital — usado para descontar fluxos "
                 "futuros no cálculo do VPL. Usinas típicas: 10–15% a.a.",
        )
        anos_extensao_replantio = st.slider(
            "Anos de Extensão pelo Replantio",
            min_value=1.0, max_value=3.0, value=1.5, step=0.5, format="%.1f",
            help="Quantas safras adicionais o replantio do Kairos preserva nas "
                 "linhas replantadas. Tipicamente 1–2 cortes.",
        )
        produtividade_reforma_tha = st.number_input(
            "Produtividade do Talhão Reformado (t/ha)",
            value=90.0, min_value=10.0, max_value=200.0, step=5.0, format="%.1f",
            help="Produtividade PLENA do talhão após Reforma Total (toda a área, "
                 "Cana-planta). Diferente do 'Ganho Esperado' do Kairos, que é o "
                 "ganho incremental por ha de FALHA replantada. "
                 "Recomendado: 70–120 t/ha (consulte histórico da variedade).",
        )

    # ── Exportação ────────────────────────────────────────────────────────
    with st.sidebar.expander("📁 Exportação", expanded=True):
        pasta_saida = st.text_input(
            "Pasta de saída dos SHPs",
            value=os.path.join(os.path.expanduser("~"), "kairos_saida"),
            help="Caminho completo da pasta onde os shapefiles serão gravados.",
        )

    return dict(
        f_contorno=f_contorno, f_linhas=f_linhas, f_falhas=f_falhas,
        campo_talhao=(campo_talhao.strip() or "TALHAO"),
        buffer_falha=buffer_falha, min_falha=min_falha, espacamento=espacamento,
        perc_falha_minimo=perc_falha_minimo,
        ioi_minimo=ioi_minimo,
        comprimento_minimo_linha=comprimento_minimo_linha,
        cenario_economico=cenario_economico,
        diesel_lh=diesel_lh, preco_diesel=preco_diesel,
        salario_operador=salario_operador, n_auxiliares=int(n_auxiliares),
        salario_auxiliar=salario_auxiliar, manutencao_mensal=manutencao_mensal,
        depreciacao_anual=depreciacao_anual, horas_mes=horas_mes,
        fator_encargos_trabalhistas=fator_encargos_trabalhistas,
        velocidade_plantio_kmh=velocidade_plantio_kmh,
        velocidade_deslocamento_kmh=velocidade_deslocamento_kmh,
        tempo_manobra_fixo_min=tempo_manobra_fixo_min,
        ciclo_soca=ciclo_soca,
        ganho_esperado_tha=ganho_esperado_tha,
        atr_medio_kgton=atr_medio_kgton,
        preco_atr_rs_kg=preco_atr_rs_kg,
        taxa_pegamento=taxa_pegamento,
        custo_muda_tha=custo_muda_tha,
        custo_logistica_muda_ha=custo_logistica_muda_ha,
        capacidade_carga_m=capacidade_carga_m,
        tempo_recarga_min=tempo_recarga_min,
        tempo_transferencia_talhao_min=tempo_transferencia_talhao_min,
        custo_reforma_ha=custo_reforma_ha,
        limite_custo_reforma_pct=limite_custo_reforma_pct,
        risco_climatico=risco_climatico,
        wacc_pct=wacc_pct,
        anos_extensao_replantio=anos_extensao_replantio,
        produtividade_reforma_tha=produtividade_reforma_tha,
        pasta_saida=pasta_saida.strip(),
    )


# ---------------------------------------------------------------------------
# Dashboard components
# ---------------------------------------------------------------------------

def render_metrics(
    gdf_linhas_eco: gpd.GeoDataFrame,
    gdf_gis: gpd.GeoDataFrame,
    espacamento: float,
    custo_h: float = 0.0,
    params: dict | None = None,
) -> None:
    n_total   = len(gdf_linhas_eco)
    n_viaveis = int(gdf_linhas_eco["viavel"].sum())
    mask      = gdf_linhas_eco["viavel"]
    lucro_total = gdf_linhas_eco.loc[mask, "lucro"].sum()
    ioi_max     = gdf_linhas_eco.loc[mask, "ioi"].max()     if n_viaveis > 0 else 0.0
    ef_media    = gdf_linhas_eco.loc[mask, "eficiencia_pct"].mean() if n_viaveis > 0 else 0.0

    # Metric 1 — total gap area across all lines (before perc_falha filter)
    area_total_falhas_ha = gdf_gis["soma_falhas"].sum() * espacamento / 10_000

    # Metric 2 — planting throughput of viable lines only
    if n_viaveis > 0:
        area_viaveis_ha   = gdf_linhas_eco.loc[mask, "soma_falhas"].sum() * espacamento / 10_000
        tempo_h_viaveis   = gdf_linhas_eco.loc[mask, "tempo_total_min"].sum() / 60.0
        rendimento_ha_h   = area_viaveis_ha / tempo_h_viaveis if tempo_h_viaveis > 0 else 0.0
    else:
        rendimento_ha_h = 0.0

    # Break-even yield: minimum ha/h to cover machine cost (R$/h)
    rendimento_min_hah = None
    if params and custo_h > 0:
        fator_soca  = eco.FATOR_SOCA.get(params.get("ciclo_soca", "Cana-planta"), 1.0)
        ganho_aj    = params["ganho_esperado_tha"] * fator_soca
        preco_ton   = params["atr_medio_kgton"] * params["preco_atr_rs_kg"]
        peg         = params["taxa_pegamento"] / 100.0
        risco       = params["risco_climatico"] / 100.0
        custo_ins   = params["custo_muda_tha"] + params.get("custo_logistica_muda_ha", 0.0)
        receita_liq_por_ha = ganho_aj * peg * preco_ton * (1.0 - risco)
        margem_por_ha      = receita_liq_por_ha - custo_ins
        if margem_por_ha > 0:
            rendimento_min_hah = custo_h / margem_por_ha

    row1 = st.columns(5)
    row1[0].metric("Linhas candidatas",    f"{n_total}")
    row1[1].metric("Linhas viáveis",       f"{n_viaveis}",
                   delta=f"{n_viaveis/n_total*100:.0f}%" if n_total else "0%")
    row1[2].metric("Lucro total estimado", f"R$ {lucro_total:,.2f}")
    row1[3].metric("Melhor IOI",           f"R$ {ioi_max:,.0f}/h")
    row1[4].metric("Eficiência média",     f"{ef_media:.1f}%",
                   help="Tempo de plantio / Tempo total das linhas viáveis.")

    row2 = st.columns(5)
    row2[0].metric(
        "Área Total de Falhas",
        f"{area_total_falhas_ha:.4f} ha",
        help="Soma dos segmentos de falha válidos (> comprimento mínimo) × espaçamento entre linhas.",
    )
    row2[1].metric(
        "Rendimento de Plantio",
        f"{rendimento_ha_h:.3f} ha/h",
        help="Área de falha das linhas viáveis ÷ tempo total de operação das linhas viáveis.",
    )
    if rendimento_min_hah is not None:
        row2[2].metric(
            "Rendimento Mínimo",
            f"{rendimento_min_hah:.3f} ha/h",
            help="Rendimento mínimo de plantio (ha/h) para cobrir todos os custos "
                 "fixos e variáveis da máquina sem operar no prejuízo. "
                 "Fórmula: Custo/hora ÷ Margem líquida por ha de falha.",
        )
    elif params:
        row2[2].metric(
            "Rendimento Mínimo",
            "Inviável",
            help="Margem por ha de falha negativa — operação sempre no prejuízo com os parâmetros atuais.",
        )

    # ── Lucro Cessante e linhas curtas ───────────────────────────────────
    lucro_cessante_total = float(gdf_linhas_eco.get("lucro_cessante", pd.Series([0.0])).sum())
    n_curtas = int(gdf_linhas_eco.get("excluida_curta", pd.Series([False])).sum())

    row2[3].metric(
        "Lucro Cessante",
        f"R$ {lucro_cessante_total:,.2f}",
        help="Receita líquida perdida nas linhas NÃO replantadas (inviáveis + curtas), "
             "projetada para os anos de extensão configurados. "
             "Quanto mais alto, maior o custo de oportunidade de deixar essas linhas "
             "sem replantio até a próxima reforma.",
    )
    row2[4].metric(
        "Linhas Curtas Excluídas",
        f"{n_curtas}",
        help="Linhas mais curtas que o comprimento mínimo configurado — "
             "razão manobra/m plantado proibitiva. Aparecem em cinza tracejado no mapa.",
    )


def _legenda_html() -> str:
    # Section 1 — class % colors
    itens_classe = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="display:inline-block;width:22px;height:4px;background:{cor};'
        f'border-radius:2px"></span>'
        f'<span style="font-size:10px">{cls}%</span></div>'
        for cls, cor in CLASSE_CORES.items()
    )
    # Section 2 — IOI tier colors
    itens_ioi = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="display:inline-block;width:22px;height:4px;background:{cor};'
        f'border-radius:2px"></span>'
        f'<span style="font-size:10px">{label} R$/h</span></div>'
        for _, _, cor, label in IOI_FAIXAS
    )
    return (
        '<div style="position:absolute;bottom:30px;right:10px;z-index:9999;'
        'background:rgba(255,255,255,0.95);padding:8px 12px;border-radius:8px;'
        'border:1px solid #bbb;line-height:1.4;font-family:sans-serif;'
        'box-shadow:2px 2px 6px rgba(0,0,0,.2);min-width:150px">'
        "<b style='font-size:11px;display:block;margin-bottom:3px'>% Falha (Camada 1)</b>"
        + itens_classe
        + "<hr style='margin:5px 0;border:none;border-top:1px solid #ddd'/>"
        "<b style='font-size:11px;display:block;margin-bottom:3px'>IOI — Linhas Viáveis (Camada 2)</b>"
        + itens_ioi
        + "<hr style='margin:5px 0;border:none;border-top:1px solid #ddd'/>"
        '<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        '<span style="display:inline-block;width:22px;height:0;border-top:2px dashed #777"></span>'
        '<span style="font-size:10px">Curta (excluída)</span></div>'
        + "</div>"
    )


def render_map(
    gdf_gis: gpd.GeoDataFrame,
    gdf_linhas_eco: gpd.GeoDataFrame,
    gdf_contorno: gpd.GeoDataFrame | None = None,
) -> None:

    def _to4326(gdf):
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            return gdf.to_crs(4326)
        return gdf

    # ── Layer 1: all lines colored by gap class ───────────────────────────
    _gdf1 = gdf_gis[["geometry", "classe", "TALHAO", "comp_linha", "perc_falhas"]].copy()
    # Sanitize: replace inf/-inf with NaN so to_json() produces valid JSON
    _gdf1["perc_falhas"] = _gdf1["perc_falhas"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    _gdf1["comp_linha"]  = _gdf1["comp_linha"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    todas = _to4326(_gdf1)
    todas["_perc_fmt"] = todas["perc_falhas"].round(1).astype(str) + "%"
    todas["_color"]    = todas["classe"].map(CLASSE_CORES).fillna("#808080")

    if todas.empty:
        st.warning("Nenhuma linha encontrada para exibir no mapa. Verifique os arquivos enviados.")
        return

    # ── Layer 2: viable lines colored by IOI tier ─────────────────────────
    viaveis = gdf_linhas_eco[gdf_linhas_eco["viavel"] == True].copy()
    viaveis_4326 = None
    if len(viaveis) > 0:
        _gdf2 = viaveis[["geometry", "TALHAO", "FID", "classe",
                          "soma_falhas", "perc_falhas", "ioi",
                          "eficiencia_pct", "lucro", "ranking"]].copy()
        # Sanitize numeric columns — replace inf/-inf with finite values for JSON
        for _col in ["ioi", "lucro", "eficiencia_pct", "perc_falhas", "soma_falhas"]:
            _gdf2[_col] = _gdf2[_col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        viaveis_4326 = _to4326(_gdf2)
        viaveis_4326["_color"]     = viaveis_4326["ioi"].apply(_ioi_cor)
        viaveis_4326["_ioi_fmt"]   = "R$ " + viaveis_4326["ioi"].round(0).astype(int).astype(str) + "/h"
        viaveis_4326["_ef_fmt"]    = viaveis_4326["eficiencia_pct"].round(1).astype(str) + "%"
        viaveis_4326["_falha_fmt"] = viaveis_4326["perc_falhas"].round(1).astype(str) + "%"
        viaveis_4326["_lucro_fmt"] = "R$ " + viaveis_4326["lucro"].round(2).astype(str)

    # ── Layer 3: excluded short rows (grey/dashed) ────────────────────────
    curtas_4326 = None
    if "excluida_curta" in gdf_linhas_eco.columns:
        curtas = gdf_linhas_eco[gdf_linhas_eco["excluida_curta"] == True].copy()
        if len(curtas) > 0:
            _cols3 = [c for c in ["geometry", "TALHAO", "FID", "comp_linha",
                                   "perc_falhas", "classe"] if c in curtas.columns]
            _gdf3 = curtas[_cols3].copy()
            for _col in ["comp_linha", "perc_falhas"]:
                if _col in _gdf3.columns:
                    _gdf3[_col] = _gdf3[_col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
            curtas_4326 = _to4326(_gdf3)
            curtas_4326["_comp_fmt"]  = curtas_4326.get("comp_linha",
                pd.Series(["0"] * len(curtas_4326))).round(1).astype(str) + " m"
            curtas_4326["_perc_fmt"]  = curtas_4326.get("perc_falhas",
                pd.Series(["0"] * len(curtas_4326))).round(1).astype(str) + "%"

    bounds = todas.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    m = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron")

    # ── Layer 0: stand boundary ───────────────────────────────────────────
    if gdf_contorno is not None and len(gdf_contorno) > 0:
        folium.GeoJson(
            _to4326(gdf_contorno[["geometry"]].copy()).to_json(),
            name="Contorno dos Talhões",
            style_function=lambda _: {
                "fillColor": "#a5d6a7", "fillOpacity": 0.10,
                "color": "#2e7d32", "weight": 2.5, "dashArray": "6 3",
            },
            show=True,
        ).add_to(m)

    # ── Layer 1 ───────────────────────────────────────────────────────────
    folium.GeoJson(
        todas.to_json(),
        name="Todas as linhas (% Falha)",
        style_function=lambda feat: {
            "color":   feat["properties"].get("_color", "#808080"),
            "weight":  1.5,
            "opacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["TALHAO", "classe", "_perc_fmt"],
            aliases=["Talhão:", "Classe:", "% Falha:"],
            sticky=True,
        ),
        show=True,
    ).add_to(m)

    # ── Layer 2 (off by default) ──────────────────────────────────────────
    if viaveis_4326 is not None:
        folium.GeoJson(
            viaveis_4326.to_json(),
            name="Linhas Viáveis (IOI)",
            style_function=lambda feat: {
                "color":   feat["properties"].get("_color", "#4caf50"),
                "weight":  4,
                "opacity": 1.0,
            },
            highlight_function=lambda feat: {"weight": 6, "opacity": 1.0},
            tooltip=folium.GeoJsonTooltip(
                fields=["TALHAO", "FID", "classe", "_falha_fmt",
                        "_ioi_fmt", "_ef_fmt", "_lucro_fmt"],
                aliases=["Talhão:", "FID:", "Classe:", "% Falha:",
                         "IOI:", "Eficiência:", "Lucro:"],
                sticky=True,
            ),
            show=False,
        ).add_to(m)

    # ── Layer 3: excluded short rows ──────────────────────────────────────
    if curtas_4326 is not None and len(curtas_4326) > 0:
        # Only include tooltip fields that actually exist in the dataframe
        _tip3_fields   = [f for f in ["TALHAO", "FID", "_comp_fmt", "_perc_fmt", "classe"]
                          if f in curtas_4326.columns]
        _tip3_aliases  = {
            "TALHAO": "Talhão:", "FID": "FID:",
            "_comp_fmt": "Comprimento:", "_perc_fmt": "% Falha:", "classe": "Classe:",
        }
        folium.GeoJson(
            curtas_4326.to_json(),
            name="Linhas Curtas Excluídas",
            style_function=lambda _: {
                "color":     "#777777",
                "weight":    2,
                "opacity":   0.85,
                "dashArray": "4 4",
            },
            tooltip=folium.GeoJsonTooltip(
                fields=_tip3_fields,
                aliases=[_tip3_aliases[f] for f in _tip3_fields],
                sticky=True,
            ) if _tip3_fields else None,
            show=True,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element(_legenda_html()))
    st_folium(m, use_container_width=True, height=580, returned_objects=[])


def render_ranking(gdf_linhas_eco: gpd.GeoDataFrame, ioi_minimo: float = 0.0) -> None:
    st.subheader("🏆 Ranking de Linhas por IOI")
    st.caption(
        "Ordenado pelo IOI — Índice Operacional Integrado (R$/hora). "
        f"Viável = IOI ≥ R$ {ioi_minimo:.0f}/h."
    )

    # ── Histograma de IOI ─────────────────────────────────────────────────
    import math
    ioi_vals = gdf_linhas_eco["ioi"].replace([np.inf, -np.inf], np.nan).dropna()
    if len(ioi_vals) > 1:
        bin_size = 50
        ioi_min  = math.floor(ioi_vals.min() / bin_size) * bin_size
        ioi_max  = math.ceil(ioi_vals.max()  / bin_size) * bin_size + bin_size
        bins     = list(range(int(ioi_min), int(ioi_max) + 1, bin_size))
        counts   = pd.cut(ioi_vals, bins=bins, right=False).value_counts().sort_index()
        labels   = [f"{int(b.left)}" for b in counts.index]
        cores_bar = ["#d32f2f" if float(b.left) < ioi_minimo else "#2e7d32"
                     for b in counts.index]

        bar_html = '<div style="display:flex;align-items:flex-end;gap:3px;height:80px;margin-bottom:4px">'
        max_c = max(counts.values) if max(counts.values) > 0 else 1
        for cnt, cor in zip(counts.values, cores_bar):
            h = max(4, int(cnt / max_c * 72))
            bar_html += (
                f'<div style="flex:1;height:{h}px;background:{cor};'
                f'border-radius:2px 2px 0 0;min-width:8px"></div>'
            )
        bar_html += "</div>"
        bar_html += (
            '<div style="display:flex;gap:3px">'
            + "".join(
                f'<div style="flex:1;font-size:8px;text-align:center;color:#555">'
                f'{labels[i]}</div>'
                for i in range(0, len(labels), max(1, len(labels) // 8))
            )
            + "</div>"
        )
        legenda_hist = (
            '<div style="margin-top:6px;font-size:9px;color:#555">'
            '<span style="background:#d32f2f;padding:2px 6px;border-radius:3px;color:white">Inviável</span>'
            f'&nbsp;&nbsp;<span style="background:#2e7d32;padding:2px 6px;border-radius:3px;color:white">'
            f'Viável (IOI &ge; R${ioi_minimo:.0f}/h)</span></div>'
        )
        with st.expander("📊 Distribuição de IOI", expanded=True):
            st.markdown(
                f'<div style="background:#f5f5f5;padding:12px;border-radius:8px;'
                f'border:1px solid #e0e0e0">'
                f'<b style="font-size:11px">IOI (R$/h) — intervalos de R$50/h</b><br>'
                f'{bar_html}{legenda_hist}</div>',
                unsafe_allow_html=True,
            )

    # ── Tabela ────────────────────────────────────────────────────────────
    df = gdf_linhas_eco.drop(columns=["geometry"], errors="ignore").copy()
    df = df.sort_values("ioi", ascending=False)
    df = df.rename(columns={
        "ranking":        "Rank",
        "TALHAO":         "Talhão",
        "FID":            "FID",
        "comp_linha":     "Compr. Linha (m)",
        "soma_falhas":    "Falhas (m)",
        "perc_falhas":    "% Falha",
        "classe":         "Classe",
        "area_falha_ha":  "Área Falha (ha)",
        "tempo_plantio_min":      "T. Plantio (min)",
        "tempo_deslocamento_min": "T. Desloc. (min)",
        "tempo_manobra_min":      "T. Manobra (min)",
        "tempo_total_min":        "T. Total (min)",
        "eficiencia_pct": "Eficiência (%)",
        "receita_liquida":"Receita Líq. (R$)",
        "custo_total":    "Custo Total (R$)",
        "lucro":          "Lucro (R$)",
        "ioi":            "IOI (R$/h)",
        "viavel":         "Viável",
    })
    if "Viável" in df.columns:
        df["Viável"] = df["Viável"].map({True: "SIM", False: "NÃO"})

    col_order = [
        "Rank", "Talhão", "FID", "Compr. Linha (m)", "Falhas (m)", "% Falha",
        "Classe", "Área Falha (ha)",
        "T. Plantio (min)", "T. Desloc. (min)", "T. Manobra (min)", "T. Total (min)",
        "Eficiência (%)", "Receita Líq. (R$)", "Custo Total (R$)",
        "Lucro (R$)", "IOI (R$/h)", "Viável",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    fmt = {
        "Compr. Linha (m)":  "{:,.1f}",
        "Falhas (m)":        "{:,.1f}",
        "% Falha":           "{:.1f}%",
        "Área Falha (ha)":   "{:.4f}",
        "T. Plantio (min)":  "{:.1f}",
        "T. Desloc. (min)":  "{:.1f}",
        "T. Manobra (min)":  "{:.1f}",
        "T. Total (min)":    "{:.1f}",
        "Eficiência (%)":    "{:.1f}%",
        "Receita Líq. (R$)": "R$ {:,.2f}",
        "Custo Total (R$)":  "R$ {:,.2f}",
        "Lucro (R$)":        "R$ {:,.2f}",
        "IOI (R$/h)":        "R$ {:,.0f}",
    }

    def _cor_linha(row):
        bg = "#e8f5e9" if str(row.get("Viável", "")) == "SIM" else "#fce4e4"
        return [f"background-color: {bg}"] * len(row)

    MAX_ROWS = 2000
    if len(df) > MAX_ROWS:
        st.warning(
            f"Exibindo os primeiros {MAX_ROWS} de {len(df)} linhas para evitar lentidão no navegador. "
            "Exporte o SHP para análise completa."
        )
        df = df.head(MAX_ROWS)
    st.dataframe(
        df.style.apply(_cor_linha, axis=1).format(fmt, na_rep="—"),
        use_container_width=True,
        height=min(45 * (len(df) + 2), 600),
    )


def render_por_talhao(
    gdf_linhas_eco: gpd.GeoDataFrame,
    gdf_gis: gpd.GeoDataFrame,
    espacamento: float,
    gdf_contorno: gpd.GeoDataFrame | None = None,
    custo_reforma_ha: float = 14000.0,
    limite_custo_reforma_pct: float = 80.0,
) -> None:
    st.subheader("📊 Resumo por Talhão")

    viaveis = gdf_linhas_eco[gdf_linhas_eco["viavel"] == True]

    # Total gap area per talhão — from full GIS layer (before perc_falha filter)
    area_talhao = (
        gdf_gis
        .groupby("TALHAO", sort=True)["soma_falhas"]
        .sum()
        .reset_index()
        .rename(columns={"soma_falhas": "_soma_falhas_total"})
    )
    area_talhao["Area_Falhas_ha"] = area_talhao["_soma_falhas_total"] * espacamento / 10_000

    # Planting throughput per talhão — viable rows only
    if len(viaveis) > 0:
        rend_talhao = (
            viaveis
            .groupby("TALHAO", sort=True)
            .agg(
                _soma_viaveis = ("soma_falhas",    "sum"),
                _tempo_min    = ("tempo_total_min", "sum"),
            )
            .reset_index()
        )
        rend_talhao["Rendimento_ha_h"] = (
            rend_talhao["_soma_viaveis"] * espacamento / 10_000
            / (rend_talhao["_tempo_min"] / 60.0).replace(0, np.nan)
        )
    else:
        rend_talhao = pd.DataFrame(columns=["TALHAO", "Rendimento_ha_h"])

    resumo_total = (
        gdf_linhas_eco
        .groupby("TALHAO", sort=True)
        .agg(
            Total_Linhas = ("FID",         "count"),
            Falhas_m     = ("soma_falhas", "sum"),
        )
        .reset_index()
    )
    resumo_viaveis = (
        viaveis
        .groupby("TALHAO", sort=True)
        .agg(
            Linhas_Viaveis = ("FID",            "count"),
            Lucro_Total    = ("lucro",           "sum"),
            IOI_Medio      = ("ioi",             "mean"),
            Efic_Media     = ("eficiencia_pct",  "mean"),
        )
        .reset_index()
    )

    resumo_total["TALHAO"]   = resumo_total["TALHAO"].astype(str)
    resumo_viaveis["TALHAO"] = resumo_viaveis["TALHAO"].astype(str)
    area_talhao["TALHAO"]    = area_talhao["TALHAO"].astype(str)
    rend_talhao["TALHAO"]    = rend_talhao["TALHAO"].astype(str) if len(rend_talhao) > 0 else rend_talhao

    resumo = resumo_total.merge(resumo_viaveis, on="TALHAO", how="left").fillna(0)
    resumo = resumo.merge(area_talhao[["TALHAO", "Area_Falhas_ha"]], on="TALHAO", how="left").fillna(0)
    resumo = resumo.merge(rend_talhao[["TALHAO", "Rendimento_ha_h"]], on="TALHAO", how="left").fillna(0)

    resumo["Pct_Viaveis"] = (
        resumo["Linhas_Viaveis"] / resumo["Total_Linhas"] * 100
    ).round(1)
    # Custo operacional por talhão (soma do custo de máquina de todas as linhas candidatas)
    custo_op = (
        gdf_linhas_eco
        .groupby("TALHAO", sort=True)["custo_maquina"]
        .sum()
        .reset_index()
        .rename(columns={"custo_maquina": "_custo_op"})
    )
    resumo = resumo.merge(custo_op, on="TALHAO", how="left").fillna(0)

    # Área do talhão em ha — vem do contorno dissolvido
    # Cast TALHAO to str everywhere to avoid int32/str merge conflict
    resumo["TALHAO"] = resumo["TALHAO"].astype(str)
    if gdf_contorno is not None and len(gdf_contorno) > 0:
        campo_t = [c for c in gdf_contorno.columns if c != "geometry"][0]
        area_geo = gdf_contorno[[campo_t, "geometry"]].copy()
        area_geo["_area_ha"] = area_geo.geometry.area / 10_000
        area_geo = area_geo.rename(columns={campo_t: "TALHAO"})
        area_geo["TALHAO"] = area_geo["TALHAO"].astype(str)
        resumo = resumo.merge(area_geo[["TALHAO", "_area_ha"]], on="TALHAO", how="left").fillna(0)
    else:
        resumo["_area_ha"] = 0.0

    # Custo total de reforma por talhão
    resumo["_custo_reforma"] = resumo["_area_ha"] * custo_reforma_ha
    resumo["_limite_reforma"] = resumo["_custo_reforma"] * (limite_custo_reforma_pct / 100.0)

    def _rec(row):
        if row["_custo_reforma"] > 0 and row["_custo_op"] >= row["_limite_reforma"]:
            return "⚠️ SUGERIR REFORMA"
        return "✅ REPLANTIO"

    resumo["Recomendação"] = resumo.apply(_rec, axis=1)
    resumo["Custo Op. (R$)"]    = resumo["_custo_op"]
    resumo["Custo Reforma (R$)"] = resumo["_custo_reforma"]

    resumo = resumo.rename(columns={
        "TALHAO":          "Talhão",
        "Total_Linhas":    "Total Linhas",
        "Falhas_m":        "Total Falhas (m)",
        "Area_Falhas_ha":  "Área Falhas (ha)",
        "Linhas_Viaveis":  "Linhas Viáveis",
        "Pct_Viaveis":     "% Viáveis",
        "Lucro_Total":     "Lucro Estimado (R$)",
        "IOI_Medio":       "IOI Médio (R$/h)",
        "Efic_Media":      "Eficiência Média (%)",
        "Rendimento_ha_h": "Rendimento (ha/h)",
    })

    col_order = [
        "Talhão", "Recomendação", "Total Linhas", "Total Falhas (m)",
        "Área Falhas (ha)", "Linhas Viáveis", "% Viáveis",
        "Custo Op. (R$)", "Custo Reforma (R$)",
        "Lucro Estimado (R$)", "IOI Médio (R$/h)",
        "Eficiência Média (%)", "Rendimento (ha/h)",
    ]
    resumo = resumo[[c for c in col_order if c in resumo.columns]]

    # Highlight reforma rows
    def _cor_reforma(row):
        bg = "#fff3e0" if "REFORMA" in str(row.get("Recomendação", "")) else ""
        return [f"background-color:{bg}" if bg else "" for _ in row]

    reformas = resumo["Recomendação"].str.contains("REFORMA").sum() if "Recomendação" in resumo.columns else 0
    if reformas > 0:
        st.warning(
            f"**{reformas} talhão(ões)**: custo operacional do Kairos ≥ {limite_custo_reforma_pct:.0f}% "
            f"do custo de reforma (R$ {custo_reforma_ha:,.0f}/ha) — avalie reforma total."
        )

    st.dataframe(
        resumo.style.apply(_cor_reforma, axis=1).format({
            "Total Falhas (m)":    "{:,.1f}",
            "Área Falhas (ha)":    "{:.4f}",
            "% Viáveis":           "{:.1f}%",
            "Lucro Estimado (R$)": "R$ {:,.2f}",
            "IOI Médio (R$/h)":    "R$ {:,.0f}",
            "Eficiência Média (%)":"{:.1f}%",
            "Rendimento (ha/h)":   "{:.3f}",
            "Custo Op. (R$)":      "R$ {:,.2f}",
            "Custo Reforma (R$)":  "R$ {:,.2f}",
        }, na_rep="—"),
        use_container_width=True,
    )


def render_vpl(
    gdf_linhas_eco: gpd.GeoDataFrame,
    gdf_contorno: gpd.GeoDataFrame | None,
    params: dict,
) -> None:
    st.subheader("📈 VPL 5 anos — Replantio vs Reforma Total")
    st.caption(
        f"Cenário: **{params.get('cenario_economico','Realista')}** | "
        f"WACC: **{params.get('wacc_pct',12.0):.1f}% a.a.** | "
        f"Extensão pelo replantio: **{params.get('anos_extensao_replantio',1.5):.1f} anos** | "
        f"Soca atual: **{params.get('ciclo_soca','Cana-planta')}**"
    )

    if gdf_contorno is None or len(gdf_contorno) == 0:
        st.warning("Contorno indisponível — VPL por talhão requer geometria do contorno.")
        return

    df_vpl = eco.calcular_vpl_por_talhao(gdf_linhas_eco, gdf_contorno, params)
    if len(df_vpl) == 0:
        st.info("Nenhum talhão para analisar.")
        return

    # ── Resumo agregado ──────────────────────────────────────────────────
    vpl_ref_total = df_vpl["vpl_reforma"].sum()
    vpl_rep_total = df_vpl["vpl_replantio"].sum()
    n_reforma  = int(df_vpl["decisao_vpl"].str.contains("REFORMA").sum())
    n_replant  = int(df_vpl["decisao_vpl"].str.contains("REPLANTIO").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VPL Reforma (Σ)",   f"R$ {vpl_ref_total:,.0f}")
    col2.metric("VPL Replantio (Σ)", f"R$ {vpl_rep_total:,.0f}",
                delta=f"R$ {vpl_rep_total - vpl_ref_total:,.0f} vs reforma")
    col3.metric("Talhões → Reforma",   f"{n_reforma}")
    col4.metric("Talhões → Replantio", f"{n_replant}")

    st.markdown(
        "<small><b>Premissas:</b> Reforma = CAPEX no ano 0 + 5 cortes "
        "(Cana-planta → Soca 4+). Replantio = custo operacional no ano 0 + "
        "receita líquida distribuída pelos anos de extensão, decaindo conforme "
        "a soca. Ambos descontados pela WACC.</small>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Tabela detalhada ─────────────────────────────────────────────────
    df_show = df_vpl.rename(columns={
        "TALHAO":        "Talhão",
        "area_ha":       "Área (ha)",
        "vpl_reforma":   "VPL Reforma (R$)",
        "vpl_replantio": "VPL Replantio (R$)",
        "decisao_vpl":   "Decisão VPL",
        "payback_anos":  "Payback (anos)",
    })

    def _cor_decisao(row):
        d = str(row.get("Decisão VPL", ""))
        if "REPLANTIO" in d:
            bg = "#e8f5e9"
        elif "REFORMA" in d:
            bg = "#fff3e0"
        else:
            bg = "#fce4e4"
        return [f"background-color:{bg}"] * len(row)

    st.dataframe(
        df_show.style.apply(_cor_decisao, axis=1).format({
            "Área (ha)":           "{:.2f}",
            "VPL Reforma (R$)":    "R$ {:,.0f}",
            "VPL Replantio (R$)":  "R$ {:,.0f}",
            "Payback (anos)":      "{:.1f}",
        }, na_rep="—"),
        use_container_width=True,
    )


def render_linhas_detalhe(gdf_linhas_eco: gpd.GeoDataFrame) -> None:
    st.subheader("📋 Detalhamento por Linha")

    talhoes = ["Todos"] + sorted(gdf_linhas_eco["TALHAO"].unique().tolist())
    col1, col2 = st.columns([2, 1])
    with col1:
        filtro_t = st.selectbox("Filtrar por talhão:", talhoes, key="sel_talhao")
    with col2:
        apenas_viaveis = st.checkbox("Apenas viáveis", value=False)

    df = gdf_linhas_eco.drop(columns=["geometry"], errors="ignore").copy()
    if filtro_t != "Todos":
        df = df[df["TALHAO"] == filtro_t]
    if apenas_viaveis:
        df = df[df["viavel"] == True]

    df["viavel"] = df["viavel"].map({True: "SIM", False: "NÃO"})
    df = df.rename(columns={
        "TALHAO":       "Talhão",
        "comp_linha":   "Compr. (m)",
        "soma_falhas":  "Falhas (m)",
        "perc_falhas":  "% Falha",
        "classe":       "Classe",
        "ioi":          "IOI (R$/h)",
        "eficiencia_pct":"Efic. (%)",
        "lucro":        "Lucro (R$)",
        "viavel":       "Viável",
    })
    cols = ["Talhão", "FID", "Compr. (m)", "Falhas (m)", "% Falha",
            "Classe", "IOI (R$/h)", "Efic. (%)", "Lucro (R$)", "Viável"]
    df = df[[c for c in cols if c in df.columns]]
    st.dataframe(df, use_container_width=True, height=420)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Kairos DSS — Replantio de Cana",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )


    st.markdown(
        "<h1 style='margin-bottom:0'>🌱 Kairos DSS</h1>"
        "<p style='color:#555;margin-top:4px'>Sistema de Apoio à Decisão para "
        "Replantio de Cana-de-Açúcar — Agricef</p>",
        unsafe_allow_html=True,
    )

    params = render_sidebar()

    files_ok = all([params["f_contorno"], params["f_linhas"], params["f_falhas"]])
    if not files_ok:
        st.info(
            "👈 Faça upload dos três ZIPs na barra lateral para iniciar. "
            "Cada ZIP deve conter um shapefile completo (.shp + .shx + .dbf + .prj)."
        )
        with st.expander("ℹ️ Como funciona o IOI — Índice Operacional Integrado"):
            st.markdown(
                """
O **IOI (R$/hora)** mede o retorno líquido por hora de operação do Kairos, calculado
individualmente para cada linha de plantio:

```
IOI  =  Lucro da Linha  /  Tempo Total de Operação (h)

Lucro  =  Receita Líquida  −  Custo Máquina  −  Custo Muda

Tempo Total  =  T. Plantio (falhas / vel. plantio)
             +  T. Deslocamento (trechos saudáveis / vel. deslocamento)
             +  T. Manobra de Cabeceira (fixo por linha)
```

Linhas com **IOI ≥ IOI mínimo** são exportadas para o piloto automático.
                """
            )
        return

    # ── PROCESSAR ─────────────────────────────────────────────────────────
    processar = st.sidebar.button("▶ PROCESSAR", type="primary", use_container_width=True)

    if processar:
        with st.spinner("Processando pipeline GIS..."):
            try:
                gdf_gis, gdf_contorno, avisos = gis_pipeline.run_pipeline(
                    params["f_contorno"].getvalue(),
                    params["f_linhas"].getvalue(),
                    params["f_falhas"].getvalue(),
                    params["campo_talhao"],
                    params["buffer_falha"],
                    params["min_falha"],
                )
                st.session_state["gdf_gis"]      = gdf_gis
                st.session_state["gdf_contorno"] = gdf_contorno
                st.session_state["avisos_gis"]   = avisos
            except ValueError as exc:
                st.error(f"Erro no processamento GIS: {exc}")
                return
            except Exception as exc:
                st.error(f"Erro inesperado: {exc}")
                return

    if st.session_state.get("gdf_gis") is None:
        st.info("Clique em **▶ PROCESSAR** na barra lateral para iniciar.")
        return

    gdf_gis: gpd.GeoDataFrame = st.session_state["gdf_gis"]

    avisos = st.session_state.get("avisos_gis", [])
    if avisos:
        with st.expander(f"Avisos de processamento GIS ({len(avisos)})", expanded=False):
            for av in avisos:
                st.write(f"• {av}")

    # ── Filtro de candidatas ──────────────────────────────────────────────
    gdf_candidatas = gdf_gis[
        (gdf_gis["soma_falhas"] > 0) &
        (gdf_gis["perc_falhas"] >= params["perc_falha_minimo"])
    ].copy()

    n_total_com_falha = int((gdf_gis["soma_falhas"] > 0).sum())
    n_candidatas      = len(gdf_candidatas)
    n_filtradas       = n_total_com_falha - n_candidatas

    if n_filtradas > 0:
        st.caption(
            f"Filtro % falha mínima ({params['perc_falha_minimo']:.0f}%): "
            f"{n_filtradas} linha(s) excluída(s). "
            f"{n_candidatas} linha(s) candidata(s)."
        )

    if len(gdf_candidatas) == 0:
        st.warning(
            f"Nenhuma linha com % de falha >= {params['perc_falha_minimo']:.0f}%. "
            "Reduza o filtro de % Falha mínima nos Parâmetros GIS."
        )
        return

    # ── Motor econômico (linha a linha) ───────────────────────────────────
    with st.spinner("Calculando IOI por linha..."):
        try:
            gdf_linhas_eco = eco.calcular_linhas(gdf_candidatas, params)
        except Exception as exc:
            st.error(f"Erro no motor econômico: {exc}")
            return

    custo_h   = eco.calcular_custo_hora(params)
    n_viaveis = int(gdf_linhas_eco["viavel"].sum())

    # ── Custo por hora ────────────────────────────────────────────────────
    fator_soca_val = eco.FATOR_SOCA.get(params.get("ciclo_soca", "Cana-planta"), 1.0)
    preco_efetivo  = params["atr_medio_kgton"] * params["preco_atr_rs_kg"]
    with st.expander(
        f"💰 Custo da máquina: R$ {custo_h:.2f}/hora  |  "
        f"Preço efetivo: R$ {preco_efetivo:.2f}/ton  |  "
        f"Fator soca ({params.get('ciclo_soca','Cana-planta')}): {fator_soca_val:.2f}×",
        expanded=False,
    ):
        d_diesel = params["diesel_lh"] * params["preco_diesel"]
        d_mdo    = (params["salario_operador"] + params["n_auxiliares"] * params["salario_auxiliar"]) / params["horas_mes"]
        d_manut  = params["manutencao_mensal"] / params["horas_mes"]
        d_depre  = (params["depreciacao_anual"] / 12) / params["horas_mes"]
        df_c = pd.DataFrame({
            "Componente": ["Diesel", "Mão de obra", "Manutenção", "Depreciação", "TOTAL"],
            "R$/hora":    [d_diesel, d_mdo, d_manut, d_depre, custo_h],
        })
        st.dataframe(
            df_c.style.format({"R$/hora": "R$ {:.2f}"}),
            use_container_width=True, hide_index=True,
        )

    # ── Métricas ──────────────────────────────────────────────────────────
    render_metrics(gdf_linhas_eco, gdf_gis, params["espacamento"], custo_h=custo_h, params=params)
    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_mapa, tab_rank, tab_talhao, tab_vpl, tab_linhas = st.tabs([
        "🗺️ Mapa",
        "🏆 Ranking de Linhas",
        "📊 Por Talhão",
        "📈 VPL 5 anos",
        "📋 Linhas",
    ])

    with tab_mapa:
        try:
            render_map(gdf_gis, gdf_linhas_eco,
                       gdf_contorno=st.session_state.get("gdf_contorno"))
        except Exception as _map_exc:
            st.error(f"Erro ao renderizar o mapa: {_map_exc}")
            st.exception(_map_exc)

    with tab_rank:
        render_ranking(gdf_linhas_eco, ioi_minimo=params["ioi_minimo"])

    with tab_talhao:
        render_por_talhao(
            gdf_linhas_eco, gdf_gis, params["espacamento"],
            gdf_contorno=st.session_state.get("gdf_contorno"),
            custo_reforma_ha=params["custo_reforma_ha"],
            limite_custo_reforma_pct=params["limite_custo_reforma_pct"],
        )

    with tab_vpl:
        render_vpl(gdf_linhas_eco, st.session_state.get("gdf_contorno"), params)

    with tab_linhas:
        render_linhas_detalhe(gdf_linhas_eco)

    st.divider()

    # ── Exportar ──────────────────────────────────────────────────────────
    st.subheader("📁 Exportar Shapefiles para Piloto Automático")

    if n_viaveis == 0:
        st.warning(
            "Nenhuma linha viável com os parâmetros atuais. "
            "Ajuste os parâmetros na barra lateral."
        )
    else:
        st.write(
            f"**{n_viaveis} linha(s) viável(is)** serão exportadas "
            f"para `{params['pasta_saida']}`"
        )
        if st.button("📦 Exportar SHPs Viáveis", type="primary"):
            if not params["pasta_saida"]:
                st.warning("Defina a pasta de exportação na barra lateral.")
            else:
                with st.spinner("Escrevendo shapefiles..."):
                    try:
                        caminhos = export_utils.exportar_talhoes(
                            gdf_linhas_eco,
                            params["pasta_saida"],
                            "TALHAO",
                        )
                        st.success(f"{len(caminhos)} shapefile(s) exportado(s):")
                        for c in caminhos:
                            st.code(c)
                    except ValueError as exc:
                        st.warning(str(exc))
                    except Exception as exc:
                        st.error(f"Erro na exportação: {exc}")


if __name__ == "__main__":
    main()
