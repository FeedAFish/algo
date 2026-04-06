from typing import Dict, Any, List
from collections import defaultdict
from pymongo.errors import BulkWriteError
from .mongo import MongoConnection
from random import randint


class DictFlattener:
    def __init__(self, sep: str = "_"):
        self.sep = sep

    def flatten(self, data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        items = []

        for k, v in data.items():
            new_key = f"{parent_key}{self.sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self.flatten(v, new_key).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(self.flatten(item, f"{new_key}_{i}").items())
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    items.append((new_key, v))
            else:
                items.append((new_key, v))

        return dict(items)


class StructuredDataExtractor:
    def __init__(self):
        self.flattener = DictFlattener(sep="_")

    def regroup_flattened_data(
        self, flattened_record: Dict[str, Any]
    ) -> Dict[str, Dict]:
        grouped = defaultdict(dict)

        for key, value in flattened_record.items():
            parts = key.split("_", 1)
            if len(parts) == 2:
                prefix, rest = parts
                grouped[prefix][rest] = value
            else:
                grouped["_root"][key] = value

        return dict(grouped)

    def extract_structured_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        flattened = self.flattener.flatten(record.copy())
        regrouped = self.regroup_flattened_data(flattened)
        extracted = {
            "_id": str(record.get("_id", "N/A")),
            "label": record.get("label", {}).get("@fr", "N/A"),
            "type": record.get("type", []),  # Keep as array
            "geo": None,
            "address": None,
            "description": None,
            "contact": None,
            "price": None,
            "uuid": record.get("uuid", "N/A"),
            "uri": record.get("uri", "N/A"),
        }

        # Extract geo location from isLocatedAt
        if "isLocatedAt" in regrouped:
            location = regrouped["isLocatedAt"]
            if location.get("0_geo_latitude") and location.get("0_geo_longitude"):
                extracted["geo"] = {
                    "latitude": location.get("0_geo_latitude"),
                    "longitude": location.get("0_geo_longitude"),
                }

        # Extract address from isLocatedAt
        if "isLocatedAt" in regrouped:
            location = regrouped["isLocatedAt"]
            extracted["address"] = {
                "streetAddress": location.get("0_address_0_streetAddress"),
                "addressLocality": location.get("0_address_0_addressLocality"),
                "postalCode": location.get("0_address_0_postalCode"),
            }

        # Extract description (prefer full description over short)
        if "hasDescription" in regrouped:
            desc = regrouped["hasDescription"]
            extracted["description"] = desc.get("0_description_@fr") or desc.get(
                "0_shortDescription_@fr"
            )

        # Extract contact from hasContact
        if "hasContact" in regrouped:
            contact = regrouped["hasContact"]
            extracted["contact"] = {
                "name": contact.get("0_legalName")
                or f"{contact.get('0_givenName', '')} {contact.get('0_familyName', '')}".strip(),
                "email": contact.get("0_email"),
                "telephone": contact.get("0_telephone"),
                "homepage": contact.get("0_homepage"),
            }

        # Add randomized price for demonstration (since original data doesn't have price)
        extracted["price"] = randint(0, 100)
        return extracted

    def extract_from_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [self.extract_structured_record(record) for record in records]


class RawToCleanInserter(MongoConnection):
    def __init__(self):
        super().__init__()
        self.extractor = StructuredDataExtractor()
        self.batch_size = 1000

    def create_indexes(self):
        self.change_clean_collection()
        self.collection.create_index("uuid", unique=True)
        print(f"Indexes created on {self.collection.name}")

    def transform_and_insert_batch(self, raw_records: List[Dict[str, Any]]) -> tuple:
        if not raw_records:
            return 0, 0

        # Extract and transform records
        structured_records = self.extractor.extract_from_records(raw_records)

        # Skip insertion if no structured records
        if not structured_records:
            return 0, len(raw_records)

        self.change_clean_collection()
        try:
            result = self.collection.insert_many(structured_records, ordered=False)
            inserted_count = len(result.inserted_ids)
            duplicate_count = len(raw_records) - inserted_count
            return inserted_count, duplicate_count
        except BulkWriteError as e:
            inserted_count = e.details.get("nInserted", 0)
            duplicate_count = len(raw_records) - inserted_count
            return inserted_count, duplicate_count

    def extract_and_insert_all(self, batch_size: int = None) -> Dict[str, int]:
        if batch_size:
            self.batch_size = batch_size

        self.change_raw_collection()
        raw_collection = self.collection  # Store reference to raw collection
        total_count = raw_collection.count_documents({})

        print(f"Processing {total_count} records from {raw_collection.name}...")
        print("=" * 80)

        total_inserted = 0
        total_duplicates = 0

        # Process in batches
        for batch_num, offset in enumerate(range(0, total_count, self.batch_size)):
            batch = list(raw_collection.find().skip(offset).limit(self.batch_size))

            inserted, duplicates = self.transform_and_insert_batch(batch)

            total_inserted += inserted
            total_duplicates += duplicates

            progress = min(offset + self.batch_size, total_count)
            print(
                f"[{progress}/{total_count}] Batch {batch_num + 1}: "
                f"Inserted: {inserted}, Duplicates: {duplicates}"
            )

        print("=" * 80)
        print(f"Total records processed: {total_count}")
        print(f"Total inserted into clean: {total_inserted}")
        print(f"Total duplicates: {total_duplicates}")

        return {
            "total_processed": total_count,
            "total_inserted": total_inserted,
            "total_duplicates": total_duplicates,
        }

    def run(self, batch_size: int = None):
        try:
            self.create_indexes()
            stats = self.extract_and_insert_all(batch_size)
            print("\nTransformation completed successfully!")
            print(f"Total processed: {stats['total_processed']}")
            print(f"Total inserted: {stats['total_inserted']}")
            print(f"Total duplicates: {stats['total_duplicates']}")
            return True
        except Exception as e:
            print(f"Error during transformation: {type(e).__name__}")
            print(f"{str(e)}")
            return False
        finally:
            self.disconnect()
