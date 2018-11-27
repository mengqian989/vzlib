# Data set creation

This document explains how the data set for this project was created (on Sep 15, 2018).

## Getting data

Get plos abstracts for "neoplasms by site[MeSH Major Topic]" and save as
plos_med.xml and plos_pmc.xml using the following query on Pubmed and PMC, respectively.

> ("plos one"[Journal] OR "plos pathogens"[Journal] OR "plos neglected tropical diseases"[Journal] OR "plos biology"[Journal] OR "plos medicine"[Journal] OR "plos computational biology"[Journal] OR "plos genetics"[Journal]) AND "neoplasms by site"[MeSH Major Topic]

Compress the data.

```bash
gzip data/plos_med.xml
gzip data/plos_pmc.xml
```

## Deciding classes to use 

Extract MeSH terms (as well as other textual information).

```bash
python xml2tsv_med.py --input data/plos_med.xml.gz --generalize --major --code > data/plos_med.txt
```

Check to see what and how many MeSH terms are annotated.

```bash
cut -f 4 plos_med.txt | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
   5561 Digestive System Neoplasms
   2700 Breast Neoplasms
   2512 Urogenital Neoplasms
   2407 Thoracic Neoplasms
   1645 Endocrine Gland Neoplasms
   1411 Head and Neck Neoplasms
    813 Nervous System Neoplasms
    312 Skin Neoplasms
    232 Bone Neoplasms
    198 Mammary Neoplasms, Animal
    128 Eye Neoplasms
     85 Hematologic Neoplasms
     50 Abdominal Neoplasms
     35 Soft Tissue Neoplasms
     13 Pelvic Neoplasms
      9 Splenic Neoplasms
```

## Extracting data

Use only top 6 frequent MeSH (by specifying the classes in xml2tsv_med.py).

> classes = {"Digestive System Neoplasms",
>            "Breast Neoplasms",
>            "Urogenital Neoplasms",
>            "Thoracic Neoplasms",
>            "Endocrine Gland Neoplasms",
>            "Head and Neck Neoplasms"}

Run xml2tsv_med.py again with the following options.

```bash
python xml2tsv_med.py --input data/plos_med.xml.gz --generalize --major --code --restrict > data/plos_med_top6.txt
```

There're 12,244 articles annotated with at least one of the classes.

```bash
cd data
wc -l plos_med_top6.txt 
12244 plos_med_top6.txt
```

Here's the distribution of the classes. 

```bash
cut -f 4 plos_med_top6.txt | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr | less
   4321 Digestive System Neoplasms
   2582 Breast Neoplasms
   2261 Urogenital Neoplasms
   1736 Thoracic Neoplasms
   1488 Endocrine Gland Neoplasms
   1367 Head and Neck Neoplasms
```

Note that the numbers are different from plos_med.txt because duplicates have been eliminated in creating plos_med_top6.txt.  If we look at the number of lines (articles), they're the same.

```bash
less plos_med.txt | grep "Digestive System Neoplasms" | wc -l
4321
less plos_med_top6.txt | grep "Digestive System Neoplasms" | wc -l
4321
```

## Adding full-text data (body text)

Finally create the data set with full text by adding body text extracted from plos_pmc.xml.

```bash
cd ..
python xml2tsv_pmc.py --input data/plos_pmc.xml.gz --med data/plos_med_top6.txt > data/plos_top6.txt
```

Count the number of articles to make sure it didn't change.

```bash
wc -l data/plos_top6.txt
12244 data/plos_top6.txt
```

## Format

The resulting file, plos_top6.txt, has the following format.

> PMID  Title  Abstract  Body_text  MeSH_terms

The fields are tab-delimted.  If an article is annotated with multiple MeSH terms, the MeSH terms are concatanated with a vertical bar in between (e.g., "MeSH_A|MeSH_B").  The following shows an example article.

> 17951913  Systemic chemotherapy and...  We report a case of...  Choroidal metastases occur most frequently...  Breast Neoplasms, Male
 
