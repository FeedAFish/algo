# Bibliothèques
import requests  # Requête HTTP
import json  # Format JSON
import time  # Gère le temps
import os  # Interaction avec le système
from pathlib import Path


class DatatoursimeDownload:
	def __init__(self,api_key,url_api,path_output,path_state,page_file,page_size,time_sleep):
		self.api_key = api_key
		self.url_api = url_api
		self.path_output = path_output
		self.path_state = path_state
		self.page_file = page_file
		self.page_size = page_size
		self.time_sleep = time_sleep



	def fetch_with_retry(self, url,retries=8, timeout=30):
		"""
		Fait une requête GET avec gestion des erreurs et retry sur 429 / erreurs temporaires.

		@param url : Url à appeler
		@param retries : Nombre maximal de tentatives
		@param timeout : Délai maximal d'attente d'une réponse HTTP avant erreur
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


	def ensure_output_dir(self):
		"""
			Crée le dossier de sortie s'il n'existe pas.

			@param directory : Dossier où stocker les fichiers NDJSON
		"""

		os.makedirs(self.path_output, exist_ok=True)  # Crée le dossier sans erreur s'il existe déjà


	def get_output_filename(self, filename):
		"""
			Construit le nom d'un fichier de sortie NDJSON.

			@param file_index : Numéro du fichier à produire
			@param directory : Dossier de sortie
		"""

		return os.path.join(self.path_output, f"data_part_{filename:04d}.ndjson")  # Exemple : data_part_0001.ndjson


	def append_ndjson(self,data, filename):
		"""
			Ajoute des données dans un fichier NDJSON.

			@param data : Liste d'objets à enregistrer
			@param filename : Nom du fichier où sauvegarder les données
		"""

		with open(filename, "a", encoding="utf-8") as f:  # Ouvre le fichier en mode ajout
			for item in data:  # Parcourt chaque objet de la liste
				f.write(json.dumps(item, ensure_ascii=False) + "\n")  # Écrit un objet JSON par ligne

		print(f"Ajout dans le fichier : {filename} | {len(data)} objets")


	def save_checkpoint(self,next_url,total_count,page_count,file_index):
		"""
			Sauvegarde l'état de l'extraction.

			@param next_url : Prochaine URL à appeler
			@param total_count : Nombre total d'objets récupérés
			@param page_count : Nombre de pages déjà traitées
			@param file_index : Numéro du fichier courant
			@param state_file : Nom du fichier checkpoint
		"""

		checkpoint = {  # Dictionnaire Python
			"next_url": next_url,
			"total_count": total_count,
			"page_count": page_count,
			"file_index": file_index,
		}

		with open(self.path_state, "w", encoding="utf-8") as f:  # Ouvre le fichier checkpoint en écriture
			json.dump(checkpoint, f, ensure_ascii=False, indent=2)  # Sauvegarde le dictionnaire dans le fichier JSON


	def load_checkpoint(self):
		"""
			Lit le fichier checkpoint.
		"""

		if not os.path.exists(self.path_state):  # Vérifie si le fichier existe
			return None  # Pas de résultat

		with open(self.path_state, "r", encoding="utf-8") as f:  # Ouvre le fichier de checkpoint en lecture
			return json.load(f)  # Renvoie les données sous le format dictionnaire Python


	def count_existing_objects(self,directory):
		"""
			Compte le nombre total d'objets déjà enregistrés dans les fichiers NDJSON.

			@param directory : Dossier qui contient les fichiers NDJSON
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
			Extrait les données.
		"""
		url = None
		self.ensure_output_dir()  # Crée le dossier de sortie si nécessaire

		checkpoint = self.load_checkpoint()  # Appelle la fonction pour voir s'il existe un état de reprise

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

			data = self.fetch_with_retry(url)  # Appelle la fonction de requête robuste
			if not data:  # Vérifie si data est vide
				print("Arrêt de l'extraction à cause d'une erreur.")
				self.save_checkpoint(url, total_count, page_count, file_index)  # Sauvegarde le checkpoint
				return total_count  # Retourne le nombre total d'objets déjà extraits

			objects = data.get("objects", [])  # Récupère la valeur associée à la clé "objects"
			output_file = self.get_output_filename(file_index)  # Détermine le fichier NDJSON courant
			self.append_ndjson(objects, output_file)  # Ajoute les objets au fichier courant

			page_count += 1  # Incrémente le compteur de pages
			total_count += len(objects)  # Met à jour le compteur total d'objets
			print(f"Page {page_count} récupérée | Total : {total_count} objets")

			next_url = data.get("meta", {}).get("next")  # Cherche l'URL de la page suivante

			if page_count % 5 == 0:  # Vérifie si la page est un multiple de 5
				print("Sauvegarde intermédiaire...")
				self.save_checkpoint(next_url, total_count, page_count, file_index)  # Sauvegarde le point de reprise

			if page_count % self.page_file == 0:  # Vérifie s'il faut passer à un nouveau fichier
				file_index += 1  # Incrémente le numéro de fichier
				print(f"Changement de fichier : prochain fichier = {self.get_output_filename(file_index)}")

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