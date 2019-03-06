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
1,8,1.40,20,kmeans,nan,6,0.6163,0.5482,0.5802,0.5802,0.3662,0.5799,0.5301,0.8817,0.7285,0.2691,0.1489
1,8,0.80,0,kmeans,nan,6,0.5931,0.5544,0.5731,0.5731,0.4308,0.5728,0.5667,0.8062,0.7367,0.0660,0.0492
1,7,0.60,0,kmeans,nan,6,0.5920,0.5463,0.5682,0.5682,0.3193,0.5679,0.4862,0.9935,0.6971,0.0578,0.0441
1,10,1.00,0,kmeans,nan,6,0.5907,0.5450,0.5669,0.5669,0.3186,0.5666,0.4857,0.8276,0.6966,0.0698,0.0523
1,10,1.40,0,kmeans,nan,6,0.5826,0.5384,0.5596,0.5596,0.3144,0.5593,0.4823,0.8193,0.6948,0.0983,0.0707
1,9,1.20,20,kmeans,nan,6,0.5708,0.5292,0.5492,0.5492,0.3137,0.5489,0.4809,0.8296,0.6935,0.2362,0.1358
1,8,1.20,20,kmeans,nan,6,0.5580,0.5196,0.5381,0.5381,0.3109,0.5378,0.4777,0.8019,0.6914,0.2495,0.1401
1,6,0.60,16,kmeans,nan,6,0.5562,0.5173,0.5360,0.5360,0.3063,0.5357,0.4746,0.8262,0.6898,0.2762,0.1400
1,9,1.40,12,kmeans,nan,6,0.5526,0.5145,0.5329,0.5329,0.3070,0.5325,0.4748,0.7904,0.6891,0.3238,0.1215
1,7,1.00,20,kmeans,nan,6,0.5539,0.5129,0.5326,0.5326,0.2914,0.5323,0.4648,0.8303,0.6835,0.2505,0.1428
```

### Results on abstracts

```bash
less output/plos_med_top6_eval_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,10,1.20,12,kmeans,nan,6,0.6278,0.5640,0.5942,0.5942,0.3692,0.5939,0.5306,0.8736,0.7302,0.4350,0.3180
1,10,1.60,0,kmeans,nan,6,0.6147,0.5630,0.5877,0.5877,0.4187,0.5874,0.5632,0.8719,0.7499,0.4262,0.3131
1,8,1.20,20,kmeans,nan,6,0.6147,0.5563,0.5840,0.5840,0.4204,0.5837,0.5674,0.8559,0.7487,0.4502,0.3338
1,10,1.60,16,kmeans,nan,6,0.6114,0.5587,0.5838,0.5838,0.4127,0.5835,0.5592,0.8569,0.7474,0.4757,0.3549
1,9,1.00,12,kmeans,nan,6,0.6255,0.5466,0.5834,0.5834,0.3528,0.5831,0.5253,0.8785,0.7229,0.4085,0.3156
1,5,1.00,12,kmeans,nan,6,0.6036,0.5613,0.5817,0.5817,0.4601,0.5814,0.5908,0.8377,0.7606,0.5851,0.4230
1,8,1.40,16,kmeans,nan,6,0.5895,0.5710,0.5801,0.5801,0.4372,0.5798,0.5639,0.8347,0.7515,0.5155,0.3702
1,6,1.00,16,kmeans,nan,6,0.6053,0.5534,0.5782,0.5782,0.4404,0.5779,0.5797,0.9302,0.7520,0.5168,0.3826
1,5,1.00,0,kmeans,nan,6,0.5816,0.5725,0.5770,0.5770,0.4642,0.5767,0.5813,0.8368,0.7597,0.5411,0.3723
1,7,0.80,4,kmeans,nan,6,0.5879,0.5611,0.5742,0.5742,0.3163,0.5739,0.4768,0.8213,0.6973,0.4515,0.3658
```

### Results on full texts

```bash
less output/plos_top6_eval_sgl.csv | grep ",6,0." | sort -t',' -k13 -nr | head
1,10,0.80,12,kmeans,nan,6,0.5620,0.4553,0.5030,0.5030,0.2290,0.5027,0.4513,0.9851,0.6240,0.2515,0.2446
1,10,0.60,20,kmeans,nan,6,0.5468,0.4345,0.4842,0.4842,0.2184,0.4838,0.4473,0.8550,0.6127,0.1980,0.1851
1,9,0.60,12,kmeans,nan,6,0.5114,0.4385,0.4721,0.4721,0.1914,0.4717,0.4100,0.8246,0.6378,0.2667,0.2321
1,8,0.60,20,kmeans,nan,6,0.5134,0.4353,0.4711,0.4711,0.1797,0.4707,0.4045,0.8274,0.6323,0.2344,0.2065
1,10,0.80,16,kmeans,nan,6,0.5244,0.4269,0.4707,0.4707,0.1876,0.4703,0.4190,0.9931,0.6285,0.2430,0.2032
1,8,0.60,16,kmeans,nan,6,0.5127,0.4343,0.4703,0.4703,0.1769,0.4699,0.4028,0.8224,0.6306,0.2538,0.2059
1,9,0.60,16,kmeans,nan,6,0.5115,0.4345,0.4699,0.4699,0.1817,0.4695,0.4055,0.9909,0.6332,0.2486,0.1981
1,10,1.20,20,kmeans,nan,6,0.5175,0.4219,0.4648,0.4648,0.2007,0.4644,0.4296,0.8503,0.6121,0.2569,0.1916
1,10,0.80,8,kmeans,nan,6,0.5162,0.4221,0.4645,0.4645,0.1843,0.4640,0.4157,0.8306,0.6280,0.3202,0.2421
1,10,1.00,12,kmeans,nan,6,0.5003,0.4321,0.4637,0.4637,0.1740,0.4633,0.3959,0.9868,0.6293,0.2980,0.2633
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

