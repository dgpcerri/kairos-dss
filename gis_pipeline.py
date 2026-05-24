"""
Pipeline GIS do Kairos — v5.0

Hardening adicionado:
  * `make_valid()` (Shapely 2.x) substitui `buffer(0)` para preservar topologia
    em multipolígonos complexos. `buffer(0)` permanece como fallback se
    `make_valid()` falhar.
  * Geometrias 3D são forçadas a 2D no `limpar()`.
  * Detecção automática da zona UTM SIRGAS 2000 a partir do centróide das
    linhas; emite aviso se o CRS de entrada divergir da zona esperada.
  * Tratamento defensivo em torno de cada operação geométrica crítica;
    talhões que falham geram aviso PT-BR mas não derrubam o pipeline.
  * Liberação de memória explícita após cada talhão (`del`).
"""

import gc
import zipfile
import tempfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.errors import GEOSException
from shapely.ops import unary_union
import streamlit as st

try:
    from shapely import make_valid as _shp_make_valid
    _HAS_MAKE_VALID = True
except ImportError:  # Shapely 1.x fallback
    _HAS_MAKE_VALID = False


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _force_2d(geom):
    """Remove dimensão Z (mantém só X/Y)."""
    if geom is None or geom.is_empty:
        return geom
    if not getattr(geom, "has_z", False):
        return geom
    try:
        from shapely import force_2d
        return force_2d(geom)
    except (ImportError, AttributeError):
        # Fallback Shapely 1.x via WKB round-trip
        from shapely import wkb
        return wkb.loads(wkb.dumps(geom, output_dimension=2))


def _repair(geom):
    """Tenta `make_valid` (Shapely 2.x); fallback `buffer(0)`."""
    if geom is None or geom.is_empty:
        return geom
    try:
        if _HAS_MAKE_VALID:
            fixed = _shp_make_valid(geom)
            if fixed is not None and not fixed.is_empty and fixed.is_valid:
                return fixed
        return geom.buffer(0)
    except (GEOSException, ValueError, TypeError):
        try:
            return geom.buffer(0)
        except Exception:
            return None


def limpar(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove nulos/vazios, força 2D, repara inválidas."""
    if gdf is None or len(gdf) == 0:
        return gdf

    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # 3D → 2D
    if gdf.geometry.has_z.any():
        gdf["geometry"] = gdf.geometry.apply(_force_2d)

    # Repair invalid
    mask_invalid = ~gdf.is_valid
    if mask_invalid.any():
        gdf.loc[mask_invalid, "geometry"] = (
            gdf.loc[mask_invalid, "geometry"].apply(_repair)
        )

    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.is_valid].copy()
    return gdf


def classificar(p: float) -> str:
    bins = [
        (2,  "0-2"),   (4,  "2-4"),   (6,  "4-6"),   (8,  "6-8"),
        (10, "8-10"),  (12, "10-12"), (14, "12-14"), (16, "14-16"),
        (18, "16-18"), (20, "18-20"),
    ]
    for limite, label in bins:
        if p <= limite:
            return label
    return ">20"


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def _safe_extract(zf: zipfile.ZipFile, target: Path) -> None:
    """Extract ZIP rejeitando path-traversal (../, caminhos absolutos)."""
    target = target.resolve()
    for member in zf.namelist():
        dest = (target / member).resolve()
        if not str(dest).startswith(str(target)):
            raise ValueError(
                f"ZIP contém caminho suspeito: '{member}'. "
                "Verifique o arquivo antes de processar."
            )
    zf.extractall(target)


def carregar_shapefile_do_zip(zip_bytes: bytes, nome_camada: str) -> gpd.GeoDataFrame:
    """Extrai um ZIP em memória e carrega o único .shp encontrado."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "upload.zip"
        zip_path.write_bytes(zip_bytes)

        try:
            with zipfile.ZipFile(zip_path) as zf:
                _safe_extract(zf, Path(tmpdir))
        except zipfile.BadZipFile:
            raise ValueError(f"O arquivo de '{nome_camada}' não é um ZIP válido.")

        shp_files = list(Path(tmpdir).rglob("*.shp"))
        if len(shp_files) == 0:
            raise ValueError(f"Nenhum arquivo .shp encontrado no ZIP de '{nome_camada}'.")
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

def _detectar_zona_utm_sirgas(gdf: gpd.GeoDataFrame) -> int | None:
    """A partir do centróide em WGS84, devolve o EPSG SIRGAS 2000 UTM
    (3187x série). Retorna None se não conseguir detectar.

    SIRGAS 2000 UTM 18S=31978, 19S=31979, 20S=31980, 21S=31981, 22S=31982,
                   23S=31983, 24S=31984, 25S=31985.
    """
    try:
        centro = gdf.to_crs(4326).unary_union.centroid
        lon, lat = centro.x, centro.y
        if lat > 0 or lon > -30 or lon < -78:
            return None
        zona = int((lon + 180) / 6) + 1
        if 18 <= zona <= 25:
            return 31960 + zona  # 18→31978, 19→31979, …, 25→31985
    except Exception:
        return None
    return None


def alinhar_crs(
    contorno: gpd.GeoDataFrame,
    linhas: gpd.GeoDataFrame,
    falhas: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, list[str]]:
    """Garante que todas as camadas estão no MESMO CRS projetado em metros.

    Estratégia:
        1. Toma o CRS de `linhas` como referência.
        2. Se for geográfico, tenta detectar zona UTM SIRGAS e reprojeta TUDO.
        3. Reprojeta contorno/falhas se diferentes.
        4. Retorna lista de avisos PT-BR sobre decisões automáticas.
    """
    avisos: list[str] = []
    crs_ref = linhas.crs

    if crs_ref is None:
        raise ValueError(
            "Shapefile de Linhas não possui CRS definido (.prj ausente?). "
            "Defina o sistema de coordenadas antes de fazer upload."
        )

    # Se CRS é geográfico, tenta promover para UTM SIRGAS
    if crs_ref.is_geographic:
        zona_utm = _detectar_zona_utm_sirgas(linhas)
        if zona_utm is None:
            raise ValueError(
                "CRS de Linhas é geográfico (graus) e não foi possível detectar "
                "uma zona UTM SIRGAS apropriada. Reprojete os shapefiles para "
                "SIRGAS 2000 UTM antes do upload."
            )
        crs_ref = f"EPSG:{zona_utm}"
        avisos.append(
            f"CRS de entrada era geográfico — reprojetado automaticamente para "
            f"SIRGAS 2000 UTM (EPSG:{zona_utm})."
        )
        linhas = linhas.to_crs(crs_ref)

    if contorno.crs != crs_ref:
        contorno = contorno.to_crs(crs_ref)
    if falhas.crs != crs_ref:
        falhas = falhas.to_crs(crs_ref)

    return contorno, linhas, falhas, avisos


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
            "CRS geográfico detectado após `alinhar_crs`. "
            "Use um CRS projetado em metros (ex: SIRGAS 2000 UTM)."
        )
    if crs and not crs.is_geographic:
        try:
            unit = crs.axis_info[0].unit_name.lower()
            if unit not in ("metre", "meter"):
                raise ValueError(
                    f"Unidade linear do CRS é '{unit}', esperado 'metre'. "
                    "Use um CRS projetado em metros (ex: SIRGAS 2000 UTM)."
                )
        except (IndexError, AttributeError):
            pass


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
) -> tuple[gpd.GeoDataFrame | None, list[str]]:
    """Pipeline por talhão (v5.0 — com tratamento defensivo amplo)."""
    avisos: list[str] = []

    try:
        talhao_geom = area.geometry.iloc[0]

        # ── clip linhas ──
        try:
            linhas_t = gpd.clip(linhas, talhao_geom, keep_geom_type=True)
        except (GEOSException, ValueError) as exc:
            return None, [f"Talhão '{talhao_id}': falha no clip de linhas ({exc})."]

        linhas_t = limpar(linhas_t)
        if len(linhas_t) == 0:
            return None, [f"Talhão '{talhao_id}': sem linhas após recorte."]

        linhas_t = linhas_t.reset_index(drop=True).copy()
        linhas_t["FID"] = linhas_t.index
        linhas_t["comp_linha"] = linhas_t.geometry.length
        linhas_t = linhas_t[linhas_t["comp_linha"] > 0].copy()

        if len(linhas_t) == 0:
            return None, [
                f"Talhão '{talhao_id}': todas as linhas com comprimento zero após recorte."
            ]

        # ── clip falhas ──
        try:
            falhas_t = gpd.clip(falhas, talhao_geom, keep_geom_type=True)
            falhas_t = limpar(falhas_t)
        except (GEOSException, ValueError) as exc:
            avisos.append(
                f"Talhão '{talhao_id}': falha no clip de falhas ({exc}). "
                "Usando soma_falhas = 0."
            )
            falhas_t = falhas.iloc[0:0]

        if len(falhas_t) == 0:
            avisos.append(
                f"Talhão '{talhao_id}': sem falhas no recorte. "
                "Linhas classificadas com 0% de falha."
            )
            linhas_t["soma_falhas"] = 0.0
        else:
            # ── buffer falhas → polygons ──
            try:
                falhas_buf = falhas_t.copy()
                falhas_buf["geometry"] = falhas_buf.geometry.buffer(buffer_falha)
                falhas_buf = limpar(falhas_buf)
            except (GEOSException, ValueError) as exc:
                avisos.append(
                    f"Talhão '{talhao_id}': erro no buffer de falhas ({exc})."
                )
                falhas_buf = falhas_t.iloc[0:0]

            if len(falhas_buf) == 0:
                linhas_t["soma_falhas"] = 0.0
            else:
                try:
                    falha_union = unary_union(falhas_buf.geometry.tolist())
                    falha_union = _repair(falha_union)
                    linhas_slim = linhas_t[["FID", "geometry"]].copy()

                    gap_segs = gpd.clip(linhas_slim, falha_union, keep_geom_type=True)
                    gap_segs = limpar(gap_segs)

                    if len(gap_segs) > 0:
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

                except (GEOSException, ValueError, MemoryError) as exc:
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

@st.cache_data(show_spinner=False, max_entries=3)
def run_pipeline(
    contorno_bytes: bytes,
    linhas_bytes: bytes,
    falhas_bytes: bytes,
    campo_talhao: str,
    buffer_falha: float,
    min_falha: float,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, list[str]]:
    """Pipeline GIS completo cacheado pelo Streamlit.

    Cache:
        max_entries=3 limita memória no Streamlit Cloud.
    """
    avisos_globais: list[str] = []

    contorno = carregar_shapefile_do_zip(contorno_bytes, "Contorno")
    linhas   = carregar_shapefile_do_zip(linhas_bytes,   "Linhas")
    falhas   = carregar_shapefile_do_zip(falhas_bytes,   "Falhas")

    contorno, linhas, falhas, avisos_crs = alinhar_crs(contorno, linhas, falhas)
    avisos_globais.extend(avisos_crs)

    contorno = limpar(contorno)
    linhas   = limpar(linhas)
    falhas   = limpar(falhas)

    validar_entradas(contorno, linhas, falhas, campo_talhao)

    # Pre-filter falhas globally
    falhas = falhas.copy()
    falhas["comp_falha"] = falhas.geometry.length
    falhas = falhas[falhas["comp_falha"] > min_falha].copy()

    if len(falhas) == 0:
        raise ValueError(
            f"Nenhuma falha com comprimento > {min_falha} m encontrada nos dados."
        )

    contorno_diss = contorno.dissolve(by=campo_talhao).reset_index()

    resultados: list[gpd.GeoDataFrame] = []
    todos_avisos: list[str] = list(avisos_globais)

    for _, row in contorno_diss.iterrows():
        talhao_id = row[campo_talhao]
        area = gpd.GeoDataFrame([row], crs=contorno_diss.crs)

        gdf_t, avs = processar_talhao(
            talhao_id, area, linhas, falhas, buffer_falha, min_falha
        )
        todos_avisos.extend(avs)

        if gdf_t is not None and len(gdf_t) > 0:
            resultados.append(gdf_t)

        del area
        gc.collect()

    if len(resultados) == 0:
        raise ValueError(
            "Nenhum talhão processado com sucesso. "
            "Verifique os arquivos enviados e os avisos de processamento."
        )

    resultado_final = pd.concat(resultados, ignore_index=True)
    resultado_final = gpd.GeoDataFrame(
        resultado_final, geometry="geometry", crs=linhas.crs
    )

    # Libera lista intermediária
    del resultados, falhas
    gc.collect()

    return resultado_final, contorno_diss, todos_avisos
