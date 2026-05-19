import geopandas as gpd
import pandas as pd
import numpy as np

# =====================================================
# CONFIGURAÇÕES
# =====================================================

CONTORNO = r"C:/projeto_kairos/dados/contorno.shp"
LINHAS = r"C:/projeto_kairos/dados/linhas.shp"
FALHAS = r"C:/projeto_kairos/dados/falhas.shp"

SAIDA = r"C:/projeto_kairos/saida/mapa_percentual_falhas.shp"

CAMPO_TALHAO = "TALHAO"

# =====================================================
# PARÂMETROS
# =====================================================

MIN_FALHA = 1.5

BUFFER_LINHA = 0.5

# =====================================================
# LIMPEZA
# =====================================================

def limpar(gdf):

    gdf = gdf[
        gdf.geometry.notnull()
    ].copy()

    gdf = gdf[
        ~gdf.geometry.is_empty
    ].copy()

    gdf = gdf[
        gdf.is_valid
    ].copy()

    return gdf

# =====================================================
# CLASSIFICAÇÃO
# =====================================================

def classificar(p):

    if p <= 2:
        return "0-2"

    elif p <= 4:
        return "2-4"

    elif p <= 6:
        return "4-6"

    elif p <= 8:
        return "6-8"

    elif p <= 10:
        return "8-10"

    elif p <= 12:
        return "10-12"

    elif p <= 14:
        return "12-14"

    elif p <= 16:
        return "14-16"

    elif p <= 18:
        return "16-18"

    elif p <= 20:
        return "18-20"

    else:
        return ">20"

# =====================================================
# CARREGAR
# =====================================================

print("================================")
print("CARREGANDO DADOS")
print("================================")

contorno = gpd.read_file(CONTORNO)
linhas = gpd.read_file(LINHAS)
falhas = gpd.read_file(FALHAS)

# =====================================================
# CRS
# =====================================================

if linhas.crs != falhas.crs:

    falhas = falhas.to_crs(
        linhas.crs
    )

if contorno.crs != linhas.crs:

    contorno = contorno.to_crs(
        linhas.crs
    )

# =====================================================
# LIMPEZA
# =====================================================

contorno = limpar(contorno)
linhas = limpar(linhas)
falhas = limpar(falhas)

# =====================================================
# VALIDAR
# =====================================================

if CAMPO_TALHAO not in contorno.columns:

    raise Exception(
        f"Campo {CAMPO_TALHAO} não encontrado"
    )

if len(contorno) == 0:
    raise Exception("Contorno vazio")

if len(linhas) == 0:
    raise Exception("Linhas vazias")

if len(falhas) == 0:
    raise Exception("Falhas vazias")

# =====================================================
# GARANTIR FID
# =====================================================

if 'FID' not in linhas.columns:

    linhas['FID'] = range(
        1,
        len(linhas) + 1
    )

# =====================================================
# COMPRIMENTO DAS LINHAS
# =====================================================

linhas['comp_linha'] = (
    linhas.geometry.length
)

# =====================================================
# COMPRIMENTO DAS FALHAS
# =====================================================

falhas['comp_falha'] = (
    falhas.geometry.length
)

# =====================================================
# FILTRAR FALHAS > 1.5m
# =====================================================

falhas = falhas[
    falhas['comp_falha']
    > MIN_FALHA
].copy()

if len(falhas) == 0:

    raise Exception(
        "Nenhuma falha > 1.5m"
    )

print(f"Falhas válidas: {len(falhas)}")

# =====================================================
# DISSOLVE TALHÕES
# =====================================================

contorno = contorno.dissolve(
    by=CAMPO_TALHAO
).reset_index()

# =====================================================
# RESULTADOS
# =====================================================

resultado_final = []

# =====================================================
# LOOP TALHÕES
# =====================================================

for idx_t, row_t in contorno.iterrows():

    talhao = row_t[
        CAMPO_TALHAO
    ]

    print("================================")
    print(f"TALHÃO {talhao}")
    print("================================")

    area = gpd.GeoDataFrame(
        [row_t],
        crs=contorno.crs
    )

    # =================================================
    # RECORTE LINHAS
    # =====================================================

    try:

        linhas_t = gpd.overlay(
            linhas,
            area,
            how='intersection'
        )

    except Exception as e:

        print(f"Erro linhas: {e}")
        continue

    # =================================================
    # RECORTE FALHAS
    # =====================================================

    try:

        falhas_t = gpd.overlay(
            falhas,
            area,
            how='intersection'
        )

    except Exception as e:

        print(f"Erro falhas: {e}")
        continue

    linhas_t = limpar(linhas_t)
    falhas_t = limpar(falhas_t)

    if len(linhas_t) == 0:

        print("Sem linhas")
        continue

    if len(falhas_t) == 0:

        print("Sem falhas")
        continue

    # =================================================
    # BUFFER LINHAS
    # =====================================================

    linhas_buffer = linhas_t.copy()

    linhas_buffer['geometry'] = (
        linhas_buffer.buffer(
            BUFFER_LINHA
        )
    )

    linhas_buffer = limpar(
        linhas_buffer
    )

    # =================================================
    # JOIN ESPACIAL
    # =====================================================

    try:

        join = gpd.sjoin(
            falhas_t,
            linhas_buffer,
            predicate='intersects',
            how='inner'
        )

    except Exception as e:

        print(f"Erro join: {e}")
        continue

    if len(join) == 0:

        print("Join vazio")
        continue

    print(f"Join OK: {len(join)}")

    # =================================================
    # IDENTIFICAR COLUNA FID
    # =====================================================

    if 'FID_right' in join.columns:

        fid_col = 'FID_right'

    elif 'FID' in join.columns:

        fid_col = 'FID'

    else:

        print("FID não encontrado")
        continue

    # =================================================
    # SOMATÓRIO DAS FALHAS
    # =====================================================

    soma = join.groupby(
        fid_col
    )['comp_falha'].sum()

    soma = soma.reset_index()

    soma.columns = [
        'FID',
        'soma_falhas'
    ]

    # =================================================
    # UNIR NAS LINHAS
    # =====================================================

    linhas_t = linhas_t.merge(
        soma,
        on='FID',
        how='left'
    )

    linhas_t['soma_falhas'] = (
        linhas_t['soma_falhas']
        .fillna(0)
    )

    # =================================================
    # PERCENTUAL
    # =====================================================

    linhas_t['perc_falhas'] = (
        linhas_t['soma_falhas']
        /
        linhas_t['comp_linha']
    ) * 100

    # =================================================
    # CLASSIFICAÇÃO
    # =====================================================

    linhas_t['classe'] = (
        linhas_t['perc_falhas']
        .apply(classificar)
    )

    # =================================================
    # TALHÃO
    # =====================================================

    linhas_t[
        CAMPO_TALHAO
    ] = talhao

    resultado_final.append(
        linhas_t
    )

# =====================================================
# CONCATENAR
# =====================================================

if len(resultado_final) == 0:

    raise Exception(
        "Nenhum resultado encontrado"
    )

resultado_final = pd.concat(
    resultado_final,
    ignore_index=True
)

resultado_final = gpd.GeoDataFrame(
    resultado_final,
    geometry='geometry',
    crs=linhas.crs
)

# =====================================================
# EXPORTAR
# =====================================================

resultado_final.to_file(
    SAIDA
)

print("================================")
print("MAPA GERADO")
print("================================")
print(f"Linhas: {len(resultado_final)}")
print(f"Talhões: {resultado_final[CAMPO_TALHAO].nunique()}")
print(f"Saída: {SAIDA}")
print("================================")