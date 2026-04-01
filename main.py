# Bibliothèques
import requests  # Requête HTTP
import json  # Format JSON
import time  # Gère le temps
import os  # Interaction avec le système
from API.script.api import Api 

api_key = "a28db3a7-7c19-4721-b1c7-bb5c76250566"  # Variable globale qui sera la clef d'authentification de l'API
url_api = "https://api.datatourisme.fr/v1/catalog"  # L'url de base de l'API

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Chemin 
path_output = os.path.join(BASE_DIR, "API", "data_raw_ndjson") # Dossier de sauvegarde des données brutes au format NDJSON
path_state = os.path.join(BASE_DIR, "API", "checkpoint.json")  # Fichier qui garde la progression de l'extraction pour pouvoir reprendre en cas d'arrêt


page_file = 1000  # Nombre de pages à stocker dans un même fichier
page_size = 21  # Nombre d'objets demandés par page à l'API
time_sleep = 0.1 # Temps avant de reprendre une requête

api = Api(api_key,url_api,path_output,path_state,page_file,page_size,time_sleep)
api.extract_data()