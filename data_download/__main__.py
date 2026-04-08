# Bibliothèques
import requests  # Requête HTTP
import json  # Format JSON
import time  # Gère le temps
import os  # Interaction avec le système
from .downloader.datatourisme_download import DatatoursimeDownload
from .downloader.picture import Picture
from dotenv import load_dotenv

load_dotenv()  # charge le .env


api_key = os.getenv("API_KEY") # Charge la clef API depuis l'env
url_api = "https://api.datatourisme.fr/v1/catalog"  # L'url de base de l'API

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Chemin
path_output = os.path.join(BASE_DIR, "..","data_lake") # Dossier de sauvegarde des données brutes au format NDJSON
path_state = os.path.join(BASE_DIR, "../data_lake", "checkpoint.json")  # Fichier qui garde la progression de l'extraction pour pouvoir reprendre en cas d'arrêt
path_picture = os.path.join(BASE_DIR, "..", "pictures")

page_file = 1000  # Nombre de pages à stocker dans un même fichier
page_size = 21  # Nombre d'objets demandés par page à l'API
time_sleep = 0.1 # Temps avant de reprendre une requête


if __name__ == "__main__":
	datatoursime_download = DatatoursimeDownload(api_key,url_api,path_output,path_state,page_file,page_size,time_sleep) # Objet
	datatoursime_download.extract_data() # Extrait les données depuis l'API
	# print(set(datatoursime_download.extract_types())) # Affiche la liste des types de POI

	picture = Picture(path_output,path_picture) # Objet
	# picture.process_files() # Extrait les images depuis les données et les enregistre
