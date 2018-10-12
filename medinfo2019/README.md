# Data preparation

Got articles for the query "breast neoplasms[MeSH Major Topic]" from pubmed on September 21, 2018 and save as brca_med.xml.  
- Retrieved 224,940 articles.  

Did the same for pmc (as pmc doesn't give mesh terms) and save as brca_pmc.xml. 
- Retrieved 39,332 articles.

Look at the mesh term distribution. Note that only major mesh terms are considered (--major) and mesh terms are generalized (--generalize).

``` 
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

Run extract.py again.

```
$ python xml2tsv_med.py --input data/brca_med.xml.gz --generalize --major --code --restrict > brca_med_top4.txt
```

This results in 16576 articles annotated with at least one of the four mesh terms.

```
$ wc -l brca_med_top4.txt 
16576 brca_med_top4.txt
```

Make sure the distribution of the classes is the same as the above but only top four terms.

```
$ cut -f 4 brca_med_top4.txt | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
  11115 Carcinoma, Ductal, Breast
   3475 Carcinoma, Lobular
   2588 Triple Negative Breast Neoplasms
   1955 Breast Neoplasms, Male
```

Finally create the data set with full text by adding body text extracted from plos_pmc.xml.

```
$ python xml2tsv_pmc.py > brca_pmc_top4.txt
```

Count the number of articles and look at the distribution of classes.

```
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

```
$ python eval.py --input brca_pmc_top4.txt --output brca_top4_eval_all.csv
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order.

> r, d, n, k, c, h, vd, v, ai, fms

r and d are VCGS's parameters, n is the number of dimensions (components) for SVD, k is for k-means, and the rest are cluster qualities: c = completeness, h = homogeneity, vd = v-measure-a, v = v-measure-b, ai = adjusted rand index, and fms = Fowlkes-Mallows index. 

v-measure-a and v-measure-b are different in how to treat multi-label cases.  The former treats treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.

Let's look at the five best parameter settings for adjusted rand index (ai).

```
$ less brca_top4_eval_all.csv | sort -t',' -k9 -nr | head -5
8,0.08,6,4,0.3579,0.2875,0.3189,0.2936,0.3180,0.5853
8,0.08,6,6,0.3043,0.2956,0.2999,0.2786,0.3142,0.5681
8,0.08,2,2,0.4161,0.2530,0.3147,0.2942,0.3053,0.6001
8,0.08,14,4,0.3366,0.2806,0.3060,0.2814,0.2973,0.5684
8,0.08,10,6,0.2976,0.2697,0.2830,0.2604,0.2907,0.5602
```

Evaluation for title + abstract.

```
$ python eval.py --input brca_pmc_top4.txt --fields title,abstract --output brca_top4_eval_ta.csv
$ less brca_top4_eval_ta.csv | sort -t',' -k9 -nr | head -5
8,0.01,2,2,0.3857,0.2335,0.2909,0.2699,0.2784,0.5861
8,0.08,2,2,0.3866,0.2335,0.2912,0.2691,0.2753,0.5849
8,0.27,2,2,0.4062,0.2400,0.3017,0.2789,0.2743,0.5913
8,0.21,2,2,0.3940,0.2338,0.2935,0.2695,0.2689,0.5868
8,0.34,2,2,0.4022,0.2352,0.2968,0.2754,0.2641,0.5882
```

Evaluation for title.

```
$ python eval.py --input brca_pmc_top4.txt --fields title --output brca_top4_eval_t.csv
$ less brca_top4_eval_t.csv | sort -t',' -k9 -nr | head -5
8,0.14,0,4,0.2308,0.2264,0.2286,0.2114,0.1748,0.4757
8,0.14,0,6,0.2581,0.3390,0.2931,0.2695,0.1659,0.4274
8,0.47,16,4,0.2383,0.2191,0.2283,0.2151,0.1503,0.4875
8,0.08,0,10,0.1971,0.3345,0.2480,0.2265,0.1431,0.3734
8,0.14,18,6,0.2451,0.3121,0.2746,0.2526,0.1356,0.4206
```



Since this is a controlled experiment and we know there're four classes in advance, it would be more appropriate to compare the three cases above only for four clusters (i.e., set k=4 for kmeans).

```
$ less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k9 -nr | head -3
8,0.08,6,4,0.3579,0.2875,0.3189,0.2936,0.3180,0.5853
8,0.08,14,4,0.3366,0.2806,0.3060,0.2814,0.2973,0.5684
8,0.08,20,4,0.3069,0.2390,0.2688,0.2469,0.2759,0.5627

$ less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k9 -nr | head -3
8,0.01,16,4,0.3123,0.2923,0.3020,0.2782,0.2210,0.5116
8,0.01,18,4,0.3115,0.2915,0.3012,0.2776,0.2198,0.5108
8,0.14,0,4,0.2801,0.2858,0.2829,0.2585,0.2196,0.4919

$ less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k9 -nr | head -3
8,0.14,0,4,0.2308,0.2264,0.2286,0.2114,0.1748,0.4757
8,0.47,16,4,0.2383,0.2191,0.2283,0.2151,0.1503,0.4875
8,0.01,0,4,0.2212,0.2134,0.2172,0.1995,0.1307,0.4538
```

What if we look at v-measure-a?

```
$ less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k7 -nr | head -3
8,0.34,16,4,0.3672,0.2997,0.3301,0.2967,0.2462,0.5557
8,0.08,6,4,0.3579,0.2875,0.3189,0.2936,0.3180,0.5853
8,0.34,10,4,0.3502,0.2810,0.3118,0.2818,0.2380,0.5523

$ less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k7 -nr | head -3
8,0.60,0,4,0.3098,0.3168,0.3133,0.2867,0.1904,0.4755
8,0.34,0,4,0.3185,0.3075,0.3129,0.2863,0.1737,0.4827
8,0.27,14,4,0.3180,0.3077,0.3128,0.2873,0.1947,0.4926

$ less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k7 -nr | head -3
8,0.53,12,4,0.2310,0.2385,0.2347,0.2153,0.0905,0.4234
8,0.53,20,4,0.2292,0.2384,0.2337,0.2139,0.0941,0.4236
8,0.14,0,4,0.2308,0.2264,0.2286,0.2114,0.1748,0.4757
```

Evaluation for medline data.

```
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
