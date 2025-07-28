import os
import geopandas as gpd
from config import data_folder

def save_shp(gdf: gpd.GeoDataFrame, file_name: str = "data.shp"):
    """
    Salva um GeoDataFrame como .shp diretamente na data_folder.

    Args:
        gdf: GeoDataFrame a ser salvo
        file_name: nome do arquivo .shp a ser salvo (default: "data.shp")
    """
    
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    file_path = os.path.join(data_folder, file_name)

    gdf.to_file(file_path)

    print(f"Shapefile salvo em {file_path}")