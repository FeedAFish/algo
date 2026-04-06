import random
from typing import Dict, Any, List, Tuple
from pymongo.errors import BulkWriteError
from .mongo import MongoConnection


class RatingGenerator:
    CERTIFICATION_RATINGS = {
        "5 étoiles": 5,
        "4 étoiles": 4,
        "3 étoiles": 3,
        "2 étoiles": 2,
        "1 étoile": 1,
    }
    COMMENTS = {
        5: [
            "Excellent établissement, très recommandé!",
            "Service de qualité supérieure et accueil chaleureux",
            "Expérience exceptionnelle, à visiter absolument!",
            "Très satisfait, je reviendrai certainement",
            "Outstanding! Dépassé toutes mes attentes",
        ],
        4: [
            "Très bon, je recommande vivement",
            "Bonne expérience, à revisiter",
            "Établissement de qualité",
            "Satisfait de ma visite",
            "Bon rapport qualité-prix",
        ],
        3: [
            "Correct, pas mauvais",
            "Moyen, quelque chose d'améliorable",
            "Acceptable, standard",
            "Pas terrible, mais pas horrible non plus",
            "À améliorer sur certains points",
        ],
        2: [
            "Décevant, ne correspondait pas à l'attente",
            "Problèmes observés lors de la visite",
            "À améliorer significativement",
            "Pas satisfait du service",
            "Besoin de mieux faire",
        ],
        1: [
            "Très décevant, ne recommande pas",
            "Expérience négative",
            "Problèmes sérieux",
            "À éviter",
            "Vraiment déçu",
        ],
    }

    def __init__(self, seed=42):
        random.seed(seed)

    def generate_rating(self) -> Tuple[int, str]:
        rating = random.choices([5, 4, 3, 2, 1], weights=[30, 35, 20, 10, 5])[0]
        comment = random.choice(self.COMMENTS[rating])
        return rating, comment


class RatingInserter(MongoConnection):

    def __init__(self, seed=42):
        super().__init__()
        self.generator = RatingGenerator(seed=seed)
        self.batch_size = 1000

    def insert_batch(self, raw_records: List[Dict[str, Any]]) -> Tuple[int, int]:
        if not raw_records:
            return 0, 0

        rating_records = []
        for record in raw_records:
            uuid = record.get("uuid", "N/A")
            rating, comment = self.generator.generate_rating()
            rating_records.append(
                {
                    "uuid": uuid,
                    "rating": rating,
                    "comment": comment,
                }
            )

        if not rating_records:
            return 0, len(raw_records)

        collection = self.db["place_ratings"]
        try:
            result = collection.insert_many(rating_records, ordered=False)
            inserted = len(result.inserted_ids)
            return inserted, 0
        except BulkWriteError as e:
            inserted = e.details.get("nInserted", 0)
            return inserted, len(raw_records) - inserted

    def run(self) -> Dict[str, int]:
        try:
            raw_collection = self.db["place_raw"]
            total_count = raw_collection.count_documents({})

            total_inserted = 0

            for _, offset in enumerate(range(0, total_count, self.batch_size)):
                batch = list(raw_collection.find().skip(offset).limit(self.batch_size))
                inserted, _ = self.insert_batch(batch)
                total_inserted += inserted

            print(f"Ratings inserted: {total_inserted:,}")
            return {
                "total_processed": total_count,
                "total_inserted": total_inserted,
                "total_duplicates": 0,
            }
        finally:
            self.disconnect()

    def run_partial(self, sample_percentage: float = 0.5) -> Dict[str, int]:
        try:
            raw_collection = self.db["place_raw"]
            total_count = raw_collection.count_documents({})

            total_inserted = 0

            for _, offset in enumerate(range(0, total_count, self.batch_size)):
                batch = list(raw_collection.find().skip(offset).limit(self.batch_size))
                sampled_batch = random.sample(
                    batch, int(len(batch) * sample_percentage)
                )
                inserted, _ = self.insert_batch(sampled_batch)
                total_inserted += inserted

            print(f"Ratings inserted: {total_inserted:,}")
            return {
                "total_processed": total_count,
                "total_inserted": total_inserted,
                "total_duplicates": 0,
            }
        finally:
            self.disconnect()
