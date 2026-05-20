"""
Gera o Manual Completo do Kairos DSS v4.0 em PDF.
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


# ── Estilos ──────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def estilo(nome, parent="Normal", **kw):
    return ParagraphStyle(nome, parent=base[parent], **kw)

TITULO_CAPA = estilo("TituloCapa",
    fontSize=32, textColor=colors.white, alignment=TA_CENTER,
    fontName="Helvetica-Bold", leading=40, spaceAfter=10)

SUBTITULO_CAPA = estilo("SubtituloCapa",
    fontSize=16, textColor=HexColor("#C8E6C9"), alignment=TA_CENTER,
    fontName="Helvetica", leading=22)

H1 = estilo("H1",
    fontSize=18, textColor=VERDE_ESCURO, fontName="Helvetica-Bold",
    spaceBefore=18, spaceAfter=8, leading=22, leftIndent=0)

H2 = estilo("H2",
    fontSize=13, textColor=AZUL_ESCURO, fontName="Helvetica-Bold",
    spaceBefore=14, spaceAfter=5, leading=17)

H3 = estilo("H3",
    fontSize=11, textColor=VERDE_MEDIO, fontName="Helvetica-Bold",
    spaceBefore=10, spaceAfter=4, leading=14)

CORPO = estilo("Corpo",
    fontSize=10, textColor=PRETO, fontName="Helvetica",
    spaceBefore=3, spaceAfter=4, leading=14, alignment=TA_JUSTIFY)

FORMULA = estilo("Formula",
    fontSize=9.5, textColor=HexColor("#1A237E"), fontName="Courier-Bold",
    spaceBefore=4, spaceAfter=4, leading=13, leftIndent=24, backColor=AZUL_BG,
    borderPad=6)

NOTA = estilo("Nota",
    fontSize=9, textColor=HexColor("#4E342E"), fontName="Helvetica-Oblique",
    spaceBefore=3, spaceAfter=3, leading=12, leftIndent=12, backColor=AMARELO_BG,
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


# ── Cabeçalho / Rodapé ───────────────────────────────────────────────────────
def cabecalho_rodape(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(VERDE_ESCURO)
        canvas.rect(MARGEM, H - 1.5*cm, W - 2*MARGEM, 0.5*cm, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(MARGEM + 4, H - 1.25*cm, "KAIROS DSS — Manual do Usuário")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W - MARGEM - 4, H - 1.25*cm, "Agricef Kairos v4.0")
    canvas.setStrokeColor(VERDE_CLARO)
    canvas.setLineWidth(0.5)
    canvas.line(MARGEM, 1.3*cm, W - MARGEM, 1.3*cm)
    canvas.setFillColor(CINZA_MEDIO)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, 0.8*cm, f"Pagina {doc.page}")
    canvas.restoreState()


# ── Caixa colorida ───────────────────────────────────────────────────────────
def caixa(titulo, conteudo, cor_borda=VERDE_MEDIO, cor_bg=VERDE_BG, cor_titulo=VERDE_ESCURO):
    s_titulo = estilo(f"CaixaTitulo_{id(titulo)}",
        fontSize=10, textColor=cor_titulo, fontName="Helvetica-Bold",
        leading=13, backColor=cor_bg)
    s_corpo = estilo(f"CaixaCorpo_{id(titulo)}",
        fontSize=9.5, textColor=PRETO, fontName="Helvetica",
        leading=13, backColor=cor_bg, alignment=TA_JUSTIFY)
    celulas = [[Paragraph(f"<b>{titulo}</b>", s_titulo)],
               [Paragraph(conteudo, s_corpo)]]
    t = Table(celulas, colWidths=[W - 2*MARGEM - 1*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), cor_bg),
        ("BOX",          (0,0), (-1,-1), 1.5, cor_borda),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [cor_bg]),
    ]))
    return t


def tabela_params(linhas, col_widths=None):
    if col_widths is None:
        col_widths = [5.2*cm, 2.8*cm, 8.7*cm]
    header = [
        Paragraph("Parametro", TABELA_HEADER),
        Paragraph("Padrao", TABELA_HEADER),
        Paragraph("Descricao e valores recomendados", TABELA_HEADER),
    ]
    dados = [header] + [
        [Paragraph(str(r[0]), TABELA_CELL),
         Paragraph(str(r[1]), TABELA_CELL),
         Paragraph(str(r[2]), TABELA_CELL)]
        for r in linhas
    ]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, CINZA_CLARO]),
        ("BOX",           (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t


def tabela_generica(linhas, col_widths):
    dados = [
        [Paragraph(str(c), TABELA_HEADER) for c in linhas[0]]
    ] + [
        [Paragraph(str(v), TABELA_CELL) for v in row]
        for row in linhas[1:]
    ]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, CINZA_CLARO]),
        ("BOX",           (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


# ── Conteúdo ──────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # =========================================================================
    # CAPA
    # =========================================================================
    story.append(Spacer(1, 3.5*cm))

    t_capa = Table(
        [[Paragraph("KAIROS DSS", TITULO_CAPA)],
         [Paragraph("Sistema de Apoio a Decisao para Replantio de Cana-de-Acucar", SUBTITULO_CAPA)],
         [Spacer(1, 0.4*cm)],
         [Paragraph("MANUAL COMPLETO DO USUARIO", estilo("CapaManual",
             fontSize=14, textColor=AMARELO, fontName="Helvetica-Bold",
             alignment=TA_CENTER))],
         [Paragraph("Versao 4.0  |  Agricef", estilo("CapaVer",
             fontSize=11, textColor=HexColor("#C8E6C9"), fontName="Helvetica",
             alignment=TA_CENTER))],
        ],
        colWidths=[W - 2*MARGEM],
    )
    t_capa.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), VERDE_ESCURO),
        ("BOX",           (0,0), (-1,-1), 0, colors.white),
        ("TOPPADDING",    (0,0), (-1,-1), 18),
        ("BOTTOMPADDING", (0,0), (-1,-1), 18),
        ("LEFTPADDING",   (0,0), (-1,-1), 30),
        ("RIGHTPADDING",  (0,0), (-1,-1), 30),
    ]))
    story.append(t_capa)
    story.append(Spacer(1, 1.5*cm))

    story.append(Paragraph(
        "Este manual descreve todos os parametros de entrada, telas, calculos e "
        "interpretacoes do sistema Kairos DSS v4.0. Qualquer operador ou tecnico agricola "
        "pode utilizar este documento como referencia completa.",
        estilo("CapaDesc", fontSize=11, textColor=HexColor("#555555"),
               alignment=TA_CENTER, fontName="Helvetica", leading=16)
    ))
    story.append(PageBreak())

    # =========================================================================
    # SUMÁRIO
    # =========================================================================
    story.append(Paragraph("Sumario", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=VERDE_CLARO, spaceAfter=10))

    sumario = [
        ("1.",  "O que e o Kairos DSS v4.0",                       "3"),
        ("2.",  "Como usar o programa — Passo a Passo",             "3"),
        ("3.",  "Arquivos de Entrada",                              "4"),
        ("4.",  "Parametros GIS (Processamento Espacial)",          "5"),
        ("5.",  "Custos por Hora da Maquina",                       "6"),
        ("6.",  "Velocidades e Logistica Operacional",              "8"),
        ("7.",  "Producao Agronomica e Precificacao ATR",           "9"),
        ("8.",  "Riscos",                                           "11"),
        ("9.",  "Gatilho de Reforma",                               "11"),
        ("10.", "Exportacao de Shapefiles",                         "12"),
        ("11.", "Tela: Mapa Interativo",                            "13"),
        ("12.", "Tela: Ranking por Linha",                          "14"),
        ("13.", "Tela: Resumo por Talhao",                          "14"),
        ("14.", "Tela: Detalhamento por Linha",                     "15"),
        ("15.", "Formulas e Calculos Completos",                    "15"),
        ("16.", "Interpretando os Resultados",                      "17"),
        ("17.", "Tabela de Referencia — Valores Recomendados",      "18"),
    ]
    for num, titulo, pag in sumario:
        story.append(Paragraph(
            f'<font color="#2E7D32"><b>{num}</b></font>  {titulo}'
            f'<font color="#9E9E9E">  ....................................  {pag}</font>',
            estilo("SumItem", fontSize=10, fontName="Helvetica",
                   spaceBefore=3, spaceAfter=3, leading=14)
        ))
    story.append(PageBreak())

    # =========================================================================
    # 1. O QUE É O KAIROS DSS v4.0
    # =========================================================================
    story.append(Paragraph("1. O que e o Kairos DSS v4.0", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O <b>Kairos DSS</b> (Decision Support System) e um aplicativo que ajuda o tecnico "
        "agricola a decidir <b>quais linhas de cana-de-acucar devem ser replantadas</b> pelo "
        "Kairos (plantadora automatica da Agricef), levando em conta nao apenas o tamanho das "
        "falhas, mas tambem a <b>viabilidade economica e operacional</b> de cada linha "
        "individualmente.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "O que o sistema faz (v4.0)",
        "1. Le tres arquivos espaciais (shapefiles ZIP): contorno dos talhoes, linhas de plantio "
        "e falhas detectadas por drone.<br/>"
        "2. Recorta e processa as geometrias por talhao, calculando o comprimento e percentual "
        "de falha de cada linha individualmente.<br/>"
        "3. Aplica o modelo economico linha a linha com cinco componentes de tempo: plantio, "
        "deslocamento, manobra, recarga e transferencia entre talhoes.<br/>"
        "4. Calcula o IOI (Indice Operacional Integrado — R$/hora) de cada linha.<br/>"
        "5. Classifica linhas em Viaveis (IOI >= IOI minimo) ou Inviaveis.<br/>"
        "6. Gera recomendacao de Replantio ou Reforma por talhao com base no custo operacional.<br/>"
        "7. Exporta shapefiles com apenas as linhas viaveis para uso no piloto automatico.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "O que e o IOI — Indice Operacional Integrado",
        "O IOI mede quanto a operacao ganha (em R$) por cada hora de trabalho do Kairos:<br/>"
        "<b>IOI = Lucro da Linha / Tempo Total de Operacao (horas)</b><br/><br/>"
        "Um IOI positivo significa que a receita do replantio supera todos os custos. "
        "Um IOI negativo significa prejuizo. O sistema calcula o IOI individualmente para "
        "cada linha e ordena por talhao do maior para o menor.",
        AZUL_ESCURO, AZUL_BG, AZUL_ESCURO
    ))

    # =========================================================================
    # 2. PASSO A PASSO
    # =========================================================================
    story.append(Paragraph("2. Como usar o programa — Passo a Passo", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    passos = [
        ("Passo 1 — Fazer login",
         "Ao abrir o aplicativo, insira seu usuario e senha fornecidos pelo administrador. "
         "O sistema possui cinco usuarios pre-cadastrados."),
        ("Passo 2 — Fazer upload dos 3 arquivos",
         "Na barra lateral esquerda, em <b>Arquivos de Entrada</b>, carregue os tres ZIPs: "
         "Contorno, Linhas e Falhas. Cada ZIP deve conter um shapefile completo "
         "(.shp + .shx + .dbf + .prj)."),
        ("Passo 3 — Configurar os parametros",
         "Ajuste os parametros nas secoes da barra lateral conforme os dados reais da sua "
         "operacao. Os valores padrao sao uma referencia, mas devem ser calibrados para cada "
         "fazenda."),
        ("Passo 4 — Clicar em PROCESSAR",
         "Clique no botao <b>PROCESSAR</b> no final da barra lateral. O sistema fara o "
         "processamento GIS (pode demorar 10 a 60 segundos). Qualquer mudanca nos parametros "
         "GIS (buffer, espaçamento, comprimento minimo) exige novo clique em PROCESSAR."),
        ("Passo 5 — Analisar os resultados",
         "Use as 4 abas para analisar: Mapa (visualizacao espacial), Ranking por Linha "
         "(lista por IOI dentro de cada talhao), Por Talhao (resumo com recomendacao de "
         "reforma) e Linhas (detalhe individual com filtros)."),
        ("Passo 6 — Ajustar parametros economicos",
         "Qualquer mudanca nos parametros economicos (custos, producao, ATR, ciclo/soca, "
         "riscos) recalcula automaticamente o IOI sem reprocessar os arquivos GIS."),
        ("Passo 7 — Exportar",
         "Quando satisfeito com os resultados, clique em <b>Exportar SHPs Viaveis</b>. "
         "Os shapefiles serao gravados na pasta configurada, prontos para o piloto "
         "automatico."),
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
        "O sistema aceita tres camadas espaciais, cada uma comprimida em um arquivo ZIP. "
        "Todos os arquivos devem estar no mesmo Sistema de Referencia de Coordenadas (SRC) "
        "projetado em metros (ex: SIRGAS 2000 / UTM).",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    arqs = [
        ("Contorno dos Talhoes",
         "Poligonos que delimitam cada talhao da fazenda. O sistema usa esta camada para "
         "recortar as linhas e falhas de cada talhao individualmente. Deve ter uma coluna "
         "com o identificador do talhao (padrao: TALHAO)."),
        ("Linhas de Plantio",
         "Linhas (geometrias do tipo LineString) que representam as fileiras de cana. "
         "Cada linha deve estar contida dentro de um talhao. O FID (identificador unico) "
         "e atribuido automaticamente pelo sistema apos o processamento."),
        ("Falhas de Drone",
         "Linhas que representam as falhas de stand (regioes sem plantas) detectadas por "
         "levantamento de drone ou outro metodo. O sistema aplica um buffer configuravel "
         "nestas geometrias antes de cruzar com as linhas de plantio."),
    ]
    for nome, desc in arqs:
        story.append(caixa(f"  {nome}", desc, AZUL_ESCURO, AZUL_BG, AZUL_ESCURO))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Campo identificador do Talhao", H2))
    story.append(Paragraph(
        "Nome da coluna no shapefile de contorno que identifica cada talhao. Valor padrao: "
        "<b>TALHAO</b>. Se sua coluna tem outro nome (ex: ID_TALHAO, NOME, COD), altere "
        "este campo antes de processar.",
        CORPO
    ))
    story.append(caixa(
        "Atencao — Formato do ZIP e CRS",
        "O ZIP deve conter os arquivos do shapefile na raiz (nao dentro de subpastas). "
        "Arquivos necessarios: arquivo.shp, arquivo.shx, arquivo.dbf, arquivo.prj. "
        "O arquivo .prj e obrigatorio. O CRS deve ser projetado em metros (UTM) — "
        "CRS geografico (graus) sera rejeitado com mensagem de erro.",
        AMARELO, AMARELO_BG, LARANJA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 4. PARÂMETROS GIS
    # =========================================================================
    story.append(Paragraph("4. Parametros GIS (Processamento Espacial)", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Estes parametros controlam como o sistema processa as geometrias espaciais. "
        "Uma mudanca aqui exige novo clique em PROCESSAR.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Buffer nas falhas (m)", "0,30 m",
         "Margem aplicada ao redor de cada falha antes de cruzar com as linhas. "
         "Garante que falhas muito finas sejam capturadas. "
         "<b>Recomendado: 0,20 a 0,50 m.</b>"),
        ("Comprimento minimo de falha (m)", "1,50 m",
         "Segmento de falha menor que este valor e ignorado. Evita micro-falhas "
         "sem relevancia agronomica. <b>Recomendado: 1,0 a 2,0 m.</b>"),
        ("Espacamento entre linhas (m)", "1,50 m",
         "Distancia entre duas linhas de plantio adjacentes. Usado para calcular a area "
         "de falha em hectares: <b>Area (ha) = Comprimento Falha (m) x Espacamento (m) / 10.000.</b> "
         "Verifique o espacamento real do talhao."),
    ]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Como o processamento GIS funciona por talhao", H2))
    etapas_gis = [
        "Recorta as linhas de plantio e falhas dentro do poligono do talhao.",
        "Atribui FID sequencial apos o recorte (evita duplicatas do clip).",
        "Recalcula comp_linha com a geometria recortada (comprimento real no talhao).",
        "Aplica o buffer configurado ao redor das falhas, transformando-as em poligonos.",
        "Intersecta as linhas de plantio com os poligonos de falha.",
        "Explode MultiLineStrings em segmentos individuais e filtra > comprimento minimo.",
        "Soma os comprimentos de falha por linha (soma_falhas) e calcula o percentual.",
        "Classifica cada linha em uma das 11 categorias de percentual de falha.",
    ]
    for i, e in enumerate(etapas_gis, 1):
        story.append(Paragraph(f"<b>{i}.</b> {e}", BULLET))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Classificacao das linhas por percentual de falha", H2))
    story.append(Spacer(1, 0.2*cm))

    classes = [
        ["Classe", "% de Falha", "Interpretacao", "Cor no Mapa"],
        ["0-2",   "0 a 2%",       "Stand praticamente completo", "Verde escuro"],
        ["2-4",   "2 a 4%",       "Falha muito baixa — analisar caso a caso", "Verde medio"],
        ["4-6",   "4 a 6%",       "Falha leve", "Verde claro"],
        ["6-8",   "6 a 8%",       "Falha moderada — inicio da zona de atencao", "Amarelo-verde"],
        ["8-10",  "8 a 10%",      "Falha moderada", "Amarelo"],
        ["10-12", "10 a 12%",     "Falha significativa — replantio recomendado", "Laranja claro"],
        ["12-14", "12 a 14%",     "Falha alta", "Laranja"],
        ["14-16", "14 a 16%",     "Falha muito alta", "Vermelho medio"],
        ["16-18", "16 a 18%",     "Falha critica", "Vermelho escuro"],
        ["18-20", "18 a 20%",     "Falha critica severa", "Bordo"],
        [">20",   "Acima de 20%", "Falha extrema — prioritario para replantio", "Quase preto"],
    ]
    col_cls = [1.5*cm, 2.2*cm, 8.5*cm, 3.5*cm]
    cores_cls = [
        "#1a9850","#66bd63","#a6d96a","#d9ef8b","#fee08b",
        "#fdae61","#f46d43","#d73027","#a50026","#7f0000","#4d0000"
    ]
    dados_cls = (
        [[Paragraph(c, TABELA_HEADER) for c in classes[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in classes[1:]]
    )
    t_cls = Table(dados_cls, colWidths=col_cls, repeatRows=1)
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
    for i, cor in enumerate(cores_cls):
        cls_style.append(("BACKGROUND", (0, i+1), (0, i+1), HexColor(cor)))
        cls_style.append(("TEXTCOLOR",  (0, i+1), (0, i+1), colors.white))
    t_cls.setStyle(TableStyle(cls_style))
    story.append(t_cls)

    story.append(PageBreak())

    # =========================================================================
    # 5. CUSTOS POR HORA
    # =========================================================================
    story.append(Paragraph("5. Custos por Hora da Maquina", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O custo por hora e calculado somando quatro componentes: diesel, mao de obra, "
        "manutencao e depreciacao. Este valor escalara o custo de maquina por linha "
        "conforme o tempo total de operacao.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Formula do Custo por Hora:", H2))
    story.append(Paragraph(
        "custo_hora = (diesel_lh x preco_diesel)<br/>"
        "           + (salario_operador + n_auxiliares x salario_auxiliar) / horas_mes<br/>"
        "           + manutencao_mensal / horas_mes<br/>"
        "           + (depreciacao_anual / 12) / horas_mes",
        FORMULA
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Consumo diesel (L/h)", "8,0 L/h",
         "Litros de diesel consumidos por hora de operacao. Consulte o manual da maquina "
         "ou meca em campo. <b>Recomendado: 6 a 12 L/h.</b>"),
        ("Preco do diesel (R$/L)", "R$ 6,50",
         "Preco medio pago pelo litro de diesel na fazenda. Atualize conforme o preco atual."),
        ("Salario do operador (R$/mes)", "R$ 3.500",
         "Salario bruto mensal do operador incluindo encargos sociais (INSS, FGTS). "
         "<b>Inclua os encargos</b> — o custo real para a empresa e aproximadamente "
         "1,7x o salario liquido."),
        ("Numero de auxiliares", "1",
         "Quantidade de auxiliares de campo que acompanham a operacao. Use 0 se a "
         "operacao for apenas com o operador."),
        ("Salario por auxiliar (R$/mes)", "R$ 2.500",
         "Salario bruto mensal de cada auxiliar, incluindo encargos."),
        ("Manutencao fixa mensal (R$/mes)", "R$ 800",
         "Custo medio mensal com manutencao preventiva e corretiva da maquina. "
         "<b>Recomendado: R$ 500 a R$ 2.000/mes.</b>"),
        ("Depreciacao anual (R$/ano)", "R$ 36.000",
         "Quanto a maquina perde de valor por ano: "
         "<b>(Valor de compra - Valor residual) / Vida util em anos.</b> "
         "Ex: maquina de R$ 400.000, residual R$ 40.000, vida util 10 anos = R$ 36.000/ano."),
        ("Horas trabalhadas por mes (h/mes)", "176 h",
         "Total de horas que a maquina opera por mes. "
         "Padrao: 22 dias x 8 horas = 176 h."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Exemplo de calculo — Custo por hora",
        "Diesel: 8 L/h x R$ 6,50 = R$ 52,00/h<br/>"
        "Mao de obra: (R$ 3.500 + 1 x R$ 2.500) / 176 h = R$ 34,09/h<br/>"
        "Manutencao: R$ 800 / 176 h = R$ 4,55/h<br/>"
        "Depreciacao: (R$ 36.000 / 12) / 176 h = R$ 17,05/h<br/>"
        "<b>TOTAL: R$ 107,69/hora</b>",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 6. VELOCIDADES E LOGÍSTICA OPERACIONAL
    # =========================================================================
    story.append(Paragraph("6. Velocidades e Logistica Operacional", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O modelo v4.0 usa <b>cinco componentes de tempo</b> por linha, substituindo o "
        "modelo anterior de dois componentes. Isso permite representar com maior fidelidade "
        "o tempo real consumido em campo.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Velocidades de Operacao", H2))
    story.append(tabela_params([
        ("Velocidade de plantio (km/h)", "2,0 km/h",
         "Velocidade real da maquina durante o plantio dentro da linha de falha. "
         "<b>Recomendado: 1,5 a 3,0 km/h.</b> Meca em campo com GPS ou cronometro."),
        ("Velocidade de deslocamento (km/h)", "5,0 km/h",
         "Velocidade da maquina ao percorrer as partes saudaveis da linha (sem plantar). "
         "<b>Recomendado: 4,0 a 8,0 km/h.</b> Sempre maior que a velocidade de plantio."),
        ("Tempo de manobra por linha (min)", "2,0 min",
         "Tempo gasto para posicionar a maquina no inicio de cada nova linha: "
         "curva de retorno, alinhamento, acionamento do sistema. "
         "<b>Recomendado: 1,5 a 4 min/linha.</b> Meca cronometrando 10 manobras."),
    ]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Logistica Operacional", H2))
    story.append(tabela_params([
        ("Capacidade de carga (m de falha)", "400 m",
         "Comprimento maximo de falha que pode ser plantado antes de precisar recarregar "
         "a muda. Quando a soma de falhas plantadas atinge este limite, a maquina para "
         "para reabastecimento. <b>Recomendado: 200 a 800 m</b> dependendo do tanque/carro."),
        ("Tempo de recarga (min)", "20 min",
         "Tempo necessario para recarregar a muda no campo. Este tempo e amortizado "
         "proporcionalmente ao comprimento de falha de cada linha. "
         "<b>Recomendado: 15 a 40 min.</b>"),
        ("Tempo de transferencia entre talhoes (min)", "30 min",
         "Tempo total para deslocar a maquina de um talhao para o proximo "
         "(deslocamento + posicionamento). Este custo e dividido igualmente entre todas "
         "as linhas do talhao. <b>Recomendado: 15 a 60 min.</b>"),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Os cinco componentes de tempo por linha", H2))
    story.append(Paragraph(
        "comp_saudavel = comp_linha - soma_falhas  (parte sem falha)",
        FORMULA
    ))
    story.append(Paragraph(
        "1. tempo_plantio_min    = soma_falhas / velocidade_plantio_mmin",
        FORMULA
    ))
    story.append(Paragraph(
        "2. tempo_desloc_min     = comp_saudavel / velocidade_desloc_mmin",
        FORMULA
    ))
    story.append(Paragraph(
        "3. tempo_manobra_min    = tempo_manobra_fixo_min  (fixo por linha)",
        FORMULA
    ))
    story.append(Paragraph(
        "4. tempo_recarga_min    = (soma_falhas / capacidade_carga_m) x tempo_recarga_min",
        FORMULA
    ))
    story.append(Paragraph(
        "5. tempo_transfer_min   = tempo_transferencia_talhao_min / n_linhas_do_talhao",
        FORMULA
    ))
    story.append(Paragraph(
        "tempo_total_min = (1) + (2) + (3) + (4) + (5)",
        FORMULA
    ))
    story.append(Paragraph(
        "eficiencia_pct  = tempo_plantio_min / tempo_total_min x 100",
        FORMULA
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Interpretando a Eficiencia (%)",
        "<b>Eficiencia alta (60-85%):</b> Linha com falha longa — maquina passa a maior parte "
        "do tempo plantando. Ideal.<br/>"
        "<b>Eficiencia media (30-60%):</b> Falha moderada, parte do tempo em deslocamento. "
        "Aceitavel.<br/>"
        "<b>Eficiencia baixa (&lt;30%):</b> Linha com pouca falha. Custo de deslocamento, "
        "manobra e transferencia dominam — pode ser inviavel.",
        AZUL_ESCURO, AZUL_BG, AZUL_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 7. PRODUÇÃO AGRONÔMICA E PRECIFICAÇÃO ATR
    # =========================================================================
    story.append(Paragraph("7. Producao Agronomica e Precificacao ATR", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O modelo v4.0 usa precificacao baseada em ATR (Acucar Total Recuperavel) e "
        "aplica um fator de reducao por ciclo de soca, tornando a estimativa de receita "
        "mais precisa e alinhada com a pratica da usina.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Precificacao por ATR", H2))
    story.append(tabela_params([
        ("ATR medio (kg ATR/ton cana)", "130 kg/ton",
         "Quantidade media de acucar recuperavel por tonelada de cana do talhao. "
         "Obtenha na balanca da usina. "
         "<b>Recomendado: 110 a 155 kg ATR/ton</b> dependendo da variedade e epoca."),
        ("Preco do ATR (R$/kg ATR)", "R$ 1,10",
         "Preco vigente pago pela usina por kg de ATR. Consulte o boletim mensal "
         "da usina ou o CONSECANA. "
         "<b>Recomendado: R$ 0,90 a R$ 1,40/kg ATR.</b>"),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "preco_efetivo_ton (R$/ton) = atr_medio_kgton x preco_atr_rs_kg",
        FORMULA
    ))
    story.append(caixa(
        "Exemplo: ATR 135 kg/ton, preco R$ 1,12/kg ATR",
        "Preco efetivo = 135 x R$ 1,12 = <b>R$ 151,20/ton</b><br/>"
        "Este valor substitui o antigo campo 'Preco da tonelada (R$/t)'.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Ciclo de Soca (Fator de Reducao de Producao)", H2))
    story.append(Paragraph(
        "A produtividade da cana diminui a cada ciclo de corte. O sistema aplica um "
        "multiplicador sobre o ganho esperado conforme o ciclo informado:",
        CORPO
    ))

    soca_tab = [
        ["Ciclo",         "Fator de Reducao", "Ganho Ajustado (ex: 60 t/ha esperado)"],
        ["Cana-planta",   "1,00 (sem reducao)", "60,0 t/ha"],
        ["Soca 1",        "0,90 (-10%)",         "54,0 t/ha"],
        ["Soca 2",        "0,80 (-20%)",         "48,0 t/ha"],
        ["Soca 3",        "0,70 (-30%)",         "42,0 t/ha"],
        ["Soca 4+",       "0,65 (-35%)",         "39,0 t/ha"],
    ]
    story.append(tabela_generica(soca_tab, [3.5*cm, 4.0*cm, 9.2*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Outros Parametros de Producao", H2))
    story.append(tabela_params([
        ("Ganho esperado por replantio (t/ha)", "60,0 t/ha",
         "Toneladas de cana colhidas por hectare de AREA DE FALHA replantada "
         "(NAO e a produtividade do talhao inteiro — e o ganho incremental). "
         "O sistema aplica o fator de soca automaticamente. "
         "<b>Recomendado: 40 a 80 t/ha</b> antes do fator de soca."),
        ("Taxa de pegamento / germinacao (%)", "85%",
         "Percentual das mudas replantadas que efetivamente brotam. "
         "<b>Recomendado: 70 a 90%.</b>"),
        ("Custo de muda (R$/ha de falha)", "R$ 400,00",
         "Custo do material de plantio (muda, tolete ou colmo) por hectare replantado. "
         "Inclua colheita e preparo da muda."),
        ("Custo de logistica de muda (R$/ha)", "R$ 50,00",
         "Custo de frete e manuseio da muda até o campo. "
         "Soma ao custo de muda para formar o custo total de insumos. "
         "<b>Recomendado: R$ 0 a R$ 200/ha</b> dependendo da distancia do viveiro."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Como a receita e calculada por linha", H2))
    story.append(Paragraph(
        "ganho_ajustado = ganho_esperado_tha x fator_soca",
        FORMULA
    ))
    story.append(Paragraph(
        "area_falha_ha = soma_falhas x espacamento / 10.000",
        FORMULA
    ))
    story.append(Paragraph(
        "receita_bruta = area_falha_ha x ganho_ajustado x (taxa_pegamento/100) x preco_efetivo_ton",
        FORMULA
    ))
    story.append(Paragraph(
        "receita_liquida = receita_bruta x (1 - risco_climatico/100)",
        FORMULA
    ))
    story.append(Paragraph(
        "custo_insumos = area_falha_ha x (custo_muda_tha + custo_logistica_muda_ha)",
        FORMULA
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(caixa(
        "Exemplo numerico de receita por linha",
        "Linha com 50 m de falha, espacamento 1,5 m, Soca 2, ATR 130 kg/ton, preco R$1,10/kg:<br/>"
        "Preco efetivo: 130 x 1,10 = R$ 143,00/ton<br/>"
        "Ganho ajustado: 60 t/ha x 0,80 (Soca 2) = 48 t/ha<br/>"
        "Area: 50 x 1,5 / 10.000 = 0,0075 ha<br/>"
        "Receita Bruta: 0,0075 x 48 x 0,85 x R$143,00 = <b>R$ 43,61</b><br/>"
        "Receita Liquida (10% risco): R$43,61 x 0,90 = <b>R$ 39,25</b>",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 8. RISCOS
    # =========================================================================
    story.append(Paragraph("8. Riscos", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(tabela_params([
        ("Desconto de risco climatico (%)", "10%",
         "Reducao percentual na receita para considerar a possibilidade de janela "
         "climatica desfavoravel (seca, geada, excesso de chuva). "
         "<b>Recomendado: 5 a 20%.</b> Regioes com distribuicao irregular de chuvas = "
         "maior desconto."),
        ("IOI minimo para viabilidade (R$/h)", "0 R$/h",
         "Limiar de IOI abaixo do qual a linha e considerada inviavel. O padrao 0 "
         "considera viavel qualquer linha com lucro positivo. Aumente este valor para "
         "ser mais seletivo e exigir uma margem minima de retorno por hora."),
    ]))

    # =========================================================================
    # 9. GATILHO DE REFORMA
    # =========================================================================
    story.append(Paragraph("9. Gatilho de Reforma", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O sistema v4.0 usa uma comparacao de custos para recomendar reforma de talhao: "
        "quando o custo operacional do replantio se aproxima do custo de reforma, "
        "pode ser mais economico reformar o talhao inteiro.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(tabela_params([
        ("Custo de reforma do canavial (R$/ha)", "R$ 14.000",
         "Custo total estimado para reformar um talhao: preparo de solo, muda, plantio "
         "mecanizado e tratos culturais iniciais. "
         "<b>Recomendado: R$ 10.000 a R$ 20.000/ha</b> dependendo da regiao e insumos."),
        ("Limite para sugerir reforma (%)", "80%",
         "Percentual do custo de reforma que, quando atingido pelo custo operacional de "
         "replantio, dispara a recomendacao de reforma. "
         "<b>Padrao: 80%</b> — se o custo de replantio supera 80% do custo de reforma, "
         "reform e financeiramente mais eficiente."),
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Logica da recomendacao", H2))
    story.append(Paragraph(
        "custo_reforma_talhao = area_ha_talhao x custo_reforma_ha",
        FORMULA
    ))
    story.append(Paragraph(
        "limite_reforma = custo_reforma_talhao x (limite_pct / 100)",
        FORMULA
    ))
    story.append(Paragraph(
        "custo_op_talhao = soma(custo_maquina) de todas as linhas do talhao",
        FORMULA
    ))
    story.append(Paragraph(
        "SE custo_op_talhao >= limite_reforma  →  SUGERIR REFORMA",
        FORMULA
    ))
    story.append(Paragraph(
        "SE custo_op_talhao <  limite_reforma  →  REPLANTIO",
        FORMULA
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(caixa(
        "Exemplo de gatilho de reforma",
        "Talhao com 10 ha, custo de reforma R$ 14.000/ha, limite 80%:<br/>"
        "Custo de reforma: 10 x R$ 14.000 = R$ 140.000<br/>"
        "Limite: R$ 140.000 x 80% = R$ 112.000<br/>"
        "Se o custo operacional total das linhas superar R$ 112.000 → SUGERIR REFORMA.<br/>"
        "A recomendacao aparece na aba <b>Por Talhao</b> do dashboard.",
        LARANJA, LARANJA_BG, LARANJA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 10. EXPORTAÇÃO
    # =========================================================================
    story.append(Paragraph("10. Exportacao de Shapefiles", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(tabela_params([
        ("Pasta de saida dos SHPs", "C:\\kairos_saida",
         "Caminho completo da pasta onde os shapefiles serao gravados. "
         "A pasta e criada automaticamente se nao existir."),
    ]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("O que e exportado", H2))
    story.append(Paragraph(
        "Sao exportadas somente as linhas com <b>IOI &gt;= IOI minimo</b> (viaveis). "
        "Um arquivo .shp separado e gerado para cada talhao, nomeado como "
        "<b>talhao_NOME.shp</b>. Cada arquivo contem as seguintes colunas:",
        CORPO
    ))
    colunas_exp = [
        ["Coluna", "Descricao"],
        ["TALHAO",       "Identificador do talhao"],
        ["FID",          "Identificador unico da linha dentro do talhao"],
        ["comp_linha",   "Comprimento total da linha dentro do talhao (metros)"],
        ["soma_falhas",  "Comprimento total das falhas na linha (metros)"],
        ["perc_falhas",  "Percentual de falha da linha (%)"],
        ["classe",       "Classe de falha (ex: 8-10, >20)"],
        ["ioi",          "IOI da linha (R$/hora) — indicador principal"],
        ["eficiencia_pct","Eficiencia operacional da linha (%)"],
        ["lucro",        "Lucro estimado da linha (R$)"],
        ["geometry",     "Geometria da linha (LineString) — para uso no QGIS/piloto automatico"],
    ]
    story.append(tabela_generica(colunas_exp, [3.5*cm, 13.2*cm]))

    story.append(PageBreak())

    # =========================================================================
    # 11. MAPA
    # =========================================================================
    story.append(Paragraph("11. Tela: Mapa Interativo", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "O mapa exibe duas camadas sobrepostas que podem ser ligadas e desligadas "
        "usando o controle de camadas no canto superior direito.",
        CORPO
    ))
    story.append(Spacer(1, 0.2*cm))

    camadas = [
        ("Camada 1: Todas as linhas (% Falha)",
         "Mostra TODAS as linhas coloridas pela classe de percentual de falha "
         "(escala verde para preto). Use para visualizar a distribuicao espacial "
         "das falhas no campo. Tooltip: Talhao, FID, Comprimento, % Falha, Classe."),
        ("Camada 2: Linhas viaveis",
         "Mostra apenas as linhas com IOI >= IOI minimo, coloridas pela classe de falha. "
         "Use para ver exatamente quais linhas o Kairos deve operar. "
         "Tooltip: Talhao, FID, % Falha, Classe, IOI (R$/h), Lucro (R$), Viavel."),
    ]
    for titulo, desc in camadas:
        story.append(caixa(titulo, desc, AZUL_ESCURO, AZUL_BG, AZUL_ESCURO))
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.2*cm))
    story.append(caixa(
        "Legenda no canto do mapa",
        "A legenda fixa no canto inferior direito do mapa mostra as 11 cores e seus "
        "respectivos percentuais de falha.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(PageBreak())

    # =========================================================================
    # 12. RANKING POR LINHA
    # =========================================================================
    story.append(Paragraph("12. Tela: Ranking por Linha", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Tabela com todas as linhas, ordenadas por IOI decrescente <b>dentro de cada talhao</b> "
        "(ranking local, nao global). Linhas viaveis aparecem em verde; inviaveis em vermelho. "
        "O ranking reseta para 1 a cada novo talhao, refletindo a ordem real de prioridade de "
        "campo por area de operacao.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    colunas_rank = [
        ["Coluna", "O que significa"],
        ["Ranking",        "Posicao no talhao (1 = maior IOI, mais rentavel naquele talhao)"],
        ["Talhao",         "Identificador do talhao"],
        ["FID",            "Identificador unico da linha"],
        ["Comprimento (m)","Comprimento total da linha no talhao"],
        ["Falhas (m)",     "Comprimento total das falhas na linha"],
        ["Area falha (ha)","Falhas (m) x Espacamento / 10.000"],
        ["% Falha",        "Percentual de falha da linha"],
        ["Classe",         "Categoria de falha (0-2, 2-4, ..., >20)"],
        ["T. Plantio (min)","Tempo efetivo de plantio"],
        ["T. Desloc (min)", "Tempo de deslocamento nas partes saudaveis"],
        ["T. Manobra (min)","Tempo fixo de manobra por linha"],
        ["T. Recarga (min)","Tempo proporcional de recarga de muda"],
        ["T. Transfer (min)","Tempo de transferencia entre talhoes amortizado"],
        ["T. Total (min)",  "Soma dos cinco componentes de tempo"],
        ["Eficiencia (%)",  "T. Plantio / T. Total x 100"],
        ["Receita Liq. (R$)","Receita apos pegamento e risco climatico"],
        ["Custo Maquina (R$)","custo_hora x (T. Total / 60)"],
        ["Custo Insumos (R$)","area_falha_ha x (custo_muda + custo_logistica)"],
        ["Lucro (R$)",      "Receita Liquida - Custo Total"],
        ["IOI (R$/h)",      "Lucro / (T. Total / 60) — indicador principal"],
        ["Viavel",          "SIM se IOI >= IOI minimo  |  NAO caso contrario"],
    ]
    story.append(tabela_generica(colunas_rank, [4.0*cm, 12.7*cm]))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Limite de exibicao: a tabela mostra ate 2.000 linhas para garantir performance "
        "do navegador. Datasets maiores sao truncados com aviso.",
        NOTA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 13. POR TALHÃO
    # =========================================================================
    story.append(Paragraph("13. Tela: Resumo por Talhao", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Visao agregada por talhao com recomendacao automatica de Replantio ou Reforma. "
        "Util para priorizar em qual talhao comecar a operacao e identificar talhoes "
        "candidatos a reforma.",
        CORPO
    ))
    story.append(Spacer(1, 0.2*cm))
    colunas_t = [
        ["Coluna", "O que significa"],
        ["Talhao",              "Identificador do talhao"],
        ["Area (ha)",           "Area total do talhao calculada pela geometria do contorno"],
        ["Total Linhas",        "Total de linhas com falha no talhao"],
        ["Linhas Viaveis",      "Quantidade de linhas com IOI >= IOI minimo"],
        ["% Viaveis",           "Percentual de linhas viaveis no talhao"],
        ["% Medio Falha",       "Media do percentual de falha de todas as linhas do talhao"],
        ["Area Falhas (ha)",    "Soma da area de falha (soma_falhas x espacamento / 10.000) de todas as linhas"],
        ["Custo Operacao (R$)", "Soma do custo de maquina de todas as linhas do talhao"],
        ["Lucro Estimado (R$)", "Soma do lucro das linhas viaveis do talhao"],
        ["Recomendacao",        "REPLANTIO ou SUGERIR REFORMA (baseado no gatilho de custo)"],
    ]
    story.append(tabela_generica(colunas_t, [4.2*cm, 12.5*cm]))

    story.append(Spacer(1, 0.5*cm))

    # =========================================================================
    # 14. LINHAS
    # =========================================================================
    story.append(Paragraph("14. Tela: Detalhamento por Linha", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Tabela com uma linha por linha de plantio, com os seguintes filtros:",
        CORPO
    ))
    story.append(Paragraph(
        "<b>Filtrar por talhao:</b> Seleciona um talhao especifico ou mostra todos.", BULLET))
    story.append(Paragraph(
        "<b>Apenas viaveis:</b> Quando marcado, mostra somente as linhas que serao exportadas "
        "(IOI >= IOI minimo). Esta e a visualizacao mais direta do que o Kairos vai plantar.", BULLET))
    story.append(Paragraph(
        "As colunas exibidas incluem todos os cinco componentes de tempo, receita, custos, "
        "lucro, IOI e ranking por talhao.", CORPO))

    story.append(PageBreak())

    # =========================================================================
    # 15. FÓRMULAS COMPLETAS
    # =========================================================================
    story.append(Paragraph("15. Formulas e Calculos Completos", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph("15.1 Metricas Espaciais (por linha)", H2))
    formulas1 = [
        ("comp_linha (m)",    "Comprimento da linha apos recorte no talhao (geometria real)."),
        ("soma_falhas (m)",   "Soma dos segmentos de falha intersectados na linha."),
        ("perc_falhas (%)",   "soma_falhas / comp_linha x 100"),
        ("classe",            "Bin de perc_falhas: 0-2, 2-4, 4-6, 6-8, 8-10, 10-12, 12-14, 14-16, 16-18, 18-20, >20"),
        ("area_falha_ha (ha)","soma_falhas x espacamento / 10.000"),
    ]
    for nome, desc in formulas1:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.2 Custo por Hora (escalar — igual para todas as linhas)", H2))
    story.append(Paragraph(
        "custo_hora = (diesel_lh x preco_diesel)<br/>"
        "           + (salario_op + n_aux x salario_aux) / horas_mes<br/>"
        "           + manutencao_mensal / horas_mes<br/>"
        "           + (depreciacao_anual / 12) / horas_mes",
        FORMULA
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.3 Cinco Componentes de Tempo (por linha)", H2))
    formulas_tempo = [
        ("vmpm_p (m/min)",         "velocidade_plantio_kmh x 1000 / 60"),
        ("vmpm_d (m/min)",         "velocidade_desloc_kmh x 1000 / 60"),
        ("comp_saudavel (m)",       "comp_linha - soma_falhas  (clipado em >= 0)"),
        ("tempo_plantio_min",       "soma_falhas / vmpm_p"),
        ("tempo_desloc_min",        "comp_saudavel / vmpm_d"),
        ("tempo_manobra_min",       "tempo_manobra_fixo_min  (constante por linha)"),
        ("tempo_recarga_min",       "(soma_falhas / capacidade_carga_m) x tempo_recarga_min"),
        ("tempo_transfer_min",      "tempo_transferencia_talhao_min / n_linhas_do_talhao"),
        ("tempo_total_min",         "soma dos cinco componentes acima"),
        ("eficiencia_pct (%)",      "tempo_plantio_min / tempo_total_min x 100"),
    ]
    for nome, desc in formulas_tempo:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.4 Modelo Economico (por linha)", H2))
    formulas_eco = [
        ("preco_efetivo_ton (R$/ton)", "atr_medio_kgton x preco_atr_rs_kg"),
        ("fator_soca",                 "1,00 / 0,90 / 0,80 / 0,70 / 0,65 conforme ciclo"),
        ("ganho_ajustado (t/ha)",      "ganho_esperado_tha x fator_soca"),
        ("receita_bruta (R$)",         "area_falha_ha x ganho_ajustado x (taxa_pegamento/100) x preco_efetivo_ton"),
        ("receita_liquida (R$)",       "receita_bruta x (1 - risco_climatico/100)"),
        ("custo_maquina (R$)",         "custo_hora x (tempo_total_min / 60)"),
        ("custo_insumos (R$)",         "area_falha_ha x (custo_muda_tha + custo_logistica_muda_ha)"),
        ("custo_total (R$)",           "custo_maquina + custo_insumos"),
        ("lucro (R$)",                 "receita_liquida - custo_total"),
        ("ioi (R$/h)",                 "lucro / (tempo_total_min / 60)  [ou -inf se tempo = 0]"),
        ("viavel",                     "TRUE se ioi >= ioi_minimo"),
        ("ranking",                    "rank de ioi decrescente DENTRO do talhao (rank 1 = maior IOI local)"),
    ]
    for nome, desc in formulas_eco:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.5 Metricas do Dashboard Principal", H2))
    formulas_dash = [
        ("Area Total de Falhas (ha)",    "soma(area_falha_ha) de todas as linhas viaveis"),
        ("Rendimento de Plantio (ha/h)", "Area Total de Falhas / soma(tempo_total_min/60) das linhas viaveis"),
        ("Rendimento Minimo (ha/h)",     "custo_hora / (receita_liq_por_ha - custo_insumos_por_ha)"),
        ("Lucro Total (R$)",             "soma(lucro) de todas as linhas viaveis"),
    ]
    for nome, desc in formulas_dash:
        story.append(Paragraph(f"<b>{nome}:</b>  {desc}", FORMULA))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "O Rendimento Minimo indica quantos ha/h a operacao precisa atingir para cobrir "
        "os custos. Se o Rendimento de Plantio for menor que o Rendimento Minimo, "
        "a operacao global pode ter margem negativa.",
        NOTA
    ))

    story.append(PageBreak())

    # =========================================================================
    # 16. INTERPRETANDO RESULTADOS
    # =========================================================================
    story.append(Paragraph("16. Interpretando os Resultados", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph("O que fazer quando MUITAS linhas sao viaveis", H2))
    story.append(caixa(
        "Sintoma: quase todas as linhas tem IOI positivo",
        "Causa provavel: parametros de producao superestimados (ganho muito alto, ATR muito alto, "
        "taxa de pegamento muito alta) ou custos subestimados.<br/><br/>"
        "Solucao: reduza o <b>Ganho esperado</b> para 40 t/ha, verifique o ATR e preco reais, "
        "aumente o risco climatico para valores mais conservadores. "
        "O objetivo e que apenas linhas com falha significativa sejam viaveis.",
        LARANJA, LARANJA_BG, LARANJA
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("O que fazer quando NENHUMA linha e viavel", H2))
    story.append(caixa(
        "Sintoma: zero linhas viaveis",
        "Causa provavel: custo por hora muito alto, velocidade de plantio muito baixa, "
        "ou a operacao realmente nao se paga.<br/><br/>"
        "Solucao: verifique o custo por hora no expander da tela principal, confirme as "
        "velocidades de plantio e deslocamento, reduza o IOI minimo para 0. "
        "Se mesmo com parametros realistas nao houver linhas viaveis, a operacao nao e "
        "economicamente recomendada para este talhao.",
        VERMELHO, HexColor("#FFEBEE"), VERMELHO
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("IOI: como interpretar os valores", H2))
    ioi_tab = [
        ["IOI (R$/h)",  "Interpretacao",                                     "Recomendacao"],
        ["< 0",         "Prejuizo — custo supera receita",                   "Nao operar"],
        ["0 a 50",      "Margem muito estreita — alto risco",                "Analisar com cautela"],
        ["50 a 150",    "Viavel com margem moderada",                        "Operar se logistica permitir"],
        ["150 a 300",   "Boa viabilidade",                                   "Prioridade normal"],
        ["300 a 500",   "Alta viabilidade — linha eficiente",                "Alta prioridade"],
        ["> 500",       "Excelente — linha longa com falha alta",            "Prioridade maxima"],
    ]
    t_ioi = Table(
        [[Paragraph(c, TABELA_HEADER) for c in ioi_tab[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in ioi_tab[1:]],
        colWidths=[2.8*cm, 7.5*cm, 6.4*cm], repeatRows=1
    )
    cores_ioi = [VERMELHO, HexColor("#FF8F00"), AMARELO, VERDE_CLARO, VERDE_MEDIO, VERDE_ESCURO]
    ioi_style = [
        ("BACKGROUND",    (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, CINZA_CLARO]),
        ("BOX",           (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
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
    story.append(Paragraph("17. Tabela de Referencia — Valores Recomendados", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    story.append(Paragraph(
        "Use esta tabela como ponto de partida. Sempre que possivel, substitua pelos "
        "valores reais medidos na sua operacao.",
        CORPO
    ))
    story.append(Spacer(1, 0.3*cm))

    ref = [
        ["Parametro",                      "Minimo",   "Padrao",  "Maximo",   "Como obter"],
        ["Buffer falhas (m)",               "0,10",     "0,30",    "0,60",     "Tecnico GIS"],
        ["Min. falha (m)",                  "0,50",     "1,50",    "3,00",     "Agronomico"],
        ["Espacamento linhas (m)",          "0,80",     "1,50",    "1,80",     "Medir no campo"],
        ["Diesel (L/h)",                    "4",        "8",       "14",       "Manual da maquina"],
        ["Preco diesel (R$/L)",             "5,00",     "6,50",    "8,00",     "NF de compra"],
        ["Salario operador (R$/mes)",       "2.500",    "3.500",   "6.000",    "RH da empresa"],
        ["Manutencao (R$/mes)",             "300",      "800",     "2.500",    "Historico oficina"],
        ["Depreciacao (R$/ano)",            "15.000",   "36.000",  "80.000",   "Contabilidade"],
        ["Horas/mes",                       "120",      "176",     "220",      "Registro de campo"],
        ["Vel. plantio (km/h)",             "1,0",      "2,0",     "3,5",      "GPS ou cronometro"],
        ["Vel. deslocamento (km/h)",        "3,0",      "5,0",     "8,0",      "GPS ou cronometro"],
        ["Tempo manobra (min)",             "1,0",      "2,0",     "5,0",      "Cronometrar 10x"],
        ["Capacidade de carga (m)",         "150",      "400",     "1000",     "Especificacao maquina"],
        ["Tempo de recarga (min)",          "10",       "20",      "45",       "Cronometrar em campo"],
        ["Tempo transferencia (min)",       "10",       "30",      "90",       "Medir deslocamento"],
        ["ATR medio (kg ATR/ton)",          "100",      "130",     "158",      "Balanca da usina"],
        ["Preco ATR (R$/kg ATR)",           "0,80",     "1,10",    "1,40",     "CONSECANA/usina"],
        ["Ganho esperado (t/ha)",           "20",       "60",      "90",       "Historico replantio"],
        ["Taxa pegamento (%)",              "60",       "85",      "95",       "Experimento campo"],
        ["Custo muda (R$/ha)",              "150",      "400",     "900",      "Viveiro/colheita"],
        ["Custo logistica muda (R$/ha)",    "0",        "50",      "200",      "Frete/distancia"],
        ["Risco climatico (%)",             "0",        "10",      "25",       "Historico climatico"],
        ["IOI minimo (R$/h)",               "0",        "0",       "200",      "Politica da empresa"],
        ["Custo reforma (R$/ha)",           "8.000",    "14.000",  "22.000",   "Orcamento agronomico"],
        ["Limite reforma (%)",              "50",       "80",      "100",      "Gestao financeira"],
    ]
    col_ref = [5.2*cm, 1.7*cm, 1.7*cm, 1.7*cm, 6.4*cm]
    t_ref = Table(
        [[Paragraph(c, TABELA_HEADER) for c in ref[0]]] +
        [[Paragraph(str(v), TABELA_CELL) for v in row] for row in ref[1:]],
        colWidths=col_ref, repeatRows=1
    )
    t_ref.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  VERDE_ESCURO),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, CINZA_CLARO]),
        ("BOX",           (0,0), (-1,-1), 0.5, CINZA_MEDIO),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, CINZA_MEDIO),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("BACKGROUND",    (1,0), (3,0),   AZUL_ESCURO),
    ]))
    story.append(t_ref)

    story.append(Spacer(1, 0.5*cm))
    story.append(caixa(
        "Dica final — Calibracao dos parametros",
        "A melhor estrategia e comparar os resultados do Kairos DSS com a operacao real: "
        "apos uma safra de replantio, meca a producao das linhas replantadas e compare com o "
        "ganho esperado configurado. Ajuste o ATR, o fator de pegamento e o ganho esperado "
        "para que o modelo reflita a realidade da sua fazenda. Com parametros calibrados, "
        "o IOI passa a ser um indicador preciso de rentabilidade por hora de maquina.",
        VERDE_MEDIO, VERDE_BG, VERDE_ESCURO
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO))
    story.append(Paragraph(
        "Kairos DSS v4.0 — Agricef  |  Manual gerado automaticamente",
        CAPTION
    ))

    return story


# ── Geração ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    output = "manual_kairos.pdf"
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=2.2*cm,
        bottomMargin=1.8*cm,
        title="Kairos DSS v4.0 — Manual Completo do Usuario",
        author="Agricef",
        subject="Manual do Sistema de Apoio a Decisao para Replantio de Cana",
    )
    story = build_story()
    doc.build(story, onFirstPage=cabecalho_rodape, onLaterPages=cabecalho_rodape)
    print(f"Manual gerado com sucesso: {output}")
