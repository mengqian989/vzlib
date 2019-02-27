# Data set creation

This document explains how the data set for this project was created (on Feb 26, 2019).  Note that this data set is intended for evaluating cluster quality only; Our exploratory IR system will be using the entire PLOS archive.

## Getting data

Use query "neoplasms by site[MeSH Major Topic]" but restrict the search to PLOS journals as follows. Choose Pubmed and PMC as databases and save the resulting document sets as plos_med.xml and plos_pmc.xml, respectively.

> ("plos one"[Journal] OR "plos pathogens"[Journal] OR "plos neglected tropical diseases"[Journal] OR "plos biology"[Journal] OR "plos medicine"[Journal] OR "plos computational biology"[Journal] OR "plos genetics"[Journal]) AND "neoplasms by site"[MeSH Major Topic]

Compress the data.

```bash
gzip data/plos_med.xml
gzip data/plos_pmc.xml
```

## Deciding which classes to use 

Extract MeSH terms (as well as other textual information).

```bash
python xml2tsv_med.py --input data/plos_med.xml.gz --generalize --major --code | gzip > data/plos_med.txt.gz
```

Check to see what and how many MeSH terms are annotated.

```bash
gzcat data/plos_med.txt.gz | cut -f 4 | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
5682 Digestive System Neoplasms
2768 Breast Neoplasms
2574 Urogenital Neoplasms
2465 Thoracic Neoplasms
1681 Endocrine Gland Neoplasms
1473 Head and Neck Neoplasms
 836 Nervous System Neoplasms
 321 Skin Neoplasms
 236 Bone Neoplasms
 203 Mammary Neoplasms, Animal
 128 Eye Neoplasms
  89 Hematologic Neoplasms
  51 Abdominal Neoplasms
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
python xml2tsv_med.py --input data/plos_med.xml.gz --generalize --major --code --restrict | gzip > data/plos_med_top6.txt.gz
```

There're 12,530 articles annotated with at least one of the classes.

```bash
gzcat data/plos_med_top6.txt.gz | wc -l  
12530 
```

Here's the distribution of the classes. 

```bash
gzcat data/plos_med_top6.txt | cut -f 4  | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
4416 Digestive System Neoplasms
2647 Breast Neoplasms
2313 Urogenital Neoplasms
1770 Thoracic Neoplasms
1516 Endocrine Gland Neoplasms
1413 Head and Neck Neoplasms
```

Note that the numbers are different from plos_med.txt because duplicates have been eliminated in creating plos_med_top6.txt.  If we look at the number of lines (articles), they're the same.

```bash
less plos_med.txt | grep "Digestive System Neoplasms" | wc -l
4416
less plos_med_top6.txt | grep "Digestive System Neoplasms" | wc -l
4416
```

## Adding full-text data (body text)

Finally create the data set with full text by adding body text extracted from plos_pmc.xml.

```bash
python xml2tsv_pmc.py --input data/plos_pmc.xml.gz --med data/plos_med_top6.txt.gz | gzip > data/plos_top6.txt.gz
```

Count the number of articles to make sure it didn't change.

```bash
gzcat data/plos_top6.txt.gz | wc -l
   12465
```

## Format

The resulting file, plos_top6.txt, has the following format.

> PMID  Title  Abstract  Body_text  MeSH_terms

The fields are tab-delimted.  If an article is annotated with multiple MeSH terms, the MeSH terms are concatanated with a vertical bar in between (e.g., "MeSH_A|MeSH_B").  The following shows an example article.

> 17951913  Systemic chemotherapy and...  We report a case of...  Choroidal metastases occur most frequently...  Breast Neoplasms, Male
 
## Experiments

```bash
nice python eval.py --input data/plos_med_top6.txt.gz --output data/plos_med_top6_eval_sgl.csv -k 6 --single > log_sgl.txt &
```
