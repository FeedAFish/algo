from src.data_clean import RawToCleanInserter
from src.raw_insert import RawDataInsert
from src.rating import RatingInserter
import random
import sys

if __name__ == "__main__":
    start_step = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    if start_step <= 1:
        inserter = RawDataInsert()
        inserter.run()

    if start_step <= 2:
        clean_inserter = RawToCleanInserter()
        clean_inserter.run()

    if start_step <= 3:
        rating_inserter = RatingInserter(seed=42)
        rating_inserter.run()

        for loop_num in range(2, 12):
            sample_percentage = random.uniform(0.3, 0.9)
            rating_inserter = RatingInserter(seed=42 + loop_num)
            rating_inserter.run_partial(sample_percentage=sample_percentage)
