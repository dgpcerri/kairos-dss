"""
Gera o Manual Completo do Kairos DSS em PDF.
Execute: python gerar_manual_kairos.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor


# ── Cores ────────────────────────────────────────────────────────────────────
VERDE_ESCURO  = HexColor("#1B5E20")
VERDE_MEDIO   = HexColor("#2E7D32")
VERDE_CLARO   = HexColor("#A5D6A7")
VERDE_BG      = HexColor("#F1F8E9")
AZUL_ESCURO   = HexColor("#0D47A1")
AZUL_CLARO    = HexColor("#BBDEFB")
AZUL_BG       = HexColor("#E3F2FD")
AMARELO       = HexColor("#F9A825")
AMARELO_BG    = HexColor("#FFFDE7")
CINZA_CLARO   = HexColor("#F5F5F5")
CINZA_MEDIO   = HexColor("#9E9E9E")
LARANJA       = HexColor("#E65100")
LARANJA_BG    = HexColor("#FFF3E0")
VERMELHO      = HexColor("#B71C1C")
PRETO         = HexColor("#212121")

W, H = A4
MARGEM = 2.0 * cm


# ── Estilos ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def estilo(nome, parent="Normal", **kw):
    s = ParagraphStyle(nome, parent=base[parent], **kw)
    return s

TITULO_CAPA = estilo("TituloCapa",
    fontSize=32, textColor=colors.white, alignment=TA_CENTER,
    fontName="Helvetica-Bold", leading=40, spaceAfter=10)

SUBTITULO_CAPA = estilo("SubtituloCapa",
    fontSize=16, textColor=HexColor("#C8E6C9"), alignment=TA_CENTER,
    fontName="Helvetica", leading=22)

H1 = estilo("H1",
    fontSize=18, textColor=VERDE_ESCURO, fontName="Helvetica-Bold",
    spaceBefore=18, spaceAfter=8, leading=22,
    borderPad=4, leftIndent=0)

H2 = estilo("H2",
    fontSize=13, textColor=AZUL_ESCURO, fontName="Helvetica-Bold",
    spaceBefore=14, spaceAfter=5, leading=17)

H3 = estilo("H3",
    fontSize=11, textColor=VERDE_MEDIO, fontName="Helvetica-Bold",
    spaceBefore=10, spaceAfter=4, leading=14)

CORPO = estilo("Corpo",
    fontSize=10, textColor=PRETO, fontName="Helvetica",
    spaceBefore=3, spaceAfter=4, leading=14, alignment=TA_JUSTIFY)

CORPO_BOLD = estilo("CorpoBold",
    fontSize=10, textColor=PRETO, fontName="Helvetica-Bold",
    spaceBefore=3, spaceAfter=4, leading=14)

FORMULA = estilo("Formula",
    fontSize=9.5, textColor=HexColor("#1A237E"), fontName="Courier-Bold",
    spaceBefore=4, spaceAfter=4, leading=13, leftIndent=24, backColor=AZUL_BG,
    borderPad=6)

NOTA = estilo("Nota",
    fontSize=9, textColor=HexColor("#4E342E"), fontName="Helvetica-Oblique",
    spaceBefore=3, spaceAfter=3, leading=12, leftIndent=12, backColor=AMARELO_BG,
    borderPad=4)

DICA = estilo("Dica",
    fontSize=9, textColor=HexColor("#1B5E20"), fontName="Helvetica",
    spaceBefore=3, spaceAfter=3, leading=12, leftIndent=12, backColor=VERDE_BG,
    borderPad=4)

BULLET = estilo("Bullet",
    fontSize=10, textColor=PRETO, fontName="Helvetica",
    spaceBefore=2, spaceAfter=2, leading=13, leftIndent=20, bulletIndent=10)

TABELA_HEADER = estilo("TabelaHeader",
    fontSize=9, textColor=colors.white, fontName="Helvetica-Bold",
    alignment=TA_CENTER, leading=11)

TABELA_CELL = estilo("TabelaCell",
    fontSize=9, textColor=PRETO, fontName="Helvetica",
    alignment=TA_LEFT, leading=11)

CAPTION = estilo("Caption",
    fontSize=8.5, textColor=CINZA_MEDIO, fontName="Helvetica-Oblique",
    alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)

NUMERO_SECAO = estilo("NumeroSecao",
    fontSize=10, textColor=VERDE_MEDIO, fontName="Helvetica-Bold",
    spaceBefore=0, spaceAfter=0, leading=12)


# ── Cabeçalho / Rodapé ────────────────────────────────────────────────────────
def cabecalho_rodape(canvas, doc):
    canvas.saveState()
    # Cabeçalho (exceto capa)
    if doc.page > 1:
        canvas.setFillColor(VERDE_ESCURO)
        canvas.rect(MARGEM, H - 1.5*cm, W - 2*MARGEM, 0.5*cm, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(MARGEM + 4, H - 1.25*cm, "KAIROS DSS — Manual do Usuário")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W - MARGEM - 4, H - 1.25*cm, "Agricef Kairos v2.0")
    # Rodapé
    canvas.setStrokeColor(VERDE_CLARO)
    canvas.setLineWidth(0.5)
    canvas.line(MARGEM, 1.3*cm, W - MARGEM, 1.3*cm)
    canvas.setFillColor(CINZA_MEDIO)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, 0.8*cm, f"Página {doc.page}")
    canvas.restoreState()


# ── Caixa colorida ────────────────────────────────────────────────────────────
def caixa(titulo, conteudo, cor_borda=VERDE_MEDIO, cor_bg=VERDE_BG, cor_titulo=VERDE_ESCURO):
    """Retorna uma Table que imita uma caixa com título colorido."""
    s_titulo = estilo(f"CaixaTitulo_{id(titulo)}",
        fontSize=10, textColor=cor_titulo, fontName="Helvetica-Bold",
        leading=13, backColor=cor_bg)
    s_corpo  = estilo(f"CaixaCorpo_{id(titulo)}",
        fontSize=9.5, textColor=PRETO, fontName="Helvetica",
        leading=13, backColor=cor_bg, alignment=TA_JUSTIFY)
    celulas = [[Paragraph(f"<b>{titulo}</b>", s_titulo)],
               [Paragraph(conteudo, s_corpo)]]
    t = Table(celulas, colWidths=[W - 2*MARGEM - 1*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), cor_bg),
        ("BOX",        (0,0), (-1,-1), 1.5, cor_borda),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [cor_bg]),
    ]))
    return t


def tabela_params(linhas, col_widths=None):
    """Tabela estilo parâmetros: Parâmetro | Valor Padrão | Descrição."""
    if col_widths is None:
        col_widths = [5.2*cm, 2.8*cm, 8.7*cm]
    header = [
        Paragraph("Parâmetro", TABELA_HEADER),
        Paragraph("Padrão", TABELA_HEADER),
        Paragraph("Descrição e valores recomendados", TABELA_HEADER),
    ]
    dados = [header] + [
        [Paragraph(str(r[0]), TABELA_CELL),
         Paragraph(str(r[1]), TABELA_CELL),
         Paragraph(str(r[2]), TABELA_CELL)]
        for r in linhas
    ]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    return t


# ── Conteúdo ──────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # =========================================================================
    # CAPA
    # =========================================================================
    story.append(Spacer(1, 3.5*cm))

    # Bloco verde da capa
    t_capa = Table(
        [[Paragraph("🌱  KAIROS DSS", TITULO_CAPA)],
         [Paragraph("Sistema de Apoio à Decisão para Replantio de Cana-de-Açúcar", SUBTITULO_CAPA)],
         [Spacer(1, 0.4*cm)],
         [Paragraph("MANUAL COMPLETO DO USUÁRIO", estilo("CapaManual",
             fontSize=14, textColor=AMARELO, fontName="Helvetica-Bold",
             alignment=TA_CENTER))],
         [Paragraph("Versão 2.0  |  Agricef", estilo("CapaVer",
             fontSize=11, textColor=HexColor("#C8E6C9"), fontName="Helvetica",
             alignment=TA_CENTER))],
        ],
        colWidths=[W - 2*MARGEM],
    )
    t_capa.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), VERDE_ESCURO),
        ("BOX",          (0,0), (-1,-1), 0, colors.white),
        ("TOPPADDING",   (0,0), (-1,-1), 18),
        ("BOTTOMPADDING",(0,0), (-1,-1), 18),
        ("LEFTPADDING",  (0,0), (-1,-1), 30),
        ("RIGHTPADDING", (0,0), (-1,-1), 30),
        ("ROUNDEDCORNERS", [12]),
    ]))
    story.append(t_capa)
    story.append(Spacer(1, 1.5*cm))

    story.append(Paragraph(
        "Este manual descreve todos os parâmetros de entrada, telas, cálculos e "
        "interpretações do sistema Kairos DSS. Qualquer operador ou técnico agrícola "
        "pode utilizar este documento como referência completa.",
        estilo("CapaDesc", fontSize=11, textColor=HexColor("#555555"),
               alignment=TA_CENTER, fontName="Helvetica", leading=16)
    ))
    story.append(PageBreak())

    # =========================================================================
    # SUMÁRIO
    # =========================================================================
    story.append(Paragraph("Sumário", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=VERDE_CLARO, spaceAfter=10))

    sumario = [
        ("1.", "O que é o Kairos DSS", "3"),
        ("2.", "Como usar o programa — Passo a Passo", "3"),
        ("3.", "Arquivos de Entrada", "4"),
        ("4.", "Parâmetros GIS (Processamento Espacial)", "5"),
        ("5.", "Blocos Operacionais", "6"),
        ("6.", "Custos por Hora da Máquina", "7"),
        ("7.", "Velocidade e Eficiência Operacional", "9"),
        ("8.", "Produção Agronômica", "10"),
        ("9.", "Riscos e Penalidades", "12"),
        ("10.", "Exportação de Shapefiles", "13"),
        ("11.", "Tela: Mapa Interativo", "14"),
        ("12.", "Tela: Ranking de Blocos", "15"),
        ("13.", "Tela: Resumo por Talhão", "16"),
        ("14.", "Tela: Detalhamento por Linha", "16"),
        ("15.", "Fórmulas e Cálculos Completos", "17"),
        ("16.", "Interpretando os Resultados", "19"),
        ("17.", "Tabela de Referência — Valores Recomendados", "20"),
    ]
    for num, titulo, pag in sumario:
        story.append(Paragraph(
            f'<font color="#2E7D32"><b>{num}</b></font>&nbsp;&nbsp;{titulo}'
            f'<font color="#9E9E9E">  ....................................  {pag}</font>',
            estilo("SumItem", fontSize=10, fontName="Helvetica",
                   spaceBefore=3, spaceAfter=3, leading=14)
        ))
    story.append(PageBreak())

    # =========================================================================
    # 1. O QUE É O KAIROS DSS
    # =========================================================================
    story.append(Paragraph("1. O que é o Kairos DSS", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O <b>Kairos DSS</b> (Decision Support System) é um aplicativo de computador que "
        "ajuda o técnico agrícola a decidir <b>quais linhas de cana-de-açúcar devem ser "
        "replantadas</b> pelo Kairos (plantadora automática da Agricef), levando em conta "
        "não apenas o tamanho das falhas, mas também a <b>viabilidade econômica e operacional</b> "
        "de cada intervenção.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "O que o sistema faz",
        "1. Lê três arquivos espaciais (shapefiles): contorno dos talhões, linhas de plantio e "
        "falhas detectadas por drone.<br/>"
        "2. Calcula o comprimento e percentual de falha de cada linha.<br/>"
        "3. Agrupa linhas vizinhas em Blocos Operacionais contínuos.<br/>"
        "4. Calcula o custo real por hora da máquina e o retorno esperado por bloco.<br/>"
        "5. Determina o IOI (Índice Operacional Integrado) — R$/hora — de cada bloco.<br/>"
        "6. Classifica blocos em Viáveis (IOI &gt; 0) ou Inviáveis.<br/>"
        "7. Exporta shapefiles com apenas as linhas viáveis para uso no piloto automático.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "O que é o IOI — Índice Operacional Integrado",
        "O IOI mede quanto a operação ganha (em R$) por cada hora de trabalho do Kairos:<br/>"
        "<b>IOI = Lucro do Bloco ÷ Tempo Total de Operação (horas)</b><br/><br/>"
        "Um IOI positivo significa que a receita do replantio supera todos os custos. "
        "Um IOI negativo significa prejuízo — o custo da operação não se paga.",
        AZUL_ESCURO, AZUL_BG, AZUL_ESCURO
    ))

    # =========================================================================
    # 2. PASSO A PASSO
    # =========================================================================
    story.append(Paragraph("2. Como usar o programa — Passo a Passo", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    passos = [
        ("Passo 1 — Abrir o programa",
         "No terminal Miniconda, ative o ambiente e execute:<br/>"
         "<font face='Courier' size='9' color='#1A237E'>conda activate kairos<br/>"
         "streamlit run kairos_app.py</font><br/>"
         "O programa abrirá automaticamente no navegador."),
        ("Passo 2 — Fazer upload dos 3 arquivos",
         "Na barra lateral esquerda, clique em <b>📂 Arquivos de Entrada</b> e carregue os três ZIPs: "
         "Contorno, Linhas e Falhas. Cada ZIP deve conter um shapefile completo "
         "(.shp + .shx + .dbf + .prj)."),
        ("Passo 3 — Configurar os parâmetros",
         "Ajuste os parâmetros nas seções da barra lateral conforme os dados reais da sua operação. "
         "Os valores padrão são uma referência, mas devem ser calibrados para cada fazenda."),
        ("Passo 4 — Clicar em PROCESSAR",
         "Clique no botão <b>▶ PROCESSAR</b> no final da barra lateral. O sistema fará o "
         "processamento GIS (pode demorar 10–60 segundos dependendo do tamanho dos arquivos)."),
        ("Passo 5 — Analisar os resultados",
         "Use as 4 abas para analisar: Mapa (visualização espacial), Ranking de Blocos "
         "(lista por IOI), Por Talhão (resumo agrupado) e Linhas (detalhe individual)."),
        ("Passo 6 — Ajustar parâmetros econômicos",
         "Qualquer mudança nos parâmetros econômicos (custos, produção, riscos) recalcula "
         "automaticamente o IOI sem precisar reprocessar os arquivos GIS."),
        ("Passo 7 — Exportar",
         "Quando satisfeito com os resultados, clique em <b>📦 Exportar SHPs Viáveis</b>. "
         "Os shapefiles serão gravados na pasta configurada, prontos para o piloto automático."),
    ]
    for titulo, desc in passos:
        story.append(KeepTogether([
            Paragraph(f"<b>{titulo}</b>", H3),
            Paragraph(desc, CORPO),
            Spacer(1, 0.2*cm),
        ]))

    story.append(PageBreak())

    # =========================================================================
    # 3. ARQUIVOS DE ENTRADA
    # =========================================================================
    story.append(Paragraph("3. Arquivos de Entrada", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O sistema aceita três camadas espaciais, cada uma comprimida em um arquivo ZIP. "
        "Todos os arquivos devem estar no mesmo Sistema de Referência de Coordenadas (SRC) "
        "projetado em metros (ex: SIRGAS 2000 / UTM).",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    arqs = [
        ("Contorno dos Talhões",
         "Polígonos que delimitam cada talhão da fazenda. O sistema usa esta camada para "
         "recortar as linhas e falhas de cada talhão individualmente. Deve ter uma coluna "
         "com o identificador do talhão (padrão: TALHAO)."),
        ("Linhas de Plantio",
         "Linhas (geometrias do tipo LineString) que representam as fileiras de cana. "
         "Cada linha deve estar contida dentro de um talhão. O FID (identificador único) "
         "é atribuído automaticamente pelo sistema após o processamento."),
        ("Falhas de Drone",
         "Linhas ou polígonos que representam as falhas de stand (regiões sem plantas) "
         "detectadas por levantamento de drone ou outro método. O sistema aplica um buffer "
         "de 0,3 m nestas geometrias antes de cruzar com as linhas de plantio."),
    ]
    for nome, desc in arqs:
        story.append(caixa(f"📄 {nome}", desc, AZUL_ESCURO, AZUL_BG, AZUL_ESCURO))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Campo identificador do Talhão", H2))
    story.append(Paragraph(
        "Nome da coluna no shapefile de contorno que identifica cada talhão. Valor padrão: "
        "<b>TALHAO</b>. Se sua coluna tem outro nome (ex: ID_TALHAO, NOME, COD), altere "
        "este campo antes de processar.",
        CORPO
    ))
    story.append(caixa(
        "⚠️ Atenção — Formato do ZIP",
        "O ZIP deve conter os arquivos do shapefile na raiz (não dentro de subpastas). "
        "Arquivos necessários: arquivo.shp, arquivo.shx, arquivo.dbf, arquivo.prj. "
        "O arquivo .prj é obrigatório — define o sistema de coordenadas.",
        AMARELO, AMARELO_BG, LARANJA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 4. PARÂMETROS GIS
    # =========================================================================
    story.append(Paragraph("4. Parâmetros GIS (Processamento Espacial)", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Estes parâmetros controlam como o sistema processa as geometrias espaciais. "
        "Uma mudança aqui exige novo clique em PROCESSAR (reprocessa os arquivos GIS).",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Buffer nas falhas (m)", "0,30 m",
         "Margem aplicada ao redor de cada falha antes de cruzar com as linhas. "
         "Garante que falhas muito finas (como bordas de polígonos) sejam capturadas. "
         "<b>Recomendado: 0,20 a 0,50 m.</b> Aumentar demais pode capturar falhas "
         "que não afetam a linha."),
        ("Comprimento mínimo de falha (m)", "1,50 m",
         "Segmento de falha menor que este valor é ignorado. Evita processar micro-falhas "
         "sem relevância agronômica. <b>Recomendado: 1,0 a 2,0 m.</b> Para ser mais "
         "rigoroso na seleção, aumente para 2,0 ou 3,0 m."),
        ("Espaçamento entre linhas (m)", "1,50 m",
         "Distância entre duas linhas de plantio adjacentes. Usado para calcular a área "
         "de falha em hectares: <b>Área (ha) = Comprimento Falha (m) × Espaçamento (m) ÷ 10.000.</b> "
         "Verifique o espaçamento real do talhão."),
    ]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Como o processamento GIS funciona", H2))
    story.append(Paragraph(
        "O sistema executa as seguintes etapas para cada talhão:",
        CORPO
    ))
    etapas_gis = [
        "Recorta as linhas de plantio e falhas dentro do polígono do talhão.",
        "Aplica o buffer configurado ao redor das falhas, transformando-as em polígonos.",
        "Cruza (intersecta) as linhas de plantio com os polígonos de falha.",
        "Filtra apenas os segmentos de interseção com comprimento > mínimo configurado.",
        "Soma os comprimentos de falha por linha (soma_falhas) e calcula o percentual.",
        "Classifica cada linha em uma das 11 categorias de percentual de falha.",
    ]
    for i, e in enumerate(etapas_gis, 1):
        story.append(Paragraph(f"<b>{i}.</b> {e}", BULLET))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Classificação das linhas por percentual de falha", H2))
    story.append(Spacer(1, 0.2*cm))

    classes = [
        ["Classe", "% de Falha", "Interpretação", "Cor no Mapa"],
        ["0-2",   "0 a 2%",   "Stand praticamente completo — geralmente não justifica replantio", "Verde escuro"],
        ["2-4",   "2 a 4%",   "Falha muito baixa — analisar caso a caso", "Verde médio"],
        ["4-6",   "4 a 6%",   "Falha leve", "Verde claro"],
        ["6-8",   "6 a 8%",   "Falha moderada — início da zona de atenção", "Amarelo-verde"],
        ["8-10",  "8 a 10%",  "Falha moderada", "Amarelo"],
        ["10-12", "10 a 12%", "Falha significativa — replantio recomendado", "Laranja claro"],
        ["12-14", "12 a 14%", "Falha alta", "Laranja"],
        ["14-16", "14 a 16%", "Falha muito alta", "Vermelho médio"],
        ["16-18", "16 a 18%", "Falha crítica", "Vermelho escuro"],
        ["18-20", "18 a 20%", "Falha crítica severa", "Bordô"],
        [">20",   "Acima de 20%", "Falha extrema — prioritário para replantio", "Quase preto"],
    ]
    col_cls = [1.5*cm, 2.2*cm, 8.5*cm, 3.5*cm]
    t_cls = Table(
        [[Paragraph(c, TABELA_HEADER) for c in classes[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in classes[1:]],
        colWidths=col_cls, repeatRows=1
    )
    cores_linhas = [
        "#1a9850","#66bd63","#a6d96a","#d9ef8b","#fee08b",
        "#fdae61","#f46d43","#d73027","#a50026","#7f0000","#4d0000"
    ]
    cls_style = [
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]
    for i, cor in enumerate(cores_linhas):
        cls_style.append(("BACKGROUND", (0, i+1), (0, i+1), HexColor(cor)))
        cls_style.append(("TEXTCOLOR",  (0, i+1), (0, i+1), colors.white))
    t_cls.setStyle(TableStyle(cls_style))
    story.append(t_cls)

    story.append(PageBreak())

    # =========================================================================
    # 5. BLOCOS OPERACIONAIS
    # =========================================================================
    story.append(Paragraph("5. Blocos Operacionais", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Um <b>Bloco Operacional</b> é um conjunto de linhas vizinhas com falha que o Kairos "
        "pode percorrer continuamente, sem precisar sair do talhão e reentrar. Agrupar linhas "
        "próximas em um bloco melhora a eficiência porque reduz o número de manobras.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Por que blocos operacionais importam?",
        "Uma linha isolada exige que o Kairos entre, saia e reposicione para cada intervenção — "
        "muito tempo improdutivo. Um bloco de 10 linhas contínuas usa o mesmo tempo de entrada/saída "
        "para cobrir 10 linhas, tornando a operação muito mais eficiente e rentável.",
        AZUL_ESCURO, AZUL_BG, AZUL_ESCURO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Distância de agrupamento — eps (m)", "6,0 m",
         "Distância máxima entre duas linhas para serem consideradas adjacentes e pertencerem "
         "ao mesmo bloco. Com espaçamento de 1,5 m entre linhas, um eps de 6 m agrupa linhas "
         "separadas por até 4 fileiras sem falha. <b>Recomendado: 4 a 8 m.</b> Aumente para "
         "criar blocos maiores; diminua para ser mais restritivo."),
        ("Penalidade de isolamento (min)", "15,0 min",
         "Minutos extras adicionados ao tempo de manobra de blocos com apenas UMA linha "
         "(linhas isoladas). Representa o tempo adicional de reposicionamento da máquina. "
         "<b>Recomendado: 10 a 20 min.</b> Use 0 para não penalizar linhas isoladas. "
         "Valores altos tornam linhas isoladas economicamente inviáveis."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Como o agrupamento funciona", H2))
    story.append(Paragraph(
        "O sistema aplica um buffer de eps/2 metros ao redor de cada linha com falha. "
        "Duas linhas cujos buffers se tocam são consideradas adjacentes. "
        "Usando o algoritmo de componentes conectados, todas as linhas conectadas "
        "direta ou indiretamente formam um único bloco. O identificador do bloco "
        "segue o padrão: <b>TALHAO_B001</b>, <b>TALHAO_B002</b>, etc.",
        CORPO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 6. CUSTOS POR HORA
    # =========================================================================
    story.append(Paragraph("6. Custos por Hora da Máquina", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O custo por hora é calculado somando quatro componentes: diesel, mão de obra, "
        "manutenção e depreciação. Este valor é usado para calcular o custo de máquina "
        "de cada bloco operacional.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Fórmula do Custo por Hora:", H2))
    story.append(Paragraph(
        "Custo/hora  =  (Diesel L/h × R$/L)  +  (Salários / Horas mês)  +  "
        "(Manutenção / Horas mês)  +  (Depreciação anual ÷ 12 ÷ Horas mês)",
        FORMULA
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Consumo diesel (L/h)", "8,0 L/h",
         "Litros de diesel consumidos por hora de operação. Consulte o manual da máquina "
         "ou meça em campo. <b>Recomendado: 6 a 12 L/h</b> para plantadoras de cana."),
        ("Preço do diesel (R$/L)", "R$ 6,50",
         "Preço médio pago pelo litro de diesel na fazenda (já com frete). "
         "Atualize conforme o preço atual de compra."),
        ("Salário do operador (R$/mês)", "R$ 3.500",
         "Salário bruto mensal do operador da máquina, incluindo encargos sociais "
         "(INSS, FGTS). <b>Inclua os encargos</b> — o custo real para a empresa é "
         "aproximadamente 1,7× o salário líquido."),
        ("Número de auxiliares", "1",
         "Quantidade de auxiliares de campo que acompanham a operação "
         "(batedores, abastecedores). Use 0 se a operação for apenas com o operador."),
        ("Salário por auxiliar (R$/mês)", "R$ 2.500",
         "Salário bruto mensal de cada auxiliar, incluindo encargos."),
        ("Manutenção fixa mensal (R$/mês)", "R$ 800",
         "Custo médio mensal com manutenção preventiva e corretiva da máquina "
         "(peças, lubrificantes, serviços). Divida o custo anual estimado por 12. "
         "<b>Recomendado: R$ 500 a R$ 2.000/mês</b> dependendo da idade da máquina."),
        ("Depreciação anual (R$/ano)", "R$ 36.000",
         "Quanto a máquina perde de valor por ano. Calcule como: "
         "<b>(Valor de compra − Valor residual) ÷ Vida útil em anos.</b> "
         "Exemplo: máquina de R$ 400.000, valor residual R$ 40.000, vida útil 10 anos → "
         "R$ 36.000/ano."),
        ("Horas trabalhadas por mês (h/mês)", "176 h",
         "Total de horas que a máquina opera por mês (não horas do mês, mas horas "
         "efetivamente em campo). Padrão: 22 dias × 8 horas = 176 h. "
         "Ajuste para a realidade da sua operação (ex: safra intensiva = 200 h/mês)."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Exemplo de cálculo — Custo por hora",
        "Diesel: 8 L/h × R$ 6,50 = R$ 52,00/h<br/>"
        "Mão de obra: (R$ 3.500 + 1 × R$ 2.500) ÷ 176 h = R$ 34,09/h<br/>"
        "Manutenção: R$ 800 ÷ 176 h = R$ 4,55/h<br/>"
        "Depreciação: (R$ 36.000 ÷ 12) ÷ 176 h = R$ 17,05/h<br/>"
        "<b>TOTAL: R$ 107,69/hora</b>",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 7. VELOCIDADE E EFICIÊNCIA
    # =========================================================================
    story.append(Paragraph("7. Velocidade e Eficiência Operacional", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Estes parâmetros definem quanto tempo a máquina gasta efetivamente plantando "
        "versus manobras e deslocamentos improdutivos.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Velocidade efetiva de plantio (m/min)", "33,3 m/min",
         "Velocidade real da máquina durante o plantio dentro da linha de falha. "
         "Conversão: <b>2 km/h = 33,3 m/min | 3 km/h = 50 m/min | 1,5 km/h = 25 m/min.</b> "
         "Meça em campo com GPS ou cronômetro. Recomendado: 25 a 50 m/min."),
        ("Tempo de manobra por linha (min)", "2,0 min",
         "Tempo gasto para posicionar a máquina no início de cada nova linha: "
         "curva de retorno, alinhamento, acionamento do sistema. "
         "<b>Recomendado: 1,5 a 4 min/linha.</b> Talhões estreitos com muitas manobras = maior valor. "
         "Meça cronometrando 10 manobras consecutivas e calculando a média."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Como os tempos são calculados por bloco", H2))
    story.append(Paragraph("Tempo de Plantio (min)  =  Total de Falhas no Bloco (m)  ÷  Velocidade (m/min)", FORMULA))
    story.append(Paragraph(
        "Tempo de Manobra (min)  =  Número de Linhas no Bloco  ×  Tempo por Manobra (min)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "+ Penalidade de Isolamento (se bloco de 1 linha)",
        FORMULA
    ))
    story.append(Paragraph("Tempo Total (min)  =  Tempo de Plantio  +  Tempo de Manobra", FORMULA))
    story.append(Paragraph("Eficiência (%)  =  (Tempo de Plantio  ÷  Tempo Total)  ×  100", FORMULA))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Interpretando a Eficiência (%)",
        "<b>Eficiência alta (70–90%):</b> Bloco com muitas linhas contínuas e falhas longas. "
        "A máquina passa a maior parte do tempo plantando. Ideal.<br/>"
        "<b>Eficiência média (40–70%):</b> Bloco misto, algumas linhas com falha curta. Aceitável.<br/>"
        "<b>Eficiência baixa (&lt;40%):</b> Poucas linhas, muita manobra. Pode ser inviável mesmo "
        "com falhas significativas.",
        AZUL_ESCURO, AZUL_BG, AZUL_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 8. PRODUÇÃO AGRONÔMICA
    # =========================================================================
    story.append(Paragraph("8. Produção Agronômica", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Estes parâmetros estimam a receita que o replantio vai gerar. "
        "São os parâmetros com maior impacto no IOI — valores superestimados "
        "tornam linhas inviáveis parecer viáveis.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Ganho esperado por replantio (t/ha de falha)", "60,0 t/ha",
         "Toneladas de cana colhidas por hectare de ÁREA DE FALHA replantada. "
         "NÃO é a produtividade do talhão inteiro — é o ganho incremental da área "
         "que estava vazia e foi replantada.<br/>"
         "<b>Como calcular:</b> Use a produtividade média do talhão × 0,60 como estimativa "
         "conservadora (a planta nova rende ~60% da cana estabelecida no 1º corte).<br/>"
         "<b>Exemplos:</b> Talhão com 80 t/ha → use 48 t/ha. Talhão com 100 t/ha → use 60 t/ha.<br/>"
         "<b>Recomendado: 30 a 70 t/ha.</b> Se tiver histórico de replantio na fazenda, use esse dado."),
        ("Preço da tonelada (R$/t)", "R$ 140,00",
         "Preço líquido recebido pela tonelada de cana, já descontados fretes e taxas. "
         "Use o ATR médio da usina multiplicado pelo preço do ATR, ou o preço médio do contrato. "
         "<b>Recomendado: R$ 100 a R$ 200/t</b> dependendo da região e usina."),
        ("Taxa de pegamento / germinação (%)", "85%",
         "Percentual das mudas replantadas que efetivamente brotam e se estabelecem. "
         "<b>Recomendado: 70 a 90%.</b> Use dados históricos do viveiro ou experimentos "
         "da fazenda. Para replantio mecanizado de cana inteira: 75–85%. "
         "Para toletes: 80–90% em condições ideais."),
        ("Custo de muda (R$/ha de falha)", "R$ 400,00",
         "Custo do material de plantio (muda, tolete ou colmo) por hectare de área replantada. "
         "Inclua o custo de colheita, transporte e preparo da muda. "
         "<b>Recomendado: R$ 200 a R$ 800/ha</b> dependendo do tipo de muda e distância. "
         "Este custo é somado ao custo de máquina para calcular o custo total do bloco."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Como a receita é calculada por bloco", H2))
    story.append(Paragraph(
        "Área de Falha (ha)  =  Total Falhas (m)  ×  Espaçamento (m)  ÷  10.000",
        FORMULA
    ))
    story.append(Paragraph(
        "Receita Bruta (R$)  =  Área de Falha (ha)  ×  Ganho Esperado (t/ha)  ×  "
        "(Taxa de Pegamento ÷ 100)  ×  Preço (R$/t)",
        FORMULA
    ))
    story.append(Paragraph(
        "Receita Líquida (R$)  =  Receita Bruta  ×  (1 − Penalidade Amassamento ÷ 100)  "
        "×  (1 − Risco Climático ÷ 100)",
        FORMULA
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Exemplo numérico de receita",
        "Bloco com 150 m de falha, espaçamento 1,5 m:<br/>"
        "Área: 150 × 1,5 ÷ 10.000 = <b>0,0225 ha</b><br/>"
        "Receita Bruta: 0,0225 × 60 t/ha × 0,85 × R$140 = <b>R$ 160,65</b><br/>"
        "Receita Líquida (5% amassamento, 10% risco): R$160,65 × 0,95 × 0,90 = <b>R$ 137,36</b>",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 9. RISCOS E PENALIDADES
    # =========================================================================
    story.append(Paragraph("9. Riscos e Penalidades", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Fatores de risco que reduzem a receita esperada do replantio.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Penalidade de amassamento (%)", "5%",
         "Redução percentual na receita devido ao dano causado pelo trânsito da máquina "
         "sobre a cana nas linhas adjacentes (amassamento). "
         "<b>Recomendado: 3 a 10%.</b> Solos úmidos ou cana alta = maior penalidade. "
         "Use 0% se o replantio for feito com a cana ainda baixa."),
        ("Desconto de risco climático (%)", "10%",
         "Redução percentual na receita para considerar a possibilidade de a janela "
         "climática ser desfavorável (seca após replantio, geada, excesso de chuva). "
         "<b>Recomendado: 5 a 20%.</b> Regiões com distribuição irregular de chuvas = "
         "maior desconto. Use valores mais altos em safras de El Niño ou La Niña."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Efeito combinado dos riscos na receita",
        "Os dois descontos são aplicados multiplicativamente:<br/>"
        "Receita Líquida = Receita Bruta × (1 − 5% amassamento) × (1 − 10% risco climático)<br/>"
        "= Receita Bruta × 0,95 × 0,90 = Receita Bruta × <b>0,855</b><br/><br/>"
        "Isso significa que, com esses valores, a receita líquida é 85,5% da bruta. "
        "Aumente os descontos para análises mais conservadoras.",
        LARANJA, LARANJA_BG, LARANJA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 10. EXPORTAÇÃO
    # =========================================================================
    story.append(Paragraph("10. Exportação de Shapefiles", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(tabela_params([
        ("Pasta de saída dos SHPs", "~/kairos_saida",
         "Caminho completo da pasta onde os shapefiles serão gravados. "
         "Exemplos: C:\\Kairos\\Exportacao ou D:\\Fazenda\\Replantio_2025. "
         "A pasta é criada automaticamente se não existir."),
    ]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("O que é exportado", H2))
    story.append(Paragraph(
        "São exportadas somente as linhas com <b>IOI &gt; 0</b> (viáveis). "
        "Um arquivo .shp separado é gerado para cada talhão, nomeado como "
        "<b>talhao_NOME.shp</b>. Cada arquivo contém as seguintes colunas:",
        CORPO
    ))
    colunas_exp = [
        ["Coluna", "Descrição"],
        ["TALHAO", "Identificador do talhão"],
        ["FID", "Identificador único da linha dentro do talhão"],
        ["bloco_id", "Identificador do Bloco Operacional (ex: T01_B003)"],
        ["comp_linha", "Comprimento total da linha dentro do talhão (metros)"],
        ["soma_falhas", "Comprimento total das falhas na linha (metros)"],
        ["perc_falhas", "Percentual de falha da linha (%)"],
        ["classe", "Classe de falha (ex: 8-10, >20)"],
        ["ioi", "IOI do bloco ao qual a linha pertence (R$/hora)"],
        ["eficiencia_pct", "Eficiência operacional do bloco (%)"],
        ["lucro_bloco", "Lucro estimado do bloco (R$)"],
        ["geometry", "Geometria da linha (LineString) — para uso no QGIS/piloto automático"],
    ]
    t_exp = Table(
        [[Paragraph(c, TABELA_HEADER) for c in colunas_exp[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in colunas_exp[1:]],
        colWidths=[3.5*cm, 13.2*cm], repeatRows=1
    )
    t_exp.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    story.append(t_exp)

    story.append(PageBreak())

    # =========================================================================
    # 11. MAPA
    # =========================================================================
    story.append(Paragraph("11. Tela: Mapa Interativo", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O mapa exibe três camadas sobrepostas que podem ser ligadas e desligadas "
        "usando o controle de camadas no canto superior direito do mapa.",
        CORPO
    ))
    story.append(Spacer(1, 0.2*cm))

    camadas = [
        ("Camada 1: Todas as linhas (% Falha)",
         "Mostra TODAS as linhas de plantio do talhão coloridas pela classe de percentual de falha "
         "(da escala verde→preto). Use esta camada para ter uma visão geral da distribuição das falhas "
         "no campo. Linhas sem falha (0%) também aparecem. "
         "Ao passar o mouse sobre uma linha, o tooltip mostra: Talhão, Classe e % Falha."),
        ("Camada 2: Linhas viáveis (por Bloco)",
         "Mostra apenas as linhas com IOI > 0, coloridas por Bloco Operacional "
         "(cada bloco tem uma cor distinta). Use esta camada para ver exatamente onde o Kairos "
         "deve operar. O tooltip mostra: Talhão, Bloco, Classe, % Falha, IOI e Eficiência."),
        ("Camada 3: Blocos Operacionais",
         "Polígonos semitransparentes que mostram a área envolvente de cada bloco viável. "
         "Permite visualizar a extensão espacial dos blocos. O tooltip mostra: Rank, Bloco, "
         "Talhão, Número de linhas, Total de Falhas, IOI e Eficiência."),
    ]
    for titulo, desc in camadas:
        story.append(caixa(titulo, desc, AZUL_ESCURO, AZUL_BG, AZUL_ESCURO))
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.2*cm))
    story.append(caixa(
        "Legenda no canto do mapa",
        "A legenda fixa no canto inferior direito do mapa mostra as 11 cores e seus respectivos "
        "percentuais de falha. Use como referência para interpretar a Camada 1.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 12. RANKING DE BLOCOS
    # =========================================================================
    story.append(Paragraph("12. Tela: Ranking de Blocos", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Tabela completa com todos os Blocos Operacionais, ordenados do maior para o menor IOI. "
        "Linhas com fundo <b>verde</b> são viáveis (IOI &gt; 0). "
        "Linhas com fundo <b>vermelho</b> são inviáveis (IOI ≤ 0).",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    colunas_rank = [
        ["Coluna", "O que significa"],
        ["Rank", "Posição no ranking (1 = melhor IOI, mais rentável)"],
        ["Bloco", "Identificador do bloco (TALHAO_BNNN)"],
        ["Talhão", "Talhão ao qual o bloco pertence"],
        ["Linhas", "Quantidade de linhas no bloco"],
        ["Falhas (m)", "Comprimento total das falhas em todas as linhas do bloco"],
        ["Área (ha)", "Área total de falha em hectares (Falhas × Espaçamento ÷ 10.000)"],
        ["T. Plantio (min)", "Tempo efetivo de plantio das falhas do bloco"],
        ["T. Manobra (min)", "Tempo de manobra (inclui penalidade se bloco unitário)"],
        ["T. Total (min)", "Tempo total de operação do bloco"],
        ["Eficiência (%)", "T. Plantio ÷ T. Total × 100"],
        ["Receita Líq. (R$)", "Receita após pegamento, amassamento e risco climático"],
        ["Custo Total (R$)", "Custo máquina + custo muda"],
        ["Lucro (R$)", "Receita Líquida − Custo Total"],
        ["IOI (R$/h)", "Lucro ÷ Tempo Total (horas) — o indicador principal"],
        ["Viável", "✅ SIM se IOI > 0  |  ❌ NÃO se IOI ≤ 0"],
    ]
    t_rank = Table(
        [[Paragraph(c, TABELA_HEADER) for c in colunas_rank[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in colunas_rank[1:]],
        colWidths=[4.0*cm, 12.7*cm], repeatRows=1
    )
    t_rank.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    story.append(t_rank)

    story.append(PageBreak())

    # =========================================================================
    # 13. POR TALHÃO
    # =========================================================================
    story.append(Paragraph("13. Tela: Resumo por Talhão", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Visão agregada por talhão. Mostra totais e médias para comparar o desempenho "
        "de diferentes talhões. Útil para priorizar em qual talhão começar a operação.",
        CORPO
    ))
    story.append(Spacer(1, 0.2*cm))
    colunas_t = [
        ["Coluna", "O que significa"],
        ["Talhão", "Identificador do talhão"],
        ["Blocos", "Total de blocos operacionais no talhão"],
        ["Blocos Viáveis", "Quantidade de blocos com IOI > 0"],
        ["% Blocos Viáveis", "Percentual de blocos viáveis no talhão"],
        ["Total Linhas", "Total de linhas com falha no talhão"],
        ["Total Falhas (m)", "Soma total de todos os comprimentos de falha"],
        ["Lucro Estimado (R$)", "Soma do lucro dos blocos viáveis do talhão"],
        ["IOI Médio (R$/h)", "Média do IOI dos blocos viáveis"],
        ["Eficiência Média (%)", "Média da eficiência dos blocos viáveis"],
    ]
    t_talhao = Table(
        [[Paragraph(c, TABELA_HEADER) for c in colunas_t[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in colunas_t[1:]],
        colWidths=[4.0*cm, 12.7*cm], repeatRows=1
    )
    t_talhao.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    story.append(t_talhao)

    story.append(Spacer(1, 0.5*cm))

    # =========================================================================
    # 14. LINHAS
    # =========================================================================
    story.append(Paragraph("14. Tela: Detalhamento por Linha", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Tabela com uma linha por linha de plantio. Possui dois filtros:",
        CORPO
    ))
    story.append(Paragraph(
        "<b>Filtrar por talhão:</b> Seleciona um talhão específico ou mostra todos.", BULLET))
    story.append(Paragraph(
        "<b>Apenas viáveis:</b> Quando marcado, mostra somente as linhas que serão exportadas "
        "(IOI &gt; 0). Esta é a visualização mais direta de O QUE o Kairos vai plantar.", BULLET))

    story.append(PageBreak())

    # =========================================================================
    # 15. FÓRMULAS COMPLETAS
    # =========================================================================
    story.append(Paragraph("15. Fórmulas e Cálculos Completos", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph("15.1 Métricas Espaciais (por linha)", H2))
    formulas1 = [
        ("comp_linha (m)", "Comprimento da linha após recorte no talhão, calculado pela geometria real."),
        ("soma_falhas (m)", "Soma dos comprimentos de todos os segmentos de falha intersectados na linha."),
        ("perc_falhas (%)", "soma_falhas ÷ comp_linha × 100"),
        ("classe", "Bin do perc_falhas: 0-2, 2-4, 4-6, 6-8, 8-10, 10-12, 12-14, 14-16, 16-18, 18-20, >20"),
    ]
    for nome, desc in formulas1:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.2 Custo por Hora (escalar — igual para todos os blocos)", H2))
    story.append(Paragraph(
        "custo_hora  =  (diesel_lh × preco_diesel)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "+  (salario_operador + n_auxiliares × salario_auxiliar) ÷ horas_mes<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "+  manutencao_mensal ÷ horas_mes<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "+  (depreciacao_anual ÷ 12) ÷ horas_mes",
        FORMULA
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.3 Métricas por Bloco Operacional", H2))
    formulas_bloco = [
        ("comp_falha_total (m)", "Σ soma_falhas de todas as linhas do bloco"),
        ("area_falha_ha (ha)",   "comp_falha_total × espacamento ÷ 10.000"),
        ("tempo_plantio_min",    "comp_falha_total ÷ velocidade_plantio_mmin"),
        ("tempo_manobra_min",    "n_linhas × tempo_manobra_fixo_min  [+ penalidade_isolamento_min se n_linhas = 1]"),
        ("tempo_total_min",      "tempo_plantio_min + tempo_manobra_min"),
        ("eficiencia_pct (%)",   "tempo_plantio_min ÷ tempo_total_min × 100"),
        ("receita_bruta (R$)",   "area_falha_ha × ganho_esperado_tha × (taxa_pegamento ÷ 100) × preco_tonelada"),
        ("receita_liquida (R$)", "receita_bruta × (1 − penalidade_amassamento ÷ 100) × (1 − risco_climatico ÷ 100)"),
        ("custo_maquina (R$)",   "custo_hora × (tempo_total_min ÷ 60)"),
        ("custo_insumos (R$)",   "area_falha_ha × custo_muda_tha"),
        ("custo_total (R$)",     "custo_maquina + custo_insumos"),
        ("lucro_bloco (R$)",     "receita_liquida − custo_total"),
        ("ioi (R$/h)",           "lucro_bloco ÷ (tempo_total_min ÷ 60)"),
        ("viavel",               "TRUE se ioi > 0, FALSE caso contrário"),
        ("ranking",              "Posição do bloco ordenado por ioi decrescente (rank 1 = maior IOI)"),
    ]
    for nome, desc in formulas_bloco:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))

    story.append(PageBreak())

    # =========================================================================
    # 16. INTERPRETANDO RESULTADOS
    # =========================================================================
    story.append(Paragraph("16. Interpretando os Resultados", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph("O que fazer quando MUITAS linhas são viáveis", H2))
    story.append(caixa(
        "Sintoma: quase todas as linhas têm IOI > 0",
        "Causa provável: parâmetros de produção superestimados (ganho muito alto, preço muito alto, "
        "taxa de pegamento muito alta) ou custos subestimados.<br/><br/>"
        "Solução: reduza o <b>Ganho esperado</b> para 40–50 t/ha, verifique o preço real da tonelada, "
        "aumente a penalidade de amassamento e o risco climático para valores mais conservadores. "
        "O objetivo é que apenas linhas com falha significativa E em blocos contínuos sejam viáveis.",
        LARANJA, LARANJA_BG, LARANJA
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("O que fazer quando NENHUMA linha é viável", H2))
    story.append(caixa(
        "Sintoma: zero blocos viáveis",
        "Causa provável: parâmetros de custo muito altos, velocidade muito baixa, "
        "ou a operação realmente não se paga neste talhão.<br/><br/>"
        "Solução: verifique se o custo por hora está correto (veja o expander 💰 na tela principal), "
        "confirme a velocidade de plantio, reduza a penalidade de isolamento. "
        "Se mesmo com parâmetros realistas não houver blocos viáveis, a operação não é economicamente "
        "recomendada para este talhão.",
        VERMELHO, HexColor("#FFEBEE"), VERMELHO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("IOI: como interpretar os valores", H2))
    ioi_tab = [
        ["IOI (R$/h)", "Interpretação", "Recomendação"],
        ["< 0",          "Prejuízo — custo supera receita",                "Não operar"],
        ["0 a 50",       "Margem muito estreita — alto risco",             "Analisar com cautela"],
        ["50 a 150",     "Viável com margem moderada",                     "Operar se logística permitir"],
        ["150 a 300",    "Boa viabilidade",                                "Prioridade normal"],
        ["300 a 500",    "Alta viabilidade — bloco eficiente",             "Alta prioridade"],
        ["> 500",        "Excelente — bloco muito contínuo e com falhas altas", "Prioridade máxima"],
    ]
    t_ioi = Table(
        [[Paragraph(c, TABELA_HEADER) for c in ioi_tab[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in ioi_tab[1:]],
        colWidths=[2.8*cm, 7.5*cm, 6.4*cm], repeatRows=1
    )
    cores_ioi = [VERMELHO, HexColor("#FF8F00"), AMARELO, VERDE_CLARO, VERDE_MEDIO, VERDE_ESCURO]
    ioi_style = [
        ("BACKGROUND", (0,0), (-1,0), VERDE_ESCURO),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",        (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0), (-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]
    for i, cor in enumerate(cores_ioi):
        ioi_style.append(("BACKGROUND", (0, i+1), (0, i+1), cor))
        ioi_style.append(("TEXTCOLOR",  (0, i+1), (0, i+1), colors.white))
    t_ioi.setStyle(TableStyle(ioi_style))
    story.append(t_ioi)

    story.append(PageBreak())

    # =========================================================================
    # 17. TABELA DE REFERÊNCIA
    # =========================================================================
    story.append(Paragraph("17. Tabela de Referência — Valores Recomendados", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Use esta tabela como ponto de partida. Sempre que possível, substitua pelos "
        "valores reais medidos na sua operação.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    ref = [
        ["Parâmetro", "Mínimo", "Padrão", "Máximo", "Como obter"],
        ["Buffer falhas (m)",          "0,10", "0,30", "0,60", "Técnico GIS"],
        ["Mín. falha (m)",             "0,50", "1,50", "3,00", "Agronômico"],
        ["Espaçamento linhas (m)",     "0,80", "1,50", "1,80", "Medir no campo"],
        ["eps agrupamento (m)",        "3,0",  "6,0",  "12,0", "Espaçamento × 4"],
        ["Penalidade isolamento (min)","0",    "15",   "30",   "Cronometrar em campo"],
        ["Diesel (L/h)",               "4",    "8",    "14",   "Manual da máquina"],
        ["Preço diesel (R$/L)",        "5,00", "6,50", "8,00", "NF de compra"],
        ["Salário operador (R$/mês)",  "2.500","3.500","6.000","RH da empresa"],
        ["Manutenção (R$/mês)",        "300",  "800",  "2.500","Histórico oficina"],
        ["Depreciação (R$/ano)",       "15.000","36.000","80.000","Contabilidade"],
        ["Horas/mês",                  "120",  "176",  "220",  "Registro de campo"],
        ["Vel. plantio (m/min)",       "20",   "33",   "55",   "GPS ou cronômetro"],
        ["Tempo manobra (min)",        "1,0",  "2,0",  "5,0",  "Cronometrar 10×"],
        ["Ganho esperado (t/ha)",      "20",   "50",   "90",   "Histórico replantio"],
        ["Preço tonelada (R$/t)",      "80",   "140",  "220",  "Contrato usina"],
        ["Taxa pegamento (%)",         "60",   "85",   "95",   "Experimento campo"],
        ["Custo muda (R$/ha)",         "150",  "400",  "900",  "Viveiro/colheita"],
        ["Penalidade amassamento (%)","0",     "5",    "15",   "Avaliação agronômica"],
        ["Risco climático (%)",        "0",    "10",   "25",   "Histórico climático"],
    ]
    col_ref = [5.0*cm, 1.8*cm, 1.8*cm, 1.8*cm, 6.3*cm]
    t_ref = Table(
        [[Paragraph(c, TABELA_HEADER) for c in ref[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in ref[1:]],
        colWidths=col_ref, repeatRows=1
    )
    t_ref.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ("BOX",          (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("BACKGROUND",   (1,0), (3,0),  AZUL_ESCURO),
    ]))
    story.append(t_ref)

    story.append(Spacer(1, 0.5*cm))
    story.append(caixa(
        "Dica final — Calibração dos parâmetros",
        "A melhor estratégia é comparar os resultados do Kairos DSS com a operação real: "
        "após uma safra de replantio, meça a produção das linhas replantadas e compare com o "
        "ganho esperado configurado. Ajuste os parâmetros para que o modelo reflita a realidade "
        "da sua fazenda. Com parâmetros calibrados, o sistema se torna uma ferramenta de decisão "
        "confiável e o IOI passa a ser um indicador preciso de rentabilidade.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO))
    story.append(Paragraph(
        "Kairos DSS v2.0 — Agricef  |  Manual gerado automaticamente",
        CAPTION
    ))

    return story


# ── Geração ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    output = "manual_kairos.pdf"
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=2.2*cm,
        bottomMargin=1.8*cm,
        title="Kairos DSS — Manual Completo do Usuário",
        author="Agricef",
        subject="Manual do Sistema de Apoio à Decisão para Replantio de Cana",
    )
    story = build_story()
    doc.build(story, onFirstPage=cabecalho_rodape, onLaterPages=cabecalho_rodape)
    print(f"Manual gerado com sucesso: {output}")
