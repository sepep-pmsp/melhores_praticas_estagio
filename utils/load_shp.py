import os
import geopandas as gpd
from config import data_folder

def load_shp(file_name: str = "data.shp", 
             **read_kwargs) -> gpd.GeoDataFrame:
    """
    
    Carrega um .shp diretamente da pasta data_folder

    Args:
        file_name (str, opcional): nome do .shp
        **read_kwargs: palavras-chave adicionais passadas para geopandas.read_file()
    
    Retorna:
        gpd.GeoDataFrame: geodataframe carregado
    
    """

    file_path = os.path.join(data_folder, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O .shp {file_name} não existe em {os.path.join(data_folder)}")
    
    return gpd.read_file(file_path, **read_kwargs)