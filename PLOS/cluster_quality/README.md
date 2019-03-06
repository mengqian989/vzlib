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

Run experiment on abstracts and full texts.

```bash
nice python eval.py --input data/plos_top6.txt.gz --output output/plos_med_top6_eval_title_sgl.csv -k 6 -f title --single --format full > log_med_title_sgl.txt &
nice python eval.py --input data/plos_top6.txt.gz --output output/plos_med_top6_eval_sgl.csv -k 6 -f "title,abstract" --single --format full > log_med_sgl.txt &
nice python eval.py --input data/plos_top6.txt.gz --output output/plos_top6_eval_sgl.csv -k 6 -t 0 --single --format full > log_sgl.txt & 
```

### Results on titles

```bash
less output/plos_med_top6_eval_title_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,8,1.40,20,kmeans,nan,6,0.6186,0.5500,0.5823,0.5823,0.3667,0.5820,0.5306,0.8768,0.7290,0.2688,0.1492
1,9,1.40,0,kmeans,nan,6,0.5832,0.5394,0.5604,0.5604,0.3155,0.5601,0.4830,0.8166,0.6949,0.1096,0.0781
1,10,0.80,0,kmeans,nan,6,0.5806,0.5388,0.5589,0.5589,0.4028,0.5586,0.5491,0.8990,0.7375,0.0549,0.0458
1,9,1.60,16,kmeans,nan,6,0.5756,0.5353,0.5547,0.5547,0.4052,0.5544,0.5485,0.8954,0.7277,0.2917,0.1572
1,10,1.20,0,kmeans,nan,6,0.5486,0.5424,0.5455,0.5455,0.3931,0.5452,0.5250,0.7676,0.7025,0.0786,0.0617
1,8,1.20,0,kmeans,nan,6,0.5655,0.5244,0.5442,0.5442,0.3110,0.5438,0.4788,0.8089,0.6923,0.1174,0.0836
1,6,0.60,16,kmeans,nan,6,0.5625,0.5214,0.5412,0.5412,0.3038,0.5408,0.4737,0.9724,0.6892,0.2761,0.1419
1,7,1.00,0,kmeans,nan,6,0.5576,0.5148,0.5354,0.5354,0.2925,0.5351,0.4662,0.8043,0.6843,0.1309,0.0920
1,10,1.00,0,kmeans,nan,6,0.5375,0.5276,0.5325,0.5325,0.3471,0.5322,0.4921,0.7222,0.6960,0.0721,0.0524
1,6,0.60,12,kmeans,nan,6,0.5527,0.5127,0.5319,0.5319,0.2995,0.5316,0.4702,0.8312,0.6870,0.3124,0.1104
```

### Results on abstracts

```bash
less output/plos_med_top6_eval_sgl.csv | grep -v "^1,6,0" | grep ",6,0." | sort -t',' -k13 -nr | head
1,7,1.20,8,maximin,0.80,6,0.5815,0.6199,0.6001,0.6001,0.5587,0.5998,0.6461,0.7644,0.8092,0.7734,0.3988
1,10,1.20,20,kmeans,nan,6,0.6272,0.5530,0.5878,0.5878,0.3684,0.5875,0.5348,0.8749,0.7291,0.3607,0.3063
1,7,1.00,12,kmeans,nan,6,0.6072,0.5573,0.5812,0.5812,0.3915,0.5809,0.5421,0.8522,0.7367,0.4800,0.3407
1,8,1.00,20,kmeans,nan,6,0.6149,0.5506,0.5810,0.5810,0.3543,0.5806,0.5203,0.8778,0.7228,0.3864,0.3246
1,8,1.40,16,kmeans,nan,6,0.5958,0.5587,0.5767,0.5767,0.4301,0.5764,0.5662,0.8364,0.7526,0.5098,0.3736
1,7,0.80,20,kmeans,nan,6,0.5781,0.5750,0.5766,0.5766,0.3861,0.5763,0.5183,0.8304,0.7269,0.3629,0.3008
1,9,1.20,4,kmeans,nan,6,0.5856,0.5645,0.5748,0.5748,0.3486,0.5745,0.4980,0.8150,0.7047,0.4671,0.3710
1,8,0.80,20,kmeans,nan,6,0.6130,0.5368,0.5724,0.5724,0.3191,0.5721,0.4997,0.8773,0.7085,0.3388,0.3086
1,7,0.80,4,kmeans,nan,6,0.5849,0.5581,0.5712,0.5712,0.3148,0.5709,0.4757,0.8202,0.6972,0.4469,0.3607
1,8,1.00,4,kmeans,nan,6,0.5819,0.5571,0.5692,0.5692,0.3238,0.5689,0.4813,0.9871,0.6977,0.4484,0.3719
```

### Results on full texts

```bash
less output/plos_top6_eval_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,10,1.00,8,maximin,0.90,6,0.5803,0.6160,0.5976,0.5976,0.5645,0.5974,0.6510,0.7530,0.7989,0.5605,0.2805
1,10,0.80,8,maximin,0.99,6,0.5046,0.5021,0.5033,0.5033,0.3918,0.5030,0.5225,0.7769,0.7460,0.5134,0.2422
1,10,0.80,16,kmeans,nan,6,0.5591,0.4500,0.4987,0.4987,0.2244,0.4983,0.4493,0.8619,0.6206,0.2382,0.2033
1,10,0.60,20,kmeans,nan,6,0.5468,0.4345,0.4842,0.4842,0.2184,0.4838,0.4473,0.8550,0.6127,0.1980,0.1851
1,7,0.60,20,kmeans,nan,6,0.5456,0.4335,0.4831,0.4831,0.2044,0.4827,0.4377,0.8597,0.6099,0.2199,0.2086
1,7,0.80,8,maximin,0.99,6,0.4618,0.4891,0.4751,0.4751,0.4245,0.4747,0.5380,0.8079,0.7171,0.5389,0.2693
1,9,0.60,12,kmeans,nan,6,0.5114,0.4385,0.4721,0.4721,0.1914,0.4717,0.4100,0.8246,0.6378,0.2667,0.2321
1,10,0.80,12,kmeans,nan,6,0.5247,0.4291,0.4721,0.4721,0.1897,0.4717,0.4196,0.8336,0.6308,0.2654,0.2447
1,8,0.60,20,kmeans,nan,6,0.5134,0.4353,0.4711,0.4711,0.1797,0.4707,0.4045,0.8274,0.6323,0.2344,0.2065
1,8,1.00,8,maximin,0.80,6,0.4708,0.4700,0.4704,0.4704,0.3519,0.4700,0.4925,0.6732,0.6925,0.5876,0.2712
```

## Obsolete

### Results on titles

```bash
less data/plos_med_top6_eval_title_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,7,1.00,0,kmeans,nan,6,0.6786,0.4959,0.5731,0.5731,0.2846,0.5721,0.4646,0.8561,0.6408,0.1305,-0.0035
1,6,0.90,16,kmeans,nan,6,0.6367,0.4692,0.5402,0.5402,0.2212,0.5392,0.4171,0.8476,0.6171,0.3161,0.0604
1,10,0.50,0,kmeans,nan,6,0.6100,0.4683,0.5298,0.5298,0.3139,0.5288,0.4760,0.7755,0.6474,0.0390,-0.0000
1,7,0.50,20,kmeans,nan,6,0.6137,0.4652,0.5292,0.5292,0.3053,0.5282,0.4724,0.9078,0.6411,0.1982,-0.0307
1,5,0.90,4,kmeans,nan,6,0.5747,0.4851,0.5261,0.5261,0.3710,0.5248,0.5229,0.7566,0.6588,0.8927,-0.7455
1,5,0.90,0,spectral,nan,6,0.5867,0.4762,0.5257,0.5257,0.4292,0.5244,0.5731,0.2839,0.6536,0.9855,-0.5769
1,5,0.90,0,kmeans,nan,6,0.5850,0.4752,0.5244,0.5244,0.4280,0.5231,0.5720,0.7554,0.6530,0.9861,-0.5769
1,6,0.60,20,kmeans,nan,6,0.5936,0.4672,0.5229,0.5229,0.3231,0.5219,0.4771,0.7607,0.6476,0.2351,-0.0026
1,5,0.90,0,maximin,0.80,6,0.5825,0.4730,0.5221,0.5221,0.4272,0.5207,0.5715,0.7696,0.6526,0.9834,-0.5769
1,6,0.80,20,maximin,0.99,7,0.5440,0.4961,0.5189,0.5189,0.4097,0.5178,0.5170,0.7051,0.6432,0.2889,0.0215
```

### Results on abstracts

```bash
less data/plos_med_top6_eval_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | grep -v maximin | head
1,5,1.00,16,kmeans,nan,6,0.7481,0.6328,0.6856,0.6856,0.5398,0.6849,0.6392,0.9773,0.7479,0.6054,0.5247
1,5,1.00,0,kmeans,nan,6,0.7477,0.6324,0.6852,0.6852,0.5388,0.6845,0.6385,0.8416,0.7478,0.5936,0.4974
1,5,0.90,0,kmeans,nan,6,0.7423,0.6226,0.6772,0.6772,0.5197,0.6765,0.6245,0.8424,0.7406,0.5719,0.4743
1,6,1.00,0,kmeans,nan,6,0.7312,0.6253,0.6741,0.6741,0.5420,0.6734,0.6373,0.8056,0.7503,0.5563,0.4431
1,5,1.00,8,spectral,nan,6,0.7474,0.5965,0.6635,0.6635,0.4939,0.6627,0.6162,0.8614,0.7414,0.6521,0.5395
1,5,1.00,8,kmeans,nan,6,0.7198,0.6136,0.6624,0.6624,0.5221,0.6617,0.6235,0.8007,0.7373,0.6580,0.5395
1,5,1.00,12,kmeans,nan,6,0.7181,0.6107,0.6601,0.6601,0.5161,0.6593,0.6193,0.8088,0.7336,0.6301,0.5086
1,5,0.90,12,spectral,nan,6,0.7451,0.5893,0.6581,0.6581,0.4789,0.6573,0.6059,0.8626,0.7351,0.5995,0.4785
1,5,0.90,8,spectral,nan,6,0.7427,0.5868,0.6556,0.6556,0.4755,0.6548,0.6035,0.8617,0.7336,0.6058,0.4485
1,5,0.90,16,spectral,nan,6,0.7427,0.5861,0.6552,0.6552,0.4756,0.6544,0.6038,0.8623,0.7334,0.5797,0.5078
```

### Results on full texts

```bash
less data/plos_top6_eval_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,10,0.60,20,kmeans,nan,6,0.5468,0.4345,0.4842,0.4842,0.2184,0.4838,0.4473,0.8550,0.6127,0.1980,0.1851
1,10,0.80,12,kmeans,nan,6,0.5203,0.4485,0.4817,0.4817,0.1963,0.4813,0.4125,0.8270,0.6414,0.2806,0.2447
1,10,0.80,16,kmeans,nan,6,0.5203,0.4468,0.4808,0.4808,0.1948,0.4804,0.4122,0.8256,0.6403,0.2641,0.2033
1,10,0.90,0,kmeans,nan,6,0.5230,0.4329,0.4737,0.4737,0.1984,0.4733,0.4231,0.8282,0.6381,0.1699,0.1309
1,9,0.60,12,kmeans,nan,6,0.5114,0.4385,0.4721,0.4721,0.1914,0.4717,0.4100,0.8246,0.6378,0.2667,0.2321
1,8,0.60,20,kmeans,nan,6,0.5134,0.4353,0.4711,0.4711,0.1797,0.4707,0.4045,0.8274,0.6323,0.2344,0.2065
1,8,0.60,16,kmeans,nan,6,0.5127,0.4343,0.4703,0.4703,0.1769,0.4699,0.4028,0.8224,0.6306,0.2538,0.2059
1,9,0.60,16,kmeans,nan,6,0.5115,0.4345,0.4699,0.4699,0.1817,0.4695,0.4055,0.9909,0.6332,0.2486,0.1981
1,10,0.90,16,kmeans,nan,6,0.5080,0.4351,0.4687,0.4687,0.1765,0.4683,0.3998,0.8251,0.6310,0.2701,0.2099
1,9,1.00,0,kmeans,nan,6,0.4985,0.4406,0.4678,0.4678,0.2042,0.4674,0.4119,0.8085,0.6448,0.2093,0.1528
```

