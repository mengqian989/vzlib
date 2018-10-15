# Data preparation

Got articles for the query "breast neoplasms[MeSH Major Topic]" from pubmed on September 21, 2018 and save as brca_med.xml.  
- Retrieved 224,940 articles.  

Did the same for pmc (as pmc doesn't give mesh terms) and save as brca_pmc.xml. 
- Retrieved 39,332 articles.

Look at the mesh term distribution. Note that only major mesh terms are considered (--major) and mesh terms are generalized (--generalize) up to a level specified by **target_mesh** variable in xml2tsv_med.py. 

```bash
$ python xml2tsv_med.py --input data/brca_med.xml.gz --generalize --major --code > brca_med.txt
$ cut -f 4 brca_med.txt | perl -npe 's/\|/\n/g' | sort | uniq -c | sort -nr | less
  11115 Carcinoma, Ductal, Breast
   3475 Carcinoma, Lobular
   2588 Triple Negative Breast Neoplasms
   1955 Breast Neoplasms, Male
    342 Inflammatory Breast Neoplasms
    155 Hereditary Breast and Ovarian Cancer Syndrome
    100 Unilateral Breast Neoplasms
     61 Breast Carcinoma In Situ
```

Use only top 4 frequent MeSH. (Specify the following in extract.py.)

> classes = {"Carcinoma, Ductal, Breast",
>            "Carcinoma, Lobular",
>            "Triple Negative Breast Neoplasms",
>            "Breast Neoplasms, Male"}

Run extract.py again.  (Later found that --major doesn't make difference since there were not MeSH terms under the top four MeSH terms in the MeSH tree.  So, --major and --code may be omitted.)

```bash
$ python xml2tsv_med.py --input data/brca_med.xml.gz --generalize --major --code --restrict > brca_med_top4.txt
```

This results in 16,576 articles annotated with at least one of the four mesh terms.

```bash
$ wc -l brca_med_top4.txt 
16576 brca_med_top4.txt
```

Make sure the distribution of the classes is the same as the above but only top four terms.

```bash
$ cut -f 4 brca_med_top4.txt | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
  11115 Carcinoma, Ductal, Breast
   3475 Carcinoma, Lobular
   2588 Triple Negative Breast Neoplasms
   1955 Breast Neoplasms, Male
```

Finally create the data set with full text by adding body text extracted from plos_pmc.xml.

```bash
$ python xml2tsv_pmc.py > brca_pmc_top4.txt
```

Count the number of articles and look at the distribution of classes.

```bash
$ wc -l brca_pmc_top4.txt
1932 brca_pmc_top4.txt

$ cut -f 5 brca_pmc_top4.txt | perl -npe 's/\|/\n/g' | sort | uniq -c | sort -nr
    935 Carcinoma, Ductal, Breast
    824 Triple Negative Breast Neoplasms
    290 Carcinoma, Lobular
    141 Breast Neoplasms, Male
```

# Experiments

Run an evaluation script for full text. Different combinations of parameters are executed.

```bash
$ python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_all.csv
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order.

> r, d, n, alg, k, c, h, vd, v, ai, fms

r and d are VCGS's parameters, n is the number of dimensions (components) for SVD, alg is an clustering algorithm (kmeans or maximin), k is the number of clusters, and the rest are evaluation measures: c = completeness, h = homogeneity, vd = v-measure-a, v = v-measure-b, ai = adjusted rand index, and fms = Fowlkes-Mallows index. 

v-measure-a and v-measure-b are different in how to treat multi-label cases.  The former treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.

Let's look at the five best parameter combinations based on adjusted rand index (ai).

```bash
$ less brca_top4_eval_all.csv | sort -t',' -k10 -nr | head -5
8,0.08,6,kmeans,6,0.2992,0.2900,0.2946,0.2738,0.3068,0.5642
8,0.08,2,kmeans,2,0.4177,0.2541,0.3159,0.2950,0.3057,0.6001
8,0.08,10,kmeans,4,0.3302,0.2624,0.2924,0.2698,0.2899,0.5697
8,0.08,6,kmeans,4,0.3329,0.2677,0.2968,0.2745,0.2875,0.5680
8,0.08,8,kmeans,4,0.3284,0.2618,0.2913,0.2681,0.2858,0.5667
```

Evaluation for title + abstract.

```bash
$ python eval.py --input brca_pmc_top4.txt.gz --fields title,abstract --output brca_top4_eval_ta.csv
$ less brca_top4_eval_ta.csv | sort -t',' -k10 -nr | head -5
8,0.01,2,kmeans,2,0.3847,0.2330,0.2902,0.2682,0.2778,0.5855
8,0.08,2,kmeans,2,0.3866,0.2335,0.2912,0.2691,0.2753,0.5849
8,0.27,2,kmeans,2,0.3973,0.2355,0.2957,0.2729,0.2698,0.5877
8,0.21,2,kmeans,2,0.3940,0.2338,0.2935,0.2695,0.2689,0.5868
8,0.34,2,kmeans,2,0.4022,0.2352,0.2968,0.2754,0.2641,0.5882
```

Evaluation for title.

```bash
$ python eval.py --input brca_pmc_top4.txt.gz --fields title --output brca_top4_eval_t.csv
$ less brca_top4_eval_t.csv | sort -t',' -k10 -nr | head -5
8,0.08,2,maximin,2,0.3069,0.1789,0.2260,0.2033,0.2185,0.5542
8,0.01,2,maximin,2,0.3041,0.1769,0.2237,0.2015,0.2163,0.5532
8,0.14,2,maximin,2,0.3062,0.1768,0.2242,0.2016,0.2135,0.5531
8,0.21,2,maximin,2,0.2976,0.1723,0.2182,0.1961,0.2095,0.5504
8,0.27,2,maximin,2,0.2948,0.1665,0.2128,0.1911,0.1940,0.5462
```



Since this is a controlled experiment and we know there're four classes in advance, it would be more appropriate to compare the three cases above only for four clusters (i.e., set k=4 for kmeans).

```bash
$ less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k10 -nr | head -5
8,0.08,10,kmeans,4,0.3302,0.2624,0.2924,0.2698,0.2899,0.5697
8,0.08,6,kmeans,4,0.3329,0.2677,0.2968,0.2745,0.2875,0.5680
8,0.08,8,kmeans,4,0.3284,0.2618,0.2913,0.2681,0.2858,0.5667
8,0.08,16,kmeans,4,0.3355,0.2563,0.2906,0.2678,0.2553,0.5604
8,0.08,20,kmeans,4,0.3390,0.2589,0.2936,0.2704,0.2537,0.5605

$ less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k10 -nr | head -5
8,0.08,0,kmeans,4,0.3352,0.3164,0.3255,0.2991,0.2259,0.5168
8,0.01,14,kmeans,4,0.3154,0.2945,0.3046,0.2822,0.2225,0.5134
8,0.08,16,kmeans,4,0.3069,0.2888,0.2976,0.2745,0.2181,0.5079
8,0.01,18,kmeans,4,0.3065,0.2876,0.2967,0.2739,0.2159,0.5083
8,0.01,12,kmeans,4,0.3116,0.2903,0.3006,0.2788,0.2100,0.5075

less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k10 -nr | head -5
8,0.21,6,maximin,4,0.1717,0.1874,0.1792,0.1628,0.1847,0.4508
8,0.14,6,maximin,4,0.1679,0.1839,0.1755,0.1595,0.1825,0.4485
8,0.40,20,kmeans,4,0.2497,0.2310,0.2400,0.2248,0.1605,0.4906
8,0.53,8,maximin,4,0.1131,0.1269,0.1196,0.1137,0.1212,0.4018
8,0.21,10,maximin,4,0.1211,0.1363,0.1283,0.1190,0.1210,0.4018
```

What if we look at v-measure-a?

```bash
$ less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k8 -nr | head -5
8,0.27,20,kmeans,4,0.3641,0.2855,0.3200,0.2912,0.2182,0.5492
8,0.40,8,kmeans,4,0.3546,0.2869,0.3172,0.2902,0.2454,0.5553
8,0.47,12,kmeans,4,0.3439,0.2908,0.3151,0.2922,0.1767,0.5201
8,0.34,10,kmeans,4,0.3518,0.2831,0.3137,0.2838,0.2416,0.5538
8,0.21,4,kmeans,4,0.3489,0.2832,0.3127,0.2849,0.2513,0.5571

$ less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k8 -nr | head -5
8,0.08,0,kmeans,4,0.3352,0.3164,0.3255,0.2991,0.2259,0.5168
8,0.21,16,kmeans,4,0.3167,0.3038,0.3101,0.2846,0.1982,0.4964
8,0.21,20,kmeans,4,0.3162,0.3038,0.3099,0.2847,0.2041,0.4986
8,0.60,20,kmeans,4,0.3069,0.3126,0.3097,0.2831,0.1920,0.4768
8,0.60,18,kmeans,4,0.3055,0.3120,0.3087,0.2831,0.1922,0.4771

$ less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k8 -nr | head -5
8,0.40,20,kmeans,4,0.2497,0.2310,0.2400,0.2248,0.1605,0.4906
8,0.53,14,kmeans,4,0.2303,0.2376,0.2339,0.2146,0.0885,0.4227
8,0.53,10,kmeans,4,0.2290,0.2362,0.2325,0.2137,0.0863,0.4211
8,0.14,0,kmeans,4,0.2213,0.2091,0.2151,0.1963,0.1136,0.4501
8,0.14,14,kmeans,4,0.2164,0.2056,0.2108,0.1920,0.1109,0.4460
```

Evaluation for medline data.

**The following will be updated soon**

```bash
$ python eval.py --input brca_med_top4.txt.gz --fields title --output brca_med_top4_eval.csv

$ less brca_med_top4_eval.csv | sort -t',' -k9 -nr | head -3
9,0.21,18,6,0.3308,0.2908,0.3095,0.2667,0.2636,0.6121
9,0.14,10,4,0.3748,0.2579,0.3056,0.2758,0.2567,0.6323
9,0.14,20,4,0.4014,0.2640,0.3185,0.2866,0.2515,0.6359

$ less brca_med_top4_eval.csv | grep ",4,0." | sort -t',' -k9 -nr | head -3
9,0.14,10,4,0.3748,0.2579,0.3056,0.2758,0.2567,0.6323
9,0.14,20,4,0.4014,0.2640,0.3185,0.2866,0.2515,0.6359
9,0.53,6,4,0.4033,0.2599,0.3161,0.2854,0.2479,0.6403

$ less brca_med_top4_eval.csv | grep ",4,0." | sort -t',' -k7 -nr | head -3
9,0.14,20,4,0.4014,0.2640,0.3185,0.2866,0.2515,0.6359
8,0.34,16,4,0.3374,0.2984,0.3167,0.2824,0.2303,0.5724
9,0.53,6,4,0.4033,0.2599,0.3161,0.2854,0.2479,0.6403


```
