# APT Malware Dataset

This project provides a parser for the dataset CSV file and converts the data into a SQL model to efficiently perform queries.

The original dataset CSV can be found here: [overview.csv](https://github.com/cyber-research/APTMalware/blob/d71ee9f29427239ba2c02de6b76807e32f769393/overview.csv)

However, an inconsistency was found for two sample hashes and their associated APT group name.

* **APT 28** was incorrectly assigned to **2 samples** that were actually attributed to **APT 29** (fixed in pull request [#2](https://github.com/cyber-research/APTMalware/pull/2))

This inconsistency was adjusted in the dataset and the URLs to the reports have been updated as well: [overview.csv](https://github.com/marius-benthin/APTMalware/blob/master/overview.csv) (updated).

To convert the CSV file into a relational model, the Python script `parser.py` can be executed.
Two environment variables are considered:

```
DATABASE_URL="mysql://username:password@localhost:3306/database?charset=utf8mb4"
DATASET_FILE="overview.csv"
```