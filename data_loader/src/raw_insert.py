import json
from pathlib import Path
from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from .mongo import MongoConnection


class RawDataInsert(MongoConnection):
    def __init__(self):
        super().__init__()
        self.data_dir = self._get_data_directory()
        self.inserted_count = 0
        self.error_count = 0
        self.duplicate_count = 0

    def _get_data_directory(self) -> Path:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        data_dir = project_root / "data_lake"

        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        return data_dir

    def read_ndjson_file(self, file_path: Path) -> List[Dict[str, Any]]:
        records = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num} in {file_path.name}: {e}")
                        self.error_count += 1
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            self.error_count += 1

        return records

    def insert_records(self, records: List[Dict[str, Any]]) -> tuple:
        if not records:
            return (0, 0)

        self.change_raw_collection()

        inserted = 0
        duplicates = 0

        try:
            if len(records) == 1:
                self.collection.insert_one(records[0])
                self.inserted_count += 1
                inserted = 1
            else:
                result = self.collection.insert_many(records, ordered=False)
                count = len(result.inserted_ids)
                self.inserted_count += count
                inserted = count
        except BulkWriteError as e:
            inserted = e.details.get("nInserted", 0)
            self.inserted_count += inserted

            for error in e.details.get("writeErrors", []):
                if error.get("code") == 11000:  # Duplicate key error code
                    duplicates += 1

            self.duplicate_count += duplicates
            return (inserted, duplicates)
        except Exception as e:
            print(f"Error inserting records: {e}")
            self.error_count += len(records)
            return (0, 0)

        return (inserted, duplicates)

    def insert_from_ndjson_file(self, file_path: Path) -> int:
        print(f"Processing {file_path.name}...")
        records = self.read_ndjson_file(file_path)

        if not records:
            print(f"No valid records found")
            return 0

        inserted, duplicates = self.insert_records(records)
        print(f"Inserted {inserted}/{len(records)} records")
        if duplicates > 0:
            print(f"({duplicates} duplicates skipped)")

        return inserted

    def create_indexes(self) -> None:
        self.change_raw_collection()
        try:
            self.collection.create_index("uuid", unique=True)
            print("Created unique index on 'uuid'")
        except Exception as e:
            print(f"Error creating indexes: {e}")

    def insert_all_ndjson_files(self) -> Dict[str, Any]:
        ndjson_files = sorted(self.data_dir.glob("*.ndjson"))

        if not ndjson_files:
            print(f"No NDJSON files found in {self.data_dir}")
            return {
                "total_files": 0,
                "total_inserted": 0,
                "total_duplicates": 0,
                "total_errors": 0,
            }

        print(f"Found {len(ndjson_files)} NDJSON files")
        print("=" * 50)

        self.inserted_count = 0
        self.error_count = 0
        self.duplicate_count = 0

        for file_path in ndjson_files:
            self.insert_from_ndjson_file(file_path)

        print("=" * 50)
        print(f"Insertion complete!")
        print(f"Total inserted: {self.inserted_count}")
        print(f"Total duplicates: {self.duplicate_count}")
        print(f"Total errors: {self.error_count}")

        return {
            "total_files": len(ndjson_files),
            "total_inserted": self.inserted_count,
            "total_duplicates": self.duplicate_count,
            "total_errors": self.error_count,
        }

    def run(self) -> bool:
        try:
            self.create_indexes()
            stats = self.insert_all_ndjson_files()

            print("\n" + "=" * 50)
            print(f"  Files processed: {stats['total_files']}")
            print(f"  Records inserted: {stats['total_inserted']}")
            print(f"  Duplicates skipped: {stats['total_duplicates']}")
            print(f"  Errors: {stats['total_errors']}")

            self.disconnect()
            return True
        except FileNotFoundError as e:
            print(f"✗ {e}")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
