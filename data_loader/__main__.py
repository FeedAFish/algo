from src.data_clean import RawToCleanInserter
from src.raw_insert import RawDataInsert

if __name__ == "__main__":
    inserter = RawDataInsert()
    success = inserter.run()

    inserter = RawToCleanInserter()
    success = inserter.run()
