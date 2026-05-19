"""
Gera o PDF de metodologia do Kairos — Cálculo de Viabilidade de Linhas.
Uso: python gerar_pdf_metodologia.py
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Cores institucionais
# ---------------------------------------------------------------------------
VERDE_ESCURO  = colors.HexColor("#1a5c2a")
VERDE_MEDIO   = colors.HexColor("#2e7d32")
VERDE_CLARO   = colors.HexColor("#e8f5e9")
CINZA_CLARO   = colors.HexColor("#f5f5f5")
CINZA_MEDIO   = colors.HexColor("#e0e0e0")
CINZA_ESCURO  = colors.HexColor("#424242")
LARANJA       = colors.HexColor("#e65100")
AZUL_INFO     = colors.HexColor("#e3f2fd")
AZUL_BORDA    = colors.HexColor("#1565c0")

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
base = getSampleStyleSheet()

def _s(name, **kw):
    return ParagraphStyle(name, **kw)

ESTILOS = {
    "capa_titulo": _s("capa_titulo",
        fontName="Helvetica-Bold", fontSize=26,
        textColor=colors.white, alignment=TA_CENTER, leading=32),

    "capa_sub": _s("capa_sub",
        fontName="Helvetica", fontSize=13,
        textColor=colors.HexColor("#c8e6c9"), alignment=TA_CENTER, leading=18),

    "capa_versao": _s("capa_versao",
        fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#a5d6a7"), alignment=TA_CENTER),

    "titulo_secao": _s("titulo_secao",
        fontName="Helvetica-Bold", fontSize=15,
        textColor=VERDE_ESCURO, spaceBefore=18, spaceAfter=6, leading=20),

    "titulo_sub": _s("titulo_sub",
        fontName="Helvetica-Bold", fontSize=12,
        textColor=VERDE_MEDIO, spaceBefore=12, spaceAfter=4, leading=16),

    "corpo": _s("corpo",
        fontName="Helvetica", fontSize=10,
        textColor=CINZA_ESCURO, leading=15, alignment=TA_JUSTIFY,
        spaceBefore=3, spaceAfter=3),

    "formula": _s("formula",
        fontName="Courier-Bold", fontSize=11,
        textColor=colors.HexColor("#1a237e"), alignment=TA_CENTER,
        leading=18, spaceBefore=6, spaceAfter=6),

    "formula_desc": _s("formula_desc",
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.HexColor("#546e7a"), alignment=TA_CENTER,
        leading=13),

    "nota": _s("nota",
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.HexColor("#5d4037"), leading=13,
        spaceBefore=4, spaceAfter=4),

    "bullet": _s("bullet",
        fontName="Helvetica", fontSize=10,
        textColor=CINZA_ESCURO, leading=15,
        leftIndent=16, spaceBefore=2, spaceAfter=2),

    "rodape": _s("rodape",
        fontName="Helvetica", fontSize=8,
        textColor=colors.HexColor("#9e9e9e"), alignment=TA_CENTER),
}


# ---------------------------------------------------------------------------
# Componentes visuais reutilizáveis
# ---------------------------------------------------------------------------

def divisor():
    return HRFlowable(width="100%", thickness=1,
                      color=CINZA_MEDIO, spaceAfter=6, spaceBefore=6)

def espaco(h=0.3):
    return Spacer(1, h * cm)

def p(texto, estilo="corpo"):
    return Paragraph(texto, ESTILOS[estilo])

def bloco_formula(formula, descricao=""):
    """Caixa azul com fórmula centralizada e descrição opcional."""
    items = [Paragraph(formula, ESTILOS["formula"])]
    if descricao:
        items.append(Paragraph(descricao, ESTILOS["formula_desc"]))
    t = Table([[item] for item in items], colWidths=[15 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), AZUL_INFO),
        ("ROUNDEDCORNERS", [6]),
        ("BOX",         (0, 0), (-1, -1), 1, AZUL_BORDA),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    return t

def bloco_nota(texto):
    """Caixa amarela de observação."""
    t = Table([[Paragraph(f"<b>Obs.:</b> {texto}", ESTILOS["nota"])]], colWidths=[15 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#fff8e1")),
        ("BOX",         (0, 0), (-1, -1), 1, colors.HexColor("#f9a825")),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t

def tabela_parametros(dados, larguras=None):
    """Tabela formatada de parâmetros."""
    if larguras is None:
        larguras = [6 * cm, 3 * cm, 6 * cm]
    style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_MEDIO),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ])
    t = Table(dados, colWidths=larguras)
    t.setStyle(style)
    return t

def tabela_classes():
    """Tabela de classificação por bins."""
    dados = [
        ["Classe", "Faixa de Falha (%)", "Ponto Médio Usado", "Indicação"],
        ["0-2",    "0% a 2%",   "1,0%",  "Linha excelente"],
        ["2-4",    "2% a 4%",   "3,0%",  "Linha boa"],
        ["4-6",    "4% a 6%",   "5,0%",  "Falha baixa"],
        ["6-8",    "6% a 8%",   "7,0%",  "Falha moderada"],
        ["8-10",   "8% a 10%",  "9,0%",  "Replantio possível"],
        ["10-12",  "10% a 12%", "11,0%", "Replantio recomendado"],
        ["12-14",  "12% a 14%", "13,0%", "Falha significativa"],
        ["14-16",  "14% a 16%", "15,0%", "Falha alta"],
        ["16-18",  "16% a 18%", "17,0%", "Falha muito alta"],
        ["18-20",  "18% a 20%", "19,0%", "Falha crítica"],
        [">20",    "Acima de 20%", "22,0%", "Replantio urgente"],
    ]
    cores_class = [
        colors.white,
        colors.HexColor("#1a9850"),  colors.HexColor("#66bd63"),
        colors.HexColor("#a6d96a"),  colors.HexColor("#d9ef8b"),
        colors.HexColor("#fee08b"),  colors.HexColor("#fdae61"),
        colors.HexColor("#f46d43"),  colors.HexColor("#d73027"),
        colors.HexColor("#a50026"),  colors.HexColor("#7f0000"),
        colors.HexColor("#4d0000"),
    ]
    txt_cores = [colors.black] * 6 + [colors.white] * 6

    style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_MEDIO),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
    for i, (bg, fg) in enumerate(zip(cores_class, txt_cores), start=0):
        if i == 0:
            continue
        style.add("BACKGROUND", (0, i), (0, i), bg)
        style.add("TEXTCOLOR",  (0, i), (0, i), fg)

    t = Table(dados, colWidths=[2.2 * cm, 3.5 * cm, 3.5 * cm, 5.8 * cm])
    t.setStyle(style)
    return t


# ---------------------------------------------------------------------------
# Funções de cabeçalho/rodapé de página
# ---------------------------------------------------------------------------

def _cabecalho_rodape(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Faixa verde no topo
    canvas.setFillColor(VERDE_ESCURO)
    canvas.rect(0, h - 1.1 * cm, w, 1.1 * cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5 * cm, h - 0.75 * cm, "Kairos — Metodologia de Viabilidade de Linhas de Cana")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 1.5 * cm, h - 0.75 * cm, "Agricef Kairos")

    # Rodapé
    canvas.setFillColor(CINZA_ESCURO)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5 * cm, 0.7 * cm, "Agricef Kairos — Documento interno de metodologia")
    canvas.drawRightString(w - 1.5 * cm, 0.7 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(CINZA_MEDIO)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.1 * cm, w - 1.5 * cm, 1.1 * cm)

    canvas.restoreState()


def _capa(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(VERDE_ESCURO)
    canvas.rect(0, 0, w, h, fill=True, stroke=False)
    canvas.setFillColor(VERDE_MEDIO)
    canvas.rect(0, h * 0.35, w, h * 0.42, fill=True, stroke=False)
    canvas.setFillColor(colors.HexColor("#1b5e20"))
    canvas.rect(0, h * 0.32, w, 0.06 * h, fill=True, stroke=False)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Conteúdo do documento
# ---------------------------------------------------------------------------

def build_story():
    story = []

    # ================================================================
    # CAPA
    # ================================================================
    story.append(espaco(5.5))
    story.append(p("🌱  KAIROS", "capa_titulo"))
    story.append(espaco(0.4))
    story.append(p("Metodologia de Cálculo de Viabilidade", "capa_titulo"))
    story.append(p("de Linhas de Cana-de-Açúcar", "capa_titulo"))
    story.append(espaco(1.2))
    story.append(p(
        "Documento técnico que descreve os parâmetros GIS, custos operacionais,<br/>"
        "indicadores de produção e o modelo econômico utilizados para determinar<br/>"
        "quais linhas devem ser replantadas pelo implemento Kairos.",
        "capa_sub"))
    story.append(espaco(1.5))
    story.append(p("Versão 1.0  ·  Sistema Kairos — Agricef", "capa_versao"))
    story.append(PageBreak())

    # ================================================================
    # 1. VISÃO GERAL
    # ================================================================
    story.append(p("1. Visão Geral do Sistema", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "O Kairos é um implemento agrícola para replantio localizado de cana-de-açúcar. "
        "Para determinar <b>quais linhas valem economicamente ser replantadas</b>, "
        "o sistema executa duas etapas principais:"
    ))
    story.append(espaco(0.3))
    story.append(p("→  <b>Etapa 1 — Classificação GIS:</b> processa os mapas de falhas mapeados por drone e "
                   "calcula o percentual de falha de cada linha individualmente, classificando-a em uma "
                   "faixa de 0 a >20%.", "bullet"))
    story.append(p("→  <b>Etapa 2 — Modelo Econômico:</b> aplica os parâmetros de custo e produção sobre "
                   "cada linha classificada, calcula o lucro estimado e determina se a linha é viável "
                   "(lucro > 0).", "bullet"))
    story.append(espaco(0.3))
    story.append(p(
        "A unidade de análise é a <b>linha individual</b> de plantio. "
        "A decisão de replantio é tomada linha por linha, não por talhão como um todo."
    ))

    story.append(espaco(0.5))

    # Fluxo visual
    fluxo = [
        ["Mapas de Falha\n(Drone)", "→", "Classificação\nGIS", "→",
         "Modelo\nEconômico", "→", "Linhas\nViáveis (SHP)"],
    ]
    tf = Table(fluxo, colWidths=[3*cm, 0.7*cm, 2.8*cm, 0.7*cm, 2.8*cm, 0.7*cm, 3*cm])
    tf.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0),  VERDE_ESCURO),
        ("BACKGROUND",    (2, 0), (2, 0),  AZUL_BORDA),
        ("BACKGROUND",    (4, 0), (4, 0),  colors.HexColor("#4a148c")),
        ("BACKGROUND",    (6, 0), (6, 0),  VERDE_MEDIO),
        ("TEXTCOLOR",     (0, 0), (0, 0),  colors.white),
        ("TEXTCOLOR",     (2, 0), (2, 0),  colors.white),
        ("TEXTCOLOR",     (4, 0), (4, 0),  colors.white),
        ("TEXTCOLOR",     (6, 0), (6, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("FONTNAME",      (1, 0), (1, 0),  "Helvetica-Bold"),
        ("FONTNAME",      (3, 0), (3, 0),  "Helvetica-Bold"),
        ("FONTNAME",      (5, 0), (5, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (1, 0), (1, 0),  14),
        ("FONTSIZE",      (3, 0), (3, 0),  14),
        ("FONTSIZE",      (5, 0), (5, 0),  14),
        ("TEXTCOLOR",     (1, 0), (1, 0),  CINZA_ESCURO),
        ("TEXTCOLOR",     (3, 0), (3, 0),  CINZA_ESCURO),
        ("TEXTCOLOR",     (5, 0), (5, 0),  CINZA_ESCURO),
    ]))
    story.append(tf)

    story.append(PageBreak())

    # ================================================================
    # 2. ETAPA GIS
    # ================================================================
    story.append(p("2. Etapa 1 — Classificação GIS", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "Esta etapa processa os três shapefiles de entrada (Contorno, Linhas e Falhas) "
        "e calcula, para cada linha dentro de cada talhão, o percentual de falha "
        "e sua classe correspondente."
    ))

    # 2.1 Parâmetros GIS
    story.append(p("2.1  Parâmetros GIS", "titulo_sub"))
    dados_gis = [
        ["Parâmetro", "Valor padrão", "Descrição"],
        ["Buffer nas falhas", "0,3 m",
         "Zona de expansão ao redor de cada falha para garantir "
         "a interseção com a linha mesmo com pequenos desvios GPS."],
        ["Comprimento mínimo de falha", "1,5 m",
         "Falhas menores que este valor são ignoradas. O Kairos não "
         "realiza replantio abaixo deste comprimento."],
        ["Espaçamento entre linhas", "1,5 m",
         "Distância entre linhas adjacentes. Usado para converter "
         "metros lineares em área equivalente (hectares)."],
    ]
    story.append(tabela_parametros(dados_gis, [4.5*cm, 2.8*cm, 7.7*cm]))

    # 2.2 Pipeline por talhão
    story.append(espaco(0.4))
    story.append(p("2.2  Pipeline de Processamento por Talhão", "titulo_sub"))
    story.append(p(
        "O processamento é executado <b>individualmente para cada talhão</b>. "
        "As etapas abaixo se repetem para todos os talhões presentes no shapefile de Contorno:"
    ))

    passos = [
        ["1", "Recorte espacial",
         "As linhas e falhas são recortadas ao polígono do talhão (clip). "
         "O comprimento de cada linha é recalculado após o recorte."],
        ["2", "Buffer nas falhas",
         "Um buffer de 0,3 m é aplicado ao redor de cada falha, "
         "transformando-as em polígonos. Isso evita perda de interseção "
         "causada por imprecisão GPS."],
        ["3", "Interseção com linhas",
         "Os polígonos de falha (bufferizados) são intersectados com as linhas. "
         "O resultado são os segmentos de cada linha que coincidem com falhas."],
        ["4", "Filtro de segmentos",
         "Apenas os segmentos de falha com comprimento > 1,5 m são mantidos."],
        ["5", "Soma por linha",
         "Os comprimentos dos segmentos válidos são somados por linha "
         "(soma_falhas)."],
        ["6", "Cálculo do percentual",
         "perc_falhas = (soma_falhas / comp_linha) × 100"],
        ["7", "Classificação",
         "O percentual é enquadrado em uma das 11 classes (ver Seção 2.3)."],
    ]
    tp = Table(passos, colWidths=[0.6*cm, 3.5*cm, 10.9*cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), VERDE_ESCURO),
        ("TEXTCOLOR",     (0, 0), (0, -1), colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, CINZA_MEDIO),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, CINZA_CLARO]),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(tp)

    # Fórmula do percentual
    story.append(espaco(0.5))
    story.append(p("Fórmula do percentual de falha:", "titulo_sub"))
    story.append(bloco_formula(
        "% Falha  =  (soma_falhas  /  comp_linha)  ×  100",
        "soma_falhas: soma dos segmentos de falha > 1,5 m na linha (metros)\n"
        "comp_linha: comprimento total da linha dentro do talhão (metros)"
    ))

    # 2.3 Tabela de classes
    story.append(espaco(0.4))
    story.append(p("2.3  Classificação das Linhas por Percentual de Falha", "titulo_sub"))
    story.append(p(
        "Após o cálculo do percentual, cada linha é enquadrada em uma das 11 classes abaixo. "
        "O <b>ponto médio</b> de cada classe é o valor utilizado no modelo econômico."
    ))
    story.append(espaco(0.2))
    story.append(tabela_classes())
    story.append(espaco(0.2))
    story.append(bloco_nota(
        "A classe '>20' utiliza 22% como ponto médio convencional no modelo econômico, "
        "pois não existe limite superior definido."
    ))

    story.append(PageBreak())

    # ================================================================
    # 3. MODELO ECONÔMICO
    # ================================================================
    story.append(p("3. Etapa 2 — Modelo Econômico", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "O modelo econômico avalia, para cada linha classificada, "
        "se o <b>valor recuperável pela replantia supera o custo de operação</b>. "
        "Quando o lucro estimado for positivo (lucro > 0), a linha é marcada como <b>viável</b>."
    ))

    # 3.1 Parâmetros de custo
    story.append(p("3.1  Custos Operacionais (R$/ha)", "titulo_sub"))
    story.append(p(
        "Os custos são expressos por hectare e somados para compor o "
        "<b>custo operacional total por hectare (custo_ha)</b>:"
    ))
    dados_custo = [
        ["Parâmetro", "Valor padrão", "Descrição"],
        ["Diesel",     "R$ 12,00/ha", "Consumo de combustível por hectare operado."],
        ["Operador",   "R$ 15,00/ha", "Custo de mão de obra do operador da máquina."],
        ["Manutenção", "R$  8,00/ha", "Manutenção preventiva e corretiva do implemento."],
        ["Muda",       "R$ 40,00/ha", "Custo das mudas de cana utilizadas no replantio."],
        ["Máquina",    "R$ 20,00/ha", "Depreciação e custo fixo do implemento Kairos."],
    ]
    story.append(tabela_parametros(dados_custo, [3.5*cm, 2.8*cm, 8.7*cm]))
    story.append(espaco(0.3))
    story.append(bloco_formula(
        "custo_ha  =  diesel  +  operador  +  manutencao  +  muda  +  maquina",
        "Exemplo com valores padrão:  custo_ha = 12 + 15 + 8 + 40 + 20 = R$ 95,00/ha"
    ))

    # 3.2 Parâmetros de produção
    story.append(espaco(0.3))
    story.append(p("3.2  Parâmetros de Produção", "titulo_sub"))
    dados_prod = [
        ["Parâmetro", "Valor padrão", "Descrição"],
        ["Produtividade", "80 t/ha",
         "Produção esperada de cana por hectare na região."],
        ["Preço por tonelada", "R$ 140,00/t",
         "Preço de venda da tonelada de cana-de-açúcar."],
    ]
    story.append(tabela_parametros(dados_prod, [3.8*cm, 2.8*cm, 8.4*cm]))
    story.append(espaco(0.3))
    story.append(bloco_formula(
        "valor_ha  =  produtividade  ×  preco",
        "Exemplo:  valor_ha = 80 × R$ 140,00 = R$ 11.200,00/ha"
    ))

    # 3.3 Eficiência operacional
    story.append(espaco(0.3))
    story.append(p("3.3  Parâmetros de Eficiência Operacional", "titulo_sub"))
    story.append(p(
        "Representam o tempo não produtivo por linha. São somados e tratados "
        "como um <b>custo fixo adicional por linha</b> (em minutos, somado diretamente ao custo):"
    ))
    dados_ef = [
        ["Parâmetro", "Valor padrão", "Descrição"],
        ["Tempo de manobra",      "8 min", "Tempo gasto nas manobras de cabeceira entre linhas."],
        ["Tempo de deslocamento", "5 min", "Tempo de deslocamento até a linha a ser replantada."],
        ["Tempo de abastecimento","4 min", "Tempo médio por parada de abastecimento de muda."],
    ]
    story.append(tabela_parametros(dados_ef, [4.2*cm, 2.4*cm, 8.4*cm]))
    story.append(espaco(0.3))
    story.append(bloco_formula(
        "tempo_op  =  manobra  +  deslocamento  +  abastecimento",
        "Exemplo:  tempo_op = 8 + 5 + 4 = 17 minutos"
    ))
    story.append(espaco(0.2))
    story.append(bloco_nota(
        "O tempo operacional é somado diretamente ao custo em R$ como um custo fixo por linha. "
        "Existe uma mistura dimensional (reais + minutos) herdada do modelo original HTML, "
        "que será corrigida em versões futuras com a inclusão do custo horário da máquina."
    ))

    story.append(PageBreak())

    # ================================================================
    # 4. FÓRMULAS DO MODELO
    # ================================================================
    story.append(p("4. Fórmulas do Modelo Econômico", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "As fórmulas abaixo são aplicadas a <b>cada linha individualmente</b> "
        "após a classificação GIS."
    ))

    # 4.1 Área equivalente
    story.append(p("4.1  Área Equivalente (ha)", "titulo_sub"))
    story.append(p(
        "Converte o comprimento linear da linha em área, usando o espaçamento entre linhas:"
    ))
    story.append(bloco_formula(
        "area_ha  =  (comp_linha  ×  espacamento)  /  10.000",
        "comp_linha em metros  ·  espacamento em metros  ·  resultado em hectares\n"
        "Exemplo: linha de 200 m, espaçamento 1,5 m  →  area_ha = (200 × 1,5) / 10.000 = 0,030 ha"
    ))

    # 4.2 Percentual da classe
    story.append(espaco(0.3))
    story.append(p("4.2  Percentual da Classe (perc_classe)", "titulo_sub"))
    story.append(p(
        "Para o cálculo do valor recuperável, usa-se o <b>ponto médio</b> do bin da classe, "
        "não o percentual exato da linha. Isso padroniza o modelo por faixa:"
    ))
    story.append(bloco_formula(
        'perc_classe  =  (limite_inferior  +  limite_superior)  /  2',
        'Exemplos:  classe "4-6"  →  perc_classe = (4 + 6) / 2 = 5,0%\n'
        '           classe "18-20" →  perc_classe = (18 + 20) / 2 = 19,0%\n'
        '           classe ">20"  →  perc_classe = 22,0%  (convencional)'
    ))

    # 4.3 Valor recuperável
    story.append(espaco(0.3))
    story.append(p("4.3  Valor Recuperável (R$)", "titulo_sub"))
    story.append(p(
        "Estima a receita que pode ser obtida com o replantio da linha, "
        "considerando a produtividade esperada, o preço da cana "
        "e um <b>fator de eficiência de 0,80</b> (80% de aproveitamento real):"
    ))
    story.append(bloco_formula(
        "valor_recuperavel  =  valor_ha  ×  (perc_classe / 100)  ×  area_ha  ×  0,80",
        "valor_ha = produtividade × preco\n"
        "O fator 0,80 reduz a superestimação causada por perdas e ineficiências no replantio."
    ))
    story.append(espaco(0.2))
    story.append(bloco_nota(
        "O fator 0,80 é empírico e representa uma estimativa conservadora de recuperação. "
        "Em versões futuras, poderá ser parametrizado conforme dados históricos de cada fazenda."
    ))

    # 4.4 Custo total
    story.append(espaco(0.3))
    story.append(p("4.4  Custo Total de Replantio da Linha (R$)", "titulo_sub"))
    story.append(p(
        "Combina o custo por área com o custo operacional fixo por linha:"
    ))
    story.append(bloco_formula(
        "custo  =  (custo_ha  ×  area_ha)  +  tempo_op",
        "custo_ha: soma dos custos operacionais em R$/ha\n"
        "area_ha: área equivalente da linha em hectares\n"
        "tempo_op: tempo não produtivo somado como custo fixo (em minutos)"
    ))

    # 4.5 Lucro
    story.append(espaco(0.3))
    story.append(p("4.5  Lucro Estimado (R$)", "titulo_sub"))
    story.append(bloco_formula(
        "lucro  =  valor_recuperavel  -  custo"
    ))

    # 4.6 Viabilidade
    story.append(espaco(0.3))
    story.append(p("4.6  Critério de Viabilidade", "titulo_sub"))
    story.append(p(
        "A linha é considerada <b>economicamente viável</b> quando o lucro estimado "
        "for positivo:"
    ))
    story.append(bloco_formula(
        "viavel  =  (lucro  >  0)",
        "Se lucro > 0  →  linha marcada como VIÁVEL  →  exportada para o piloto automático\n"
        "Se lucro ≤ 0  →  linha marcada como NÃO VIÁVEL  →  não exportada"
    ))

    story.append(PageBreak())

    # ================================================================
    # 5. EXEMPLO NUMÉRICO
    # ================================================================
    story.append(p("5. Exemplo Numérico Completo", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "A seguir, um exemplo passo a passo para uma linha hipotética "
        "com os valores padrão do sistema:"
    ))

    story.append(espaco(0.3))

    # Dados da linha
    story.append(p("Dados da linha:", "titulo_sub"))
    dados_linha = [
        ["Atributo", "Valor"],
        ["Comprimento da linha (comp_linha)", "250 m"],
        ["Soma das falhas > 1,5 m (soma_falhas)", "30 m"],
        ["Espaçamento entre linhas", "1,5 m"],
        ["Classe calculada", "10-12"],
    ]
    tl = Table(dados_linha, colWidths=[9*cm, 6*cm])
    tl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), CINZA_ESCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_MEDIO),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(tl)

    story.append(espaco(0.4))
    story.append(p("Parâmetros do modelo (valores padrão):", "titulo_sub"))
    dados_param_ex = [
        ["Parâmetro", "Valor"],
        ["custo_ha (diesel+operador+manutencao+muda+maquina)", "R$ 95,00/ha"],
        ["tempo_op (manobra+deslocamento+abastecimento)", "17 min"],
        ["produtividade", "80 t/ha"],
        ["preco", "R$ 140,00/t"],
        ["valor_ha (produtividade × preco)", "R$ 11.200,00/ha"],
    ]
    tp2 = Table(dados_param_ex, colWidths=[11*cm, 4*cm])
    tp2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), CINZA_ESCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_MEDIO),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(tp2)

    story.append(espaco(0.4))
    story.append(p("Cálculo passo a passo:", "titulo_sub"))

    calc = [
        ["Passo", "Fórmula", "Resultado"],
        ["1  % Falha",
         "(30 / 250) × 100",
         "12,0%  →  classe \"10-12\""],
        ["2  perc_classe",
         "(10 + 12) / 2",
         "11,0%"],
        ["3  area_ha",
         "(250 × 1,5) / 10.000",
         "0,0375 ha"],
        ["4  valor_recuperavel",
         "11.200 × (11/100) × 0,0375 × 0,80",
         "R$ 36,96"],
        ["5  custo",
         "(95 × 0,0375) + 17",
         "R$ 20,56"],
        ["6  lucro",
         "36,96 - 20,56",
         "R$ 16,40"],
        ["7  viavel",
         "16,40 > 0?",
         "SIM  ✓  Linha exportada"],
    ]
    tc = Table(calc, colWidths=[3.5*cm, 6*cm, 5.5*cm])
    tc.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_MEDIO),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("ALIGN",         (2, 0), (2, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
        ("TEXTCOLOR",     (2, -1), (2, -1), VERDE_MEDIO),
        ("FONTNAME",      (2, -1), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(tc)

    # ================================================================
    # 6. LIMITAÇÕES
    # ================================================================
    story.append(espaco(0.6))
    story.append(p("6. Limitações Atuais do Modelo", "titulo_secao"))
    story.append(divisor())

    lims = [
        "O <b>tempo operacional</b> (minutos) é somado ao custo em R$ sem conversão por custo horário — mistura dimensional a ser corrigida.",
        "O <b>fator de eficiência 0,80</b> é fixo e empírico; não considera variações por talhão, estágio do canavial ou histórico de produção.",
        "O modelo <b>não considera compensação lateral</b> da cana — linhas com pouca falha podem se recuperar naturalmente sem replantio.",
        "A <b>produtividade histórica</b> por talhão não é utilizada — o modelo usa um único valor global.",
        "O <b>tempo real de máquina</b> e a <b>logística de campo</b> não são modelados.",
        "A <b>mistura dimensional</b> entre reais e minutos no cálculo do custo é uma simplificação do modelo original.",
    ]
    for lim in lims:
        story.append(p(f"•  {lim}", "bullet"))

    story.append(espaco(0.5))
    story.append(p("7. Saída do Sistema", "titulo_secao"))
    story.append(divisor())
    story.append(p(
        "Ao final do processamento, o sistema gera <b>um shapefile por talhão</b> "
        "contendo apenas as linhas economicamente viáveis (lucro > 0). "
        "Cada arquivo exportado contém os seguintes atributos:"
    ))
    dados_saida = [
        ["Campo", "Tipo", "Descrição"],
        ["TALHAO",      "Texto",   "Identificador do talhão."],
        ["FID",         "Inteiro", "Identificador único da linha dentro do talhão."],
        ["comp_linha",  "Real",    "Comprimento da linha em metros (após recorte)."],
        ["soma_falhas", "Real",    "Soma dos segmentos de falha > 1,5 m na linha (metros)."],
        ["perc_falhas", "Real",    "Percentual de falha calculado (%)."],
        ["classe",      "Texto",   "Classe de falha: '0-2', '2-4', ..., '>20'."],
        ["lucro",       "Real",    "Lucro estimado da operação de replantio (R$)."],
        ["geometry",    "Linha",   "Geometria da linha para o piloto automático."],
    ]
    story.append(tabela_parametros(dados_saida, [3*cm, 2*cm, 10*cm]))
    story.append(espaco(0.3))
    story.append(p(
        "Os arquivos estão prontos para serem carregados no sistema de piloto automático "
        "do trator para execução do replantio localizado pelo Kairos.",
        "nota"
    ))

    return story


# ---------------------------------------------------------------------------
# Gerar PDF
# ---------------------------------------------------------------------------

def gerar_pdf(caminho_saida: str = "metodologia_kairos.pdf"):
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Kairos — Metodologia de Viabilidade de Linhas",
        author="Agricef Kairos",
        subject="Modelo econômico e GIS para replantio localizado de cana-de-açúcar",
    )

    story = build_story()

    # Capa sem cabeçalho/rodapé, demais páginas com
    def _template(canvas, doc):
        if doc.page == 1:
            _capa(canvas, doc)
        else:
            _cabecalho_rodape(canvas, doc)

    doc.build(story, onFirstPage=_template, onLaterPages=_template)
    print(f"PDF gerado: {caminho_saida}")


if __name__ == "__main__":
    gerar_pdf("metodologia_kairos.pdf")
