# APTClass Dataset

This module provides a parser for the dataset CSV file and converts the data into a SQL model to efficiently perform queries.
In order to be able to reproduce the numbers described in the paper for the single-authorship attributed samples, the following panda filter rule was proposed by the researchers.

**Note:** APTClass considers different aliases of the same APT group as separate labels! 

```python
import pandas

df = pandas.read_csv('2021-jan-aptclass_dataset.csv', sep='|', encoding='utf-8')
df = df[~df['apt_country'].str.contains('unknown')]
df = df[~df['apt_country'].str.contains(',')]
df = df[~df['apt_country'].str.contains('no_linked_nation')]
df = df[~df['apt_name'].str.contains('unknown')]

# this filter rule also removes rows containing multiple aliases of the same APT group
df = df[~df['apt_name'].str.contains(',')]

samples, groups, countries = 0, set(), set()
for df_tuple in df.itertuples():
    samples += 1
    groups.add(df_tuple.apt_name)
    countries.add(df_tuple.apt_country)

print("Total labeled Samples:", samples)
print("Number of groups:", len(groups))
print("Number of countries:", len(countries))
```
```
Total labeled Samples:  15660
Number of groups:       164
Number of countries:    18
```

However, after consultation with the authors, it was determined that additional filtering rules were necessary to obtain samples with unique attribution.
In addition, the following countries need to be removed as they are ambiguous.

```python
df = df[~df['apt_country'].str.contains('Iran Israel')]
df = df[~df['apt_country'].str.contains('North Korea South Korea')]
df = df[~df['apt_country'].str.contains('NATO')]
df = df[~df['apt_country'].str.contains('China Iran')]
df = df[~df['apt_country'].str.contains('Russia Ukraine')]
```
```
Total labeled Samples:  15379
Number of groups:       156
Number of countries:    13
```

Furthermore, some inconsistencies between the sample hashes and the annotated APT group names have been discovered.

* **SIG17** was incorrectly assigned to **4245 samples** that were actually attributed to other SIG clusters in the report |
**Note:** The countries of three of 19 newly added SIG clusters could be determined using [Malpedia](https://malpedia.caad.fkie.fraunhofer.de)

* **Trident** was incorrectly assigned to **4 samples** that were actually attributed to **APT 29** in the report
* Actor **8** was incorrectly assigned to **13 samples** that were not clearly attributed to a known threat actor
* **APT 29** was incorrectly assigned to **3 samples** that were not clearly attributed to a threat actor

These inconsistencies were adjusted in a copy of the dataset `2022-aug-aptclass_dataset.csv` and according to the filtering criteria already mentioned above, the numbers update as follows.

```
Total labeled Samples:  11830
Number of groups:       158
Number of countries:    14
```

To convert the CSV file into a relational model, the Python script `parser.py` can be executed.
Three environment variables are considered, where `ALIAS_AWARE` specifies whether aliases of APT groups should be treated as separate threat actors.

```
DATABASE_URL="mysql://username:password@localhost:3306/database?charset=utf8mb4"
DATASET_FILE="2022-aug-aptclass_dataset.csv"
ALIAS_AWARE=True
```