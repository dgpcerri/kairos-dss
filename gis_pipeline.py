import zipfile
import tempfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
import streamlit as st


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def limpar(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.is_valid].copy()
    return gdf


def classificar(p: float) -> str:
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


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def carregar_shapefile_do_zip(zip_bytes: bytes, nome_camada: str) -> gpd.GeoDataFrame:
    """Extrai um ZIP em memória e carrega o único .shp encontrado."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "upload.zip"
        zip_path.write_bytes(zip_bytes)

        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
        except zipfile.BadZipFile:
            raise ValueError(
                f"O arquivo de '{nome_camada}' não é um ZIP válido."
            )

        shp_files = list(Path(tmpdir).rglob("*.shp"))

        if len(shp_files) == 0:
            raise ValueError(
                f"Nenhum arquivo .shp encontrado no ZIP de '{nome_camada}'."
            )
        if len(shp_files) > 1:
            nomes = ", ".join(f.name for f in shp_files)
            raise ValueError(
                f"Múltiplos .shp no ZIP de '{nome_camada}': {nomes}. "
                "Inclua apenas um shapefile por ZIP."
            )

        return gpd.read_file(shp_files[0])


# ---------------------------------------------------------------------------
# CRS & validation
# ---------------------------------------------------------------------------

def alinhar_crs(
    contorno: gpd.GeoDataFrame,
    linhas: gpd.GeoDataFrame,
    falhas: gpd.GeoDataFrame,
) -> tuple:
    crs_ref = linhas.crs

    if crs_ref is None:
        raise ValueError(
            "Shapefile de Linhas não possui CRS definido. "
            "Defina o sistema de coordenadas antes de fazer upload."
        )

    if contorno.crs != crs_ref:
        contorno = contorno.to_crs(crs_ref)
    if falhas.crs != crs_ref:
        falhas = falhas.to_crs(crs_ref)

    return contorno, linhas, falhas


def validar_entradas(
    contorno: gpd.GeoDataFrame,
    linhas: gpd.GeoDataFrame,
    falhas: gpd.GeoDataFrame,
    campo_talhao: str,
) -> None:
    if campo_talhao not in contorno.columns:
        cols = ", ".join(str(c) for c in contorno.columns.tolist())
        raise ValueError(
            f"Campo '{campo_talhao}' não encontrado no Contorno. "
            f"Colunas disponíveis: {cols}"
        )

    if len(contorno) == 0:
        raise ValueError("Shapefile de Contorno está vazio após limpeza.")
    if len(linhas) == 0:
        raise ValueError("Shapefile de Linhas está vazio após limpeza.")
    if len(falhas) == 0:
        raise ValueError("Shapefile de Falhas está vazio após limpeza.")

    crs = linhas.crs
    if crs and crs.is_geographic:
        raise ValueError(
            "CRS geográfico detectado (graus). "
            "O buffer em metros requer um CRS projetado, como SIRGAS 2000 UTM. "
            "Reprojecte os shapefiles antes de fazer upload."
        )


# ---------------------------------------------------------------------------
# Per-talhão processing
# ---------------------------------------------------------------------------

def processar_talhao(
    talhao_id: Any,
    area: gpd.GeoDataFrame,
    linhas: gpd.GeoDataFrame,
    falhas: gpd.GeoDataFrame,
    buffer_falha: float,
    min_falha: float,
) -> tuple:
    """
    Processa um único talhão e retorna (GeoDataFrame | None, lista de avisos).

    Pipeline:
      1. Clip linhas e falhas ao polígono do talhão
      2. Reatribui FID sequencial pós-clip
      3. Recalcula comp_linha com geometria clippada
      4. Buffer nas falhas (polígonos)
      5. Clip linhas ao union das falhas bufferizadas → segmentos de falha
      6. Explode MultiLineStrings em LineStrings individuais
      7. Filtra segmentos > min_falha
      8. Soma por FID → soma_falhas
      9. Calcula perc_falhas e classe
    """
    avisos = []

    try:
        talhao_geom = area.geometry.iloc[0]

        # --- clip linhas ---
        linhas_t = gpd.clip(linhas, talhao_geom, keep_geom_type=True)
        linhas_t = limpar(linhas_t)

        if len(linhas_t) == 0:
            return None, [f"Talhão '{talhao_id}': sem linhas após recorte."]

        # New sequential FID within this talhão to avoid duplicates from clip
        linhas_t = linhas_t.reset_index(drop=True).copy()
        linhas_t["FID"] = linhas_t.index

        # Length after clip (actual length within the talhão boundary)
        linhas_t["comp_linha"] = linhas_t.geometry.length
        linhas_t = linhas_t[linhas_t["comp_linha"] > 0].copy()

        if len(linhas_t) == 0:
            return None, [f"Talhão '{talhao_id}': todas as linhas têm comprimento zero após recorte."]

        # --- clip falhas ---
        falhas_t = gpd.clip(falhas, talhao_geom, keep_geom_type=True)
        falhas_t = limpar(falhas_t)

        if len(falhas_t) == 0:
            avisos.append(
                f"Talhão '{talhao_id}': sem falhas no recorte. "
                "Linhas classificadas com 0% de falha."
            )
            linhas_t["soma_falhas"] = 0.0
        else:
            # --- buffer falhas → polygons ---
            falhas_buf = falhas_t.copy()
            falhas_buf["geometry"] = falhas_buf.geometry.buffer(buffer_falha)
            falhas_buf = limpar(falhas_buf)

            if len(falhas_buf) == 0:
                linhas_t["soma_falhas"] = 0.0
            else:
                falha_union = unary_union(falhas_buf.geometry)
                linhas_slim = linhas_t[["FID", "geometry"]].copy()

                try:
                    gap_segs = gpd.clip(
                        linhas_slim, falha_union, keep_geom_type=True
                    )
                    gap_segs = limpar(gap_segs)

                    if len(gap_segs) > 0:
                        # Explode MultiLineStrings so each segment is measured individually
                        gap_segs = gap_segs.explode(index_parts=False)
                        gap_segs = limpar(gap_segs)
                        gap_segs["seg_len"] = gap_segs.geometry.length
                        gap_segs = gap_segs[gap_segs["seg_len"] > min_falha]

                    if len(gap_segs) > 0:
                        soma = (
                            gap_segs.groupby("FID")["seg_len"]
                            .sum()
                            .reset_index()
                            .rename(columns={"seg_len": "soma_falhas"})
                        )
                        linhas_t = linhas_t.merge(soma, on="FID", how="left")
                        linhas_t["soma_falhas"] = linhas_t["soma_falhas"].fillna(0.0)
                    else:
                        linhas_t["soma_falhas"] = 0.0

                except Exception as exc:
                    avisos.append(
                        f"Talhão '{talhao_id}': erro no recorte de falhas ({exc}). "
                        "Usando soma_falhas = 0."
                    )
                    linhas_t["soma_falhas"] = 0.0

        linhas_t["perc_falhas"] = (
            linhas_t["soma_falhas"] / linhas_t["comp_linha"]
        ) * 100

        linhas_t["classe"] = linhas_t["perc_falhas"].apply(classificar)
        linhas_t["TALHAO"] = str(talhao_id)

        return linhas_t, avisos

    except Exception as exc:
        return None, [f"Talhão '{talhao_id}': erro inesperado ({exc})."]


# ---------------------------------------------------------------------------
# Main pipeline (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def run_pipeline(
    contorno_bytes: bytes,
    linhas_bytes: bytes,
    falhas_bytes: bytes,
    campo_talhao: str,
    buffer_falha: float,
    min_falha: float,
) -> tuple:
    """
    Pipeline GIS completo. Resultado cacheado por Streamlit.

    Retorna (GeoDataFrame com geometria + FID + TALHAO + comp_linha +
             soma_falhas + perc_falhas + classe, lista de avisos).
    """
    contorno = carregar_shapefile_do_zip(contorno_bytes, "Contorno")
    linhas = carregar_shapefile_do_zip(linhas_bytes, "Linhas")
    falhas = carregar_shapefile_do_zip(falhas_bytes, "Falhas")

    contorno, linhas, falhas = alinhar_crs(contorno, linhas, falhas)

    contorno = limpar(contorno)
    linhas = limpar(linhas)
    falhas = limpar(falhas)

    validar_entradas(contorno, linhas, falhas, campo_talhao)

    # Pre-filter falhas globally (Kairos doesn't replant below this threshold)
    falhas = falhas.copy()
    falhas["comp_falha"] = falhas.geometry.length
    falhas = falhas[falhas["comp_falha"] > min_falha].copy()

    if len(falhas) == 0:
        raise ValueError(
            f"Nenhuma falha com comprimento > {min_falha} m encontrada nos dados."
        )

    contorno_diss = contorno.dissolve(by=campo_talhao).reset_index()

    resultados = []
    todos_avisos: list[str] = []

    for _, row in contorno_diss.iterrows():
        talhao_id = row[campo_talhao]
        area = gpd.GeoDataFrame([row], crs=contorno_diss.crs)

        gdf_t, avs = processar_talhao(
            talhao_id, area, linhas, falhas, buffer_falha, min_falha
        )
        todos_avisos.extend(avs)

        if gdf_t is not None and len(gdf_t) > 0:
            resultados.append(gdf_t)

    if len(resultados) == 0:
        raise ValueError(
            "Nenhum talhão processado com sucesso. "
            "Verifique os arquivos enviados e os avisos de processamento."
        )

    resultado_final = pd.concat(resultados, ignore_index=True)
    resultado_final = gpd.GeoDataFrame(
        resultado_final, geometry="geometry", crs=linhas.crs
    )

    return resultado_final, contorno_diss, todos_avisos
