import re
import unicodedata
from pathlib import Path

import geopandas as gpd


_COLUNAS_EXPORT = [
    "TALHAO",
    "FID",
    "comp_linha",
    "soma_falhas",
    "perc_falhas",
    "classe",
    "ioi",
    "eficiencia_pct",
    "lucro",
    "geometry",
]


def sanitizar_nome(nome: str) -> str:
    nome = str(nome)
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r"[^\w\-]", "_", nome)
    nome = re.sub(r"_+", "_", nome).strip("_")
    return nome or "talhao"


def exportar_talhoes(
    gdf_linhas_eco: gpd.GeoDataFrame,
    pasta_saida: str,
    campo_talhao: str = "TALHAO",
) -> list:
    """
    Escreve um SHP por talhão com apenas as linhas viáveis (ioi >= ioi_minimo).

    Nome dos arquivos: talhao_<nome_sanitizado>.shp
    Retorna lista de caminhos absolutos gerados.
    Levanta ValueError se nenhuma linha viável existir.
    """
    col_talhao = campo_talhao if campo_talhao in gdf_linhas_eco.columns else "TALHAO"

    viaveis = gdf_linhas_eco[gdf_linhas_eco["viavel"] == True].copy()

    if len(viaveis) == 0:
        raise ValueError(
            "Nenhuma linha economicamente viável (IOI >= mínimo) encontrada. "
            "Nenhum arquivo foi exportado."
        )

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)

    colunas = [c for c in _COLUNAS_EXPORT if c in viaveis.columns]
    viaveis = viaveis[colunas]

    arquivos = []
    for talhao_id in sorted(viaveis[col_talhao].unique()):
        gdf_t  = viaveis[viaveis[col_talhao] == talhao_id].copy()
        caminho = pasta / f"talhao_{sanitizar_nome(str(talhao_id))}.shp"
        gdf_t.to_file(str(caminho))
        arquivos.append(str(caminho))

    return arquivos
