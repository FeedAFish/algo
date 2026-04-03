# Bibliothèques
import requests  # Permet de faire des requêtes HTTP
import json  # Permet de lire le JSON
import os  # Permet de manipuler les dossiers et fichiers


class Picture:
	def __init__(self, path_output, path_picture):
		self.path_output = path_output  # Dossier contenant les fichiers NDJSON
		self.path_picture = path_picture  # Dossier où enregistrer les images


	def ensure_picture_dir(self):
		"""
		Crée le dossier des images s'il n'existe pas.
		"""

		os.makedirs(self.path_picture, exist_ok=True)  # Crée le dossier sans erreur s'il existe déjà


	def get_locator(self, data):
		"""
		Récupère directement le locator dans la structure Datatourisme.
		Retourne None si aucune image n'est trouvée.

		@param data: dictionnaire
		"""

		try:
			return data["hasMainRepresentation"][0]["hasRelatedResource"][0]["locator"][0]  # Va chercher directement la première URL d'image
		except (KeyError, IndexError, TypeError):
			return None  # Retourne None si la structure n'existe pas ou est incomplète


	def get_extension_from_url(self, url):
		"""
		Récupère l'extension du fichier à partir de l'URL.

		@param url : l'url de l'image
		"""

		url = url.lower()  # Met l'URL en minuscule

		for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:  # Liste des extensions possibles
			if ext in url:  # Vérifie si l'extension est présente dans l'URL
				return ext  # Retourne l'extension trouvée

		return ".jpg"  # Retourne jpg par défaut si aucune extension connue n'est trouvée


	def download_image(self, url, output_file):
		"""
		Télécharge une image et l'enregistre sur le disque.

		@param url : l'url de l'image
		@param output_file : fichier de données où récupérer le lien de l'image
		"""

		response = requests.get(url, stream=True, timeout=30)  # Envoie la requête HTTP pour télécharger l'image
		response.raise_for_status()  # Lève une erreur si la requête échoue

		with open(output_file, "wb") as f:  # Ouvre le fichier en écriture binaire
			for chunk in response.iter_content(8192):  # Lit la réponse par blocs de 8192 octets
				if chunk:  # Vérifie que le bloc n'est pas vide
					f.write(chunk)  # Écrit le bloc dans le fichier


	def process_files(self):
		"""
		Lit tous les fichiers NDJSON et télécharge les images trouvées.
		"""

		self.ensure_picture_dir()  # S'assure que le dossier des images existe

		for filename in os.listdir(self.path_output):  # Parcourt tous les fichiers du dossier de sortie
			if not filename.endswith(".ndjson"):  # Ignore les fichiers qui ne sont pas au format ndjson
				continue  # Passe au fichier suivant

			file_path = os.path.join(self.path_output, filename)  # Construit le chemin complet du fichier

			with open(file_path, "r", encoding="utf-8") as f:  # Ouvre le fichier NDJSON en lecture
				for line_number, line in enumerate(f, start=1):  # Lit chaque ligne avec son numéro
					line = line.strip()  # Supprime les espaces et retours à la ligne

					if not line:  # Vérifie si la ligne est vide
						continue  # Ignore les lignes vides

					try:
						data = json.loads(line)  # Convertit la ligne JSON en dictionnaire Python
					except json.JSONDecodeError:  # Capture les erreurs de JSON invalide
						print(f"Erreur JSON dans {filename}, ligne {line_number}")  # Affiche un message d'erreur
						continue  # Passe à la ligne suivante

					uuid = data.get("uuid")  # Récupère l'identifiant unique
					locator = self.get_locator(data)  # Récupère l'URL de l'image

					if not uuid or not locator:  # Vérifie que uuid et locator existent
						continue  # Ignore l'entrée si une donnée manque

					extension = self.get_extension_from_url(locator)  # Détermine l'extension du fichier image
					output_file = os.path.join(self.path_picture, f"{uuid}{extension}")  # Construit le chemin final de l'image

					if os.path.exists(output_file):  # Vérifie si le fichier existe déjà
						continue  # Évite de retélécharger l'image

					try:
						self.download_image(locator, output_file)  # Télécharge et sauvegarde l'image
						print(f"Téléchargé : {output_file}")  # Affiche un message de succès
					except requests.RequestException as e:  # Capture les erreurs liées à la requête HTTP
						print(f"Erreur téléchargement pour {locator} : {e}")  # Affiche l'erreur