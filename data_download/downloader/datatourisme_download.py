# Bibliothèques
import requests  # Requête HTTP
import json  # Format JSON
import time  # Gère le temps
import os  # Interaction avec le système
from pathlib import Path


class DatatoursimeDownload:
	"""
	Handles the extraction of data from the Datatourisme API.

	This class manages API requests, pagination, retry logic,
	NDJSON file writing, and checkpointing to allow resuming
	interrupted downloads.

	Attributes:

		api_key (str): API key used for authentication.
		url_api (str): Base URL of the API.
		path_output (str): Directory where NDJSON files are stored.
		path_state (str): File path used to store checkpoint state.
		page_file (int): Number of pages per output file.
		page_size (int): Number of objects per API page.
		time_sleep (int | float): Delay between API requests (in seconds).
	"""

	def __init__(self,api_key,url_api,path_output,path_state,page_file,page_size,time_sleep):
		"""
		Initializes the DatatoursimeDownload instance.

		Args:

			api_key (str): API key for authentication.
			url_api (str): Base API endpoint.
			path_output (str): Output directory for NDJSON files.
			path_state (str): Path to the checkpoint file.
			page_file (int): Number of pages per output file.
			page_size (int): Number of objects per page.
			time_sleep (int | float): Delay between requests in seconds.
		"""

		self.api_key = api_key
		self.url_api = url_api
		self.path_output = path_output
		self.path_state = path_state
		self.page_file = page_file
		self.page_size = page_size
		self.time_sleep = time_sleep



	def _fetch_with_retry(self, url,retries=8, timeout=30):
		"""
		Sends a GET request with retry logic.

		Retries are performed in case of HTTP 429 (rate limiting)
		or server errors (5xx), using exponential backoff.

		Args:
			url (str): URL to request.
			retries (int, optional): Maximum number of retry attempts. Defaults to 8.
			timeout (int, optional): Request timeout in seconds. Defaults to 30.

		Returns:

			dict | None: Parsed JSON response if successful, otherwise None.
		"""

		for attempt in range(retries):  # Boucle de répétition
			try:
				response = requests.get(url, timeout=timeout)  # Requête pour récupérer les données avec un timeout

				if response.status_code == 200:  # Gère les succès de requête
					return response.json()  # Renvoie les données JSON converties en dictionnaire Python

				if response.status_code == 429:  # Gère l'erreur "trop de requêtes"
					wait_time = min(2 ** attempt, 60)  # Calcule le temps d'attente
					print(f"[429] Trop de requêtes. Nouvelle tentative dans {wait_time}s...")
					time.sleep(wait_time)  # Le programme attend
					continue  # Passe à la tentative suivante

				if 500 <= response.status_code < 600:  # Gère les erreurs serveur
					wait_time = min(2 ** attempt, 60)  # Calcule le temps d'attente
					print(f"[{response.status_code}] Erreur serveur. Nouvelle tentative dans {wait_time}s...")
					time.sleep(wait_time)  # Le programme attend
					continue  # Passe à la tentative suivante

				print(f"Erreur HTTP {response.status_code}")  # Gère les autres erreurs HTTP
				print(response.text)  # Affiche le détail de l'erreur
				return None  # Pas de résultat exploitable

			except requests.exceptions.RequestException as e:  # Intercepte les exceptions réseau
				wait_time = min(2 ** attempt, 60)  # Calcule le temps d'attente
				print(f"Erreur réseau : {e}")
				print(f"Nouvelle tentative dans {wait_time}s...")
				time.sleep(wait_time)  # Le programme attend

		print("Échec après plusieurs tentatives.")
		return None  # Pas de résultat


	def _ensure_output_dir(self):
		"""
		Ensures that the output directory exists.

		Creates the directory if it does not already exist.
		"""

		os.makedirs(self.path_output, exist_ok=True)  # Crée le dossier sans erreur s'il existe déjà


	def _get_output_filename(self, filename):
		"""
		Builds the output NDJSON file path.

		Args:

			filename (int): Index of the output file.

		Returns:

			str: Full path to the NDJSON file.
		"""

		return os.path.join(self.path_output, f"data_part_{filename:04d}.ndjson")  # Exemple : data_part_0001.ndjson


	def _append_ndjson(self,data, filename):
		"""
		Appends data to an NDJSON file.

		Each object is written as a JSON line.

		Args:

			data (list[dict]): List of objects to write.
			filename (str): Target NDJSON file path.
		"""

		with open(filename, "a", encoding="utf-8") as f:  # Ouvre le fichier en mode ajout
			for item in data:  # Parcourt chaque objet de la liste
				f.write(json.dumps(item, ensure_ascii=False) + "\n")  # Écrit un objet JSON par ligne

		print(f"Ajout dans le fichier : {filename} | {len(data)} objets")


	def _save_checkpoint(self,next_url,total_count,page_count,file_index):
		"""
		Saves the current extraction state to a checkpoint file.

		Args:

			next_url (str): URL of the next page to fetch.
			total_count (int): Total number of processed objects.
			page_count (int): Number of processed pages.
			file_index (int): Current output file index.
		"""

		checkpoint = {  # Dictionnaire Python
			"next_url": next_url,
			"total_count": total_count,
			"page_count": page_count,
			"file_index": file_index,
		}

		with open(self.path_state, "w", encoding="utf-8") as f:  # Ouvre le fichier checkpoint en écriture
			json.dump(checkpoint, f, ensure_ascii=False, indent=2)  # Sauvegarde le dictionnaire dans le fichier JSON


	def _load_checkpoint(self):
		"""
		Loads the checkpoint file if it exists.

		Returns:

			dict | None: Checkpoint data if available, otherwise None.
		"""

		if not os.path.exists(self.path_state):  # Vérifie si le fichier existe
			return None  # Pas de résultat

		with open(self.path_state, "r", encoding="utf-8") as f:  # Ouvre le fichier de checkpoint en lecture
			return json.load(f)  # Renvoie les données sous le format dictionnaire Python


	def count_existing_objects(self,directory):
		"""
		Counts the total number of objects stored in NDJSON files.

		Args:

			directory (str): Directory containing NDJSON files.

		Returns:

			int: Total number of objects found.
		"""

		if not os.path.exists(directory):  # Vérifie si le dossier existe
			return 0  # Aucun objet si le dossier n'existe pas

		total = 0  # Initialise le compteur total

		for filename in sorted(os.listdir(directory)):  # Parcourt tous les fichiers du dossier
			if filename.endswith(".ndjson"):  # Ne garde que les fichiers NDJSON
				filepath = os.path.join(directory, filename)  # Construit le chemin complet
				with open(filepath, "r", encoding="utf-8") as f:  # Ouvre le fichier en lecture
					for _ in f:  # Compte chaque ligne
						total += 1  # Une ligne = un objet

		return total  # Renvoie le nombre total d'objets déjà sauvegardés


	def extract_data(self):
		"""
		Extracts data from the API and stores it in NDJSON files.

		Supports resuming from a checkpoint if available.

		Returns:

			int: Total number of extracted objects.
		"""

		url = None
		self._ensure_output_dir()  # Crée le dossier de sortie si nécessaire

		checkpoint = self._load_checkpoint()  # Appelle la fonction pour voir s'il existe un état de reprise

		if checkpoint and ((checkpoint["total_count"]/checkpoint["page_count"]) == self.page_size): # Vérifie si checkpoint est vide ou non
			print("Checkpoint trouvé. Reprise en cours...")
			url = checkpoint["next_url"]  # Récupère l'URL stockée dans le checkpoint
			page_count = checkpoint["page_count"]  # Récupère le nombre de pages déjà traitées
			file_index = checkpoint["file_index"]  # Récupère le numéro du fichier courant
			total_count = checkpoint["total_count"]  # Récupère le nombre d'objets déjà traités
			print(f"Reprise depuis page ~{page_count + 1} | Objets déjà sauvegardés : {total_count}")
		else:  # Démarre une extraction neuve
			print("Début de l'extraction...")
			url = f"{self.url_api}?api_key={self.api_key}&page=1&page_size={self.page_size}&lang=fr"  # Construit l'URL de départ
			page_count = 0  # Initialise le compteur de pages
			file_index = 1  # Initialise le numéro du premier fichier
			total_count = 0  # Initialise le compteur total d'objets
		while url:  # Tant que url n'est pas None ou vide
			print(f"Requête : {url}")

			data = self._fetch_with_retry(url)  # Appelle la fonction de requête robuste
			if not data:  # Vérifie si data est vide
				print("Arrêt de l'extraction à cause d'une erreur.")
				self._save_checkpoint(url, total_count, page_count, file_index)  # Sauvegarde le checkpoint
				return total_count  # Retourne le nombre total d'objets déjà extraits

			objects = data.get("objects", [])  # Récupère la valeur associée à la clé "objects"
			output_file = self._get_output_filename(file_index)  # Détermine le fichier NDJSON courant
			self._append_ndjson(objects, output_file)  # Ajoute les objets au fichier courant

			page_count += 1  # Incrémente le compteur de pages
			total_count += len(objects)  # Met à jour le compteur total d'objets
			print(f"Page {page_count} récupérée | Total : {total_count} objets")

			next_url = data.get("meta", {}).get("next")  # Cherche l'URL de la page suivante

			if page_count % 5 == 0:  # Vérifie si la page est un multiple de 5
				print("Sauvegarde intermédiaire...")
				self._save_checkpoint(next_url, total_count, page_count, file_index)  # Sauvegarde le point de reprise

			if page_count % self.page_file == 0:  # Vérifie s'il faut passer à un nouveau fichier
				file_index += 1  # Incrémente le numéro de fichier
				print(f"Changement de fichier : prochain fichier = {self._get_output_filename(file_index)}")

			url = next_url  # Met à jour l'URL suivante
			time.sleep(self.time_sleep)  # Le programme attend pour éviter de surcharger l'API

		if os.path.exists(self.path_state):  # Vérifie si le fichier temporaire existe
			os.remove(self.path_state)  # Supprime le fichier temporaire
			print("Checkpoint supprimé : extraction terminée.")

		return total_count  # Retourne le nombre total d'objets extraits


	if __name__ == "__main__":  # Vérifie si le fichier est exécuté directement
		print("Début extraction...")

		total = extract_data()  # Appelle la fonction qui extrait les données

		print(f"Extraction terminée : {total} objets")


	def extract_types(self):
		"""
		Extracts all "type" values from NDJSON files.

		Iterates over all files in the output directory and collects
		type fields from each JSON object.

		Returns:

			list: List of extracted types.
		"""

		all_types = []

		for file_path in Path(self.path_output).glob("*.ndjson"):  # Trouve tous les fichiers .ndjson
			print(".")
			with open(file_path, "r", encoding="utf-8") as f:
				for line_number, line in enumerate(f, start=1):
					line = line.strip()

					if not line:
						continue

					try:
						data = json.loads(line)
					except json.JSONDecodeError:
						print(f"Erreur JSON dans {file_path.name}, ligne {line_number}")
						continue

					types = data.get("type", [])

					if isinstance(types, list):
						all_types.extend(types)

		return all_types