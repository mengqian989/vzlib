# Data

Data set size (total number of documents).

```bash
# medline
zcat brca_med_top4.txt.gz | cut -f4 | grep -v '|' |  wc -l
14075

# pmc
zcat brca_pmc_top4.txt.gz | cut -f5 | grep -v '|' |  wc -l
1682
```

Distribution of classes (MeSH terms).

```bash
# medline
zcat brca_med_top4.txt.gz | cut -f4 | grep -v '|' |  sort | uniq -c 
   1653 Breast Neoplasms, Male
   8644 Carcinoma, Ductal, Breast
   1341 Carcinoma, Lobular
   2437 Triple Negative Breast Neoplasms

# pmc
zcat brca_pmc_top4.txt.gz | cut -f5 | grep -v '|' |  sort | uniq -c 
    124 Breast Neoplasms, Male
    687 Carcinoma, Ductal, Breast
     88 Carcinoma, Lobular
    783 Triple Negative Breast Neoplasms
```

# Experiments

## Parameters

Tested the combinations of the following parameters:

- Minimal document frequencies: words with document frequency equal or smaller than df are ignored.
  - 10, 30, 50, 70, 100
- R: Parameter for VCGS.
  - 5, 6, 7, 8, 9, 10
- D: Parameter for VCGS.
  - 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
- Number of components (dimensions) for SVD: 
  - 0, 4, 8, 12, 16, 20
  - When set to 0, SVD is not applied.
- Clustering algorithms: 
  - kNN or maximin
- Number of clusters for kNN: 
  - 4
- Theta for maximin:
  - 0.8, 0.9, 0.99
  
## Abstracts (larger data)

Run an evaluation script for medline data created above. Different combinations of parameters are executed. (It takes about a couple of hours to complete.)

```bash
nice python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval_sgl.csv --single -d  "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0" > log_sgl.txt &

# use the same number of documents in each cluster by downsampling
nice python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval_sgl_bal.csv --single --balance -d  "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0" > log_bal.txt &
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order:

> df,r,d,n,alg,theta,k,c,h,vd,v,ari,ami,fms,prtm,prt,sc,sct

where 

- df is the minimal document frequency
- r and d are VCGS's parameters
- n is the number of dimensions for SVD
- alg is an clustering algorithm (kmeans or maximin)
- theta is a parameter for maximin
- k is the number of clusters. This is set beforehand for kNN but is determined by the algorithm for maximin. 
- the rest are evaluation measures: c = completeness, h = homogeneity, vd = v-measure-d, v = v-measure, ari = adjusted rand index, ami = adjusted mutual information, fms = Fowlkes-Mallows index, prtm = macro-averaged purity, prt = micro-averaged purity, sc is silhouette coefficient, and sct is silhouette coefficient computed using true labels.  
- Macro-averaged purity (prtm) is the homogeneity used in Javed's JASIST paper. Note that purity is weighted by cluster size (micro-average) and Javed's homogeneity is macro-averged.

Notes:

- v-measure-d and v-measure are different in how they treat multi-label cases.  The former treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.  Since we're looking at only single-label instances here, they must be always the same.
- When df is greater than 1 (e.g., 10), VCGS is not applied, that is, terms with document frequencies greater than this parameter are all treated as keywords.  This is for investigating the effectiness of VCGS in comparison with DF-based feature selection.

Now let's look at the 10 best parameter combinations based on adjusted rand index (ARI).

```bash
# ranking by ari 
less brca_med_top4_eval_sgl.csv | sort -t',' -k12 -nr | grep ",4,0" | head
1,10,0.10,12,maximin,0.99,4,0.4693,0.4600,0.4646,0.4646,0.5211,0.4599,0.7299,0.7906,0.1813,0.1381
1,10,0.55,12,maximin,0.99,4,0.5087,0.4127,0.4557,0.4557,0.4866,0.4125,0.7420,0.8471,0.1669,0.1401
1,10,0.90,8,maximin,0.90,4,0.3878,0.4028,0.3952,0.3952,0.4294,0.3876,0.6648,0.7382,0.2619,0.1640
1,9,0.90,16,maximin,0.99,4,0.3478,0.4005,0.3723,0.3723,0.4173,0.3476,0.6407,0.6707,0.1590,0.1312
1,8,0.05,8,maximin,0.90,4,0.3665,0.4006,0.3828,0.3828,0.3857,0.3664,0.6295,0.7999,0.2824,0.1593
1,6,0.25,0,kmeans,nan,4,0.4203,0.3812,0.3998,0.3998,0.3726,0.3810,0.6608,0.8236,0.0387,0.0311
1,5,0.20,0,kmeans,nan,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8252,0.0373,0.0304
1,9,0.15,0,kmeans,nan,4,0.3973,0.3685,0.3824,0.3824,0.3709,0.3683,0.6556,0.7971,0.0238,0.0186
1,9,0.80,8,maximin,0.90,4,0.4076,0.4253,0.4162,0.4162,0.3706,0.4074,0.6293,0.8348,0.2875,0.1606
1,8,0.20,0,kmeans,nan,4,0.3950,0.3634,0.3786,0.3786,0.3626,0.3632,0.6524,0.7989,0.0293,0.0232
```

Observations:

- good ari seems to come with relatively good prt (but the opposite doesn't hold; see below).
- df = 1 dominates the top 10, which means VCGS works better than DF-based feature selection.
- maximin with LSA works better than kmeans.
- Good parameter settings (r, d, n) seem more or less random and would be difficult to tune.  More investigation is needed to see how sensitive the performance is to these parameters.
- LSA is not quite effective for kmeans

Let's look at prt-sorted results.

```bash
# ranking by prec
less brca_med_top4_eval_sgl.csv | sort -t',' -k15 -nr | grep ",4,0" | head
1,5,0.35,16,kmeans,nan,4,0.4071,0.3337,0.3668,0.3668,0.2646,0.3335,0.6237,0.8917,0.1299,0.1275
1,9,0.15,16,kmeans,nan,4,0.3395,0.3468,0.3431,0.3431,0.2323,0.3394,0.5476,0.8681,0.1827,0.1212
1,6,0.15,20,kmeans,nan,4,0.3362,0.3377,0.3369,0.3369,0.2242,0.3360,0.5471,0.8667,0.1570,0.1082
1,10,0.20,12,kmeans,nan,4,0.3357,0.3452,0.3404,0.3404,0.2327,0.3355,0.5457,0.8650,0.2227,0.1402
1,6,0.55,8,kmeans,nan,4,0.3661,0.3479,0.3568,0.3568,0.2698,0.3477,0.5918,0.8643,0.2637,0.1277
1,5,0.35,8,kmeans,nan,4,0.3498,0.3290,0.3391,0.3391,0.2473,0.3288,0.5809,0.8627,0.2541,0.1402
1,7,0.40,16,kmeans,nan,4,0.3359,0.3265,0.3311,0.3311,0.2272,0.3263,0.5589,0.8623,0.1768,0.1212
1,5,0.20,16,kmeans,nan,4,0.3291,0.3227,0.3259,0.3259,0.2192,0.3225,0.5507,0.8614,0.1767,0.1215
1,6,0.60,12,kmeans,nan,4,0.3793,0.3745,0.3769,0.3769,0.2803,0.3743,0.5871,0.8604,0.1997,0.1417
1,5,0.50,8,kmeans,nan,4,0.3712,0.3449,0.3576,0.3576,0.2851,0.3447,0.6059,0.8594,0.2663,0.1216
```

Purity reached nearly 0.9 but ari is suboptimal (0.2646 at best).
Then, let's see how good the DF-based feature selection is.  The following shows the 10 best results in ari where minimum DF was set to other than 1.

```bash
 less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | grep ",4,0" | sort -t',' -k12 -nr | head
100,nan,nan,20,kmeans,nan,4,0.3676,0.3484,0.3577,0.3577,0.3374,0.3482,0.6311,0.7863,0.1357,0.1064
10,nan,nan,16,maximin,0.99,4,0.3147,0.3380,0.3259,0.3259,0.3164,0.3145,0.5882,0.7066,0.1404,0.1187
70,nan,nan,0,kmeans,nan,4,0.2722,0.2835,0.2778,0.2778,0.2037,0.2720,0.5263,0.7058,0.0227,0.0151
50,nan,nan,4,maximin,0.80,4,0.2798,0.3372,0.3058,0.3058,0.2026,0.2796,0.4868,0.7374,0.5386,0.0465
50,nan,nan,0,kmeans,nan,4,0.2693,0.2821,0.2756,0.2756,0.1978,0.2691,0.5209,0.7083,0.0209,0.0138
10,nan,nan,20,kmeans,nan,4,0.2622,0.2721,0.2671,0.2671,0.1934,0.2620,0.5205,0.7104,0.1646,0.1044
30,nan,nan,20,kmeans,nan,4,0.2619,0.2721,0.2669,0.2669,0.1900,0.2617,0.5179,0.7089,0.1659,0.1053
10,nan,nan,16,kmeans,nan,4,0.2589,0.2705,0.2646,0.2646,0.1863,0.2587,0.5137,0.7131,0.1903,0.1187
50,nan,nan,20,kmeans,nan,4,0.2598,0.2715,0.2655,0.2655,0.1854,0.2596,0.5133,0.7098,0.1684,0.1071
70,nan,nan,16,kmeans,nan,4,0.2583,0.2717,0.2648,0.2648,0.1820,0.2581,0.5094,0.7131,0.1891,0.1172
```

It was found that maximin worked better than kmeans except for the best result. In any case, the best ARI is 0.3374 and VCGS work better.  

How about v-measure or ami?

```bash
# v-measure
less brca_med_top4_eval_sgl.csv | sort -t',' -k11 -nr | grep ",4,0" | head
1,10,0.10,12,maximin,0.99,4,0.4693,0.4600,0.4646,0.4646,0.5211,0.4599,0.7299,0.7906,0.1813,0.1381
1,10,0.55,12,maximin,0.99,4,0.5087,0.4127,0.4557,0.4557,0.4866,0.4125,0.7420,0.8471,0.1669,0.1401
1,9,0.80,8,maximin,0.90,4,0.4076,0.4253,0.4162,0.4162,0.3706,0.4074,0.6293,0.8348,0.2875,0.1606
1,6,0.25,0,kmeans,nan,4,0.4203,0.3812,0.3998,0.3998,0.3726,0.3810,0.6608,0.8236,0.0387,0.0311
1,5,0.20,0,kmeans,nan,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8252,0.0373,0.0304
1,10,0.70,16,kmeans,nan,4,0.4079,0.3842,0.3957,0.3957,0.3316,0.3840,0.6285,0.8473,0.1632,0.1236
1,10,0.90,8,maximin,0.90,4,0.3878,0.4028,0.3952,0.3952,0.4294,0.3876,0.6648,0.7382,0.2619,0.1640
1,8,0.90,8,kmeans,nan,4,0.3950,0.3927,0.3938,0.3938,0.3073,0.3925,0.6015,0.8561,0.2557,0.1666
1,9,0.95,0,kmeans,nan,4,0.3993,0.3861,0.3926,0.3926,0.3159,0.3859,0.6134,0.8519,0.0968,0.0693
1,8,0.85,8,kmeans,nan,4,0.3947,0.3892,0.3919,0.3919,0.3086,0.3890,0.6044,0.8554,0.2477,0.1693

# ami
less brca_med_top4_eval_sgl.csv | sort -t',' -k13 -nr | grep ",4,0" | head
1,10,0.10,12,maximin,0.99,4,0.4693,0.4600,0.4646,0.4646,0.5211,0.4599,0.7299,0.7906,0.1813,0.1381
1,10,0.55,12,maximin,0.99,4,0.5087,0.4127,0.4557,0.4557,0.4866,0.4125,0.7420,0.8471,0.1669,0.1401
1,9,0.80,8,maximin,0.90,4,0.4076,0.4253,0.4162,0.4162,0.3706,0.4074,0.6293,0.8348,0.2875,0.1606
1,8,0.90,8,kmeans,nan,4,0.3950,0.3927,0.3938,0.3938,0.3073,0.3925,0.6015,0.8561,0.2557,0.1666
1,8,0.85,8,kmeans,nan,4,0.3947,0.3892,0.3919,0.3919,0.3086,0.3890,0.6044,0.8554,0.2477,0.1693
1,10,0.90,8,maximin,0.90,4,0.3878,0.4028,0.3952,0.3952,0.4294,0.3876,0.6648,0.7382,0.2619,0.1640
1,9,1.00,8,kmeans,nan,4,0.3928,0.3874,0.3901,0.3901,0.3046,0.3872,0.6018,0.8553,0.2569,0.1647
1,8,0.80,8,kmeans,nan,4,0.3958,0.3874,0.3916,0.3916,0.3102,0.3872,0.6071,0.8539,0.2461,0.1669
1,8,0.90,20,kmeans,nan,4,0.3969,0.3862,0.3915,0.3915,0.3129,0.3860,0.6101,0.8522,0.1592,0.1194
1,9,0.95,0,kmeans,nan,4,0.3993,0.3861,0.3926,0.3926,0.3159,0.3859,0.6134,0.8519,0.0968,0.0693
```

Observations:

- Overall, we see similar patterns to ari.

## Full texts vs. abstracts (smaller data)

The aim of the following experiments is to show, if any, the advantage of full-text data over abstracts for clustering biomedical articles.  First, run eval.py script. (We can run them in parallel as follows. Takes less than an hour on miksa3.)

```bash
nice python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_all_sgl.csv --single -d  "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0" > log_full.txt &

nice python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_ta_sgl.csv --fields title,abstract --single -d  "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0" > log_ta.txt &

nice python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_t_sgl.csv --fields title --single -d "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0" > log_t.txt &
```

Let's look at the result based on ARI.

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head
1,6,0.40,8,maximin,0.90,4,0.4015,0.4389,0.4193,0.4193,0.4637,0.4001,0.6637,0.8125,0.8036,0.3521,0.1424
1,6,0.40,4,maximin,0.90,4,0.3171,0.3744,0.3433,0.3433,0.4290,0.3156,0.6318,0.8334,0.7530,0.5555,0.0864
1,6,0.40,4,maximin,0.80,4,0.3171,0.3744,0.3433,0.3433,0.4290,0.3156,0.6318,0.8334,0.7530,0.5555,0.0864
1,8,0.50,8,maximin,0.99,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,8,0.50,8,maximin,0.90,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,9,0.60,8,maximin,0.99,4,0.3426,0.3779,0.3594,0.3594,0.4196,0.3411,0.6375,0.7420,0.7690,0.3640,0.1471
1,9,0.60,8,maximin,0.90,4,0.3426,0.3779,0.3594,0.3594,0.4196,0.3411,0.6375,0.7420,0.7690,0.3640,0.1471
1,5,0.30,8,maximin,0.99,4,0.3469,0.3906,0.3674,0.3674,0.4166,0.3454,0.6304,0.7398,0.7780,0.3780,0.1563
1,8,0.70,8,maximin,0.90,4,0.3409,0.3849,0.3616,0.3616,0.4077,0.3394,0.6230,0.6933,0.7686,0.3681,0.1303
1,8,0.50,4,maximin,0.80,4,0.2982,0.3538,0.3236,0.3236,0.4033,0.2967,0.6146,0.8257,0.7494,0.5544,0.0908

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head 
1,5,1.00,8,maximin,0.90,4,0.3814,0.4461,0.4112,0.4112,0.4227,0.3797,0.6235,0.7277,0.7663,0.5386,0.1918
1,5,0.10,20,kmeans,nan,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749,0.7562,0.1655,0.1334
1,5,0.40,8,maximin,0.80,4,0.2670,0.3336,0.2966,0.2966,0.3451,0.2655,0.5649,0.7309,0.7160,0.3126,0.1103
30,nan,nan,12,kmeans,nan,4,0.3496,0.3078,0.3274,0.3274,0.3088,0.3060,0.5974,0.8093,0.7283,0.2708,0.1825
1,6,1.00,4,maximin,0.90,4,0.2634,0.3343,0.2947,0.2947,0.2750,0.2617,0.5092,0.6108,0.6678,0.7609,0.0155
1,6,1.00,4,maximin,0.80,4,0.2634,0.3343,0.2947,0.2947,0.2750,0.2617,0.5092,0.6108,0.6678,0.7609,0.0155
1,5,0.80,8,maximin,0.99,4,0.2117,0.2633,0.2347,0.2347,0.2638,0.2099,0.5071,0.5429,0.6736,0.3954,0.1343
1,5,0.20,12,kmeans,nan,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.7358,0.7111,0.1967,0.1790
1,9,0.20,0,kmeans,nan,4,0.3306,0.3618,0.3455,0.3455,0.2555,0.3290,0.5290,0.7132,0.7057,0.0295,0.0226
1,5,0.20,16,kmeans,nan,4,0.3843,0.3861,0.3852,0.3852,0.2547,0.3828,0.5517,0.8414,0.7081,0.1533,0.1513

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head
70,nan,nan,4,kmeans,nan,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.6358,0.7706,0.6073,-0.0047
100,nan,nan,4,kmeans,nan,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220,0.6188,0.7685,0.6613,-0.0112
100,nan,nan,0,kmeans,nan,4,0.2920,0.3545,0.3202,0.3202,0.2644,0.2905,0.5188,0.7703,0.7661,0.4266,0.0320
1,10,0.70,4,maximin,0.90,4,0.2248,0.2666,0.2439,0.2439,0.2547,0.2231,0.5140,0.7773,0.7213,0.6590,0.0619
1,10,0.70,4,maximin,0.80,4,0.2248,0.2666,0.2439,0.2439,0.2547,0.2231,0.5140,0.7773,0.7213,0.6590,0.0619
1,7,0.30,4,maximin,0.80,4,0.2338,0.2749,0.2527,0.2527,0.2538,0.2321,0.5151,0.7236,0.7280,0.6620,0.0639
1,10,0.50,4,maximin,0.90,4,0.2269,0.2708,0.2469,0.2469,0.2528,0.2252,0.5117,0.7830,0.7225,0.6624,0.0631
1,10,0.50,4,maximin,0.80,4,0.2269,0.2708,0.2469,0.2469,0.2528,0.2252,0.5117,0.7830,0.7225,0.6624,0.0631
1,6,0.50,4,maximin,0.90,4,0.2222,0.2673,0.2427,0.2427,0.2521,0.2206,0.5096,0.7810,0.7219,0.6625,0.0595
1,6,0.50,4,maximin,0.80,4,0.2222,0.2673,0.2427,0.2427,0.2521,0.2206,0.5096,0.7810,0.7219,0.6625,0.0595
```

Observations:

- Using all fields (title+abstract+fulltext) achieved the best performance in ARI, followed by title+abs, then title.
- When using only titles, DF-based feature selection worked better than VCGS in most cases. This would be due to the small number of words from titles (therefore not many keywords were identified by VCGS).  This tendency is also seen in title+abstract.
- maximin generally works better than kmeans for title+abstract+fulltext and title+abstract.
- LSA is generally effective probably due to the smaller size of data.

Sort by adjusted mutual information.

```bash
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head -5
1,6,0.40,8,maximin,0.90,4,0.4015,0.4389,0.4193,0.4193,0.4637,0.4001,0.6637,0.8125,0.8036,0.3521,0.1424
1,9,0.60,16,maximin,0.99,4,0.3563,0.4013,0.3774,0.3774,0.3830,0.3548,0.6079,0.7311,0.7589,0.2206,0.1767
1,8,0.50,8,maximin,0.99,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,8,0.50,8,maximin,0.90,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,5,0.30,8,maximin,0.99,4,0.3469,0.3906,0.3674,0.3674,0.4166,0.3454,0.6304,0.7398,0.7780,0.3780,0.1563

less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head -5
1,5,0.10,20,kmeans,nan,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749,0.7562,0.1655,0.1334
1,5,0.20,16,kmeans,nan,4,0.3843,0.3861,0.3852,0.3852,0.2547,0.3828,0.5517,0.8414,0.7081,0.1533,0.1513
1,5,1.00,8,maximin,0.90,4,0.3814,0.4461,0.4112,0.4112,0.4227,0.3797,0.6235,0.7277,0.7663,0.5386,0.1918
1,5,0.20,20,kmeans,nan,4,0.3734,0.3843,0.3788,0.3788,0.2490,0.3719,0.5430,0.7381,0.7045,0.1382,0.1303
1,5,0.20,12,kmeans,nan,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.7358,0.7111,0.1967,0.1790

less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head -5
1,5,0.90,20,kmeans,nan,4,0.3283,0.3233,0.3258,0.3258,0.2285,0.3216,0.5415,0.9621,0.7505,0.1742,0.0747
50,nan,nan,4,kmeans,nan,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402,0.7901,0.7598,0.5600,-0.0528
70,nan,nan,4,kmeans,nan,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.6358,0.7706,0.6073,-0.0047
1,10,0.90,0,kmeans,nan,4,0.3416,0.3149,0.3277,0.3277,0.1544,0.3131,0.5210,0.8239,0.6313,0.0574,0.0278
30,nan,nan,8,kmeans,nan,4,0.3158,0.3093,0.3125,0.3125,0.2155,0.3075,0.5343,0.9492,0.7443,0.3025,0.0357
```

Observations:

- For both metrics, the tendency is the same but smaller difference between all and title+abs.

Sort by prt.

```bash
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k16 -nr | head -5
1,6,0.40,8,maximin,0.90,4,0.4015,0.4389,0.4193,0.4193,0.4637,0.4001,0.6637,0.8125,0.8036,0.3521,0.1424
1,5,0.30,8,maximin,0.99,4,0.3469,0.3906,0.3674,0.3674,0.4166,0.3454,0.6304,0.7398,0.7780,0.3780,0.1563
1,8,0.50,8,maximin,0.99,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,8,0.50,8,maximin,0.90,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,5,0.30,12,maximin,0.99,4,0.3027,0.3466,0.3232,0.3232,0.3900,0.3012,0.6115,0.7657,0.7720,0.2777,0.1946

less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k16 -nr | head -5
1,5,1.00,8,maximin,0.90,4,0.3814,0.4461,0.4112,0.4112,0.4227,0.3797,0.6235,0.7277,0.7663,0.5386,0.1918
1,5,0.10,20,kmeans,nan,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749,0.7562,0.1655,0.1334
30,nan,nan,12,kmeans,nan,4,0.3496,0.3078,0.3274,0.3274,0.3088,0.3060,0.5974,0.8093,0.7283,0.2708,0.1825
1,5,0.40,8,maximin,0.80,4,0.2670,0.3336,0.2966,0.2966,0.3451,0.2655,0.5649,0.7309,0.7160,0.3126,0.1103
1,5,0.20,12,kmeans,nan,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.7358,0.7111,0.1967,0.1790

less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k16 -nr | head -5
70,nan,nan,4,kmeans,nan,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.6358,0.7706,0.6073,-0.0047
100,nan,nan,4,kmeans,nan,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220,0.6188,0.7685,0.6613,-0.0112
100,nan,nan,0,kmeans,nan,4,0.2920,0.3545,0.3202,0.3202,0.2644,0.2905,0.5188,0.7703,0.7661,0.4266,0.0320
50,nan,nan,4,kmeans,nan,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402,0.7901,0.7598,0.5600,-0.0528
100,nan,nan,8,kmeans,nan,4,0.2923,0.3511,0.3190,0.3190,0.2457,0.2907,0.5096,0.8119,0.7587,0.4660,-0.0045
```

Observations:

- prt are similar but other metics are quite different.

# Evaluation metrics

To see the difference among different evaluation metrics empirically, the following shows Pearson's correlation coefficient between every pair of metrics **by R**, not python.

```R
cls <- c(r="numeric",d="numeric",n="numeric",k="numeric",c="numeric",h="numeric",ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric",prt="numeric",sc="numeric",sct="numeric") 

# abstract data 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls,na.strings="na") 
cor(x[,10:16],use="pairwise.complete.obs")
            v       ari       ami       fms        prt         sc        sct
v   1.0000000 0.8773201 0.9479307 0.7017890  0.4593293  0.2370127  0.3854788
ari 0.8773201 1.0000000 0.8936266 0.8188384  0.3759744  0.1035182  0.2907318
ami 0.9479307 0.8936266 1.0000000 0.8248086  0.3737182  0.1974180  0.2954746
fms 0.7017890 0.8188384 0.8248086 1.0000000  0.4131840  0.2430231  0.1334362
prt 0.4593293 0.3759744 0.3737182 0.4131840  1.0000000  0.3266357 -0.1264683
sc  0.2370127 0.1035182 0.1974180 0.2430231  0.3266357  1.0000000 -0.2043118
sct 0.3854788 0.2907318 0.2954746 0.1334362 -0.1264683 -0.2043118  1.0000000

ami and vd (or v) are found to be strongly correlated.  ari has relatively strong correlation with the three but it's not as strong as theirs.  The following shows the scatter plot for every pair of metrics: v, ari, ami, prt, sc, sct.

```R
panel.cor <- function(x, y, digits = 3, cex.cor, ...)
{
 usr <- par("usr"); on.exit(par(usr))
 par(usr = c(0, 1, 0, 1))
 # correlation coefficient
 r <- cor(x, y)
 txt <- format(c(r, 0.123456789), digits = digits)[1]
 txt <- paste("r = ", txt, sep = "")
 text(0.5, 0.6, txt, cex=1.5)

 # p-value calculation
 p <- cor.test(x, y)$p.value
 txt2 <- format(c(p, 0.123456789), digits = digits)[1]
 txt2 <- paste("p = ", txt2, sep = "")
 if(p<0.01) txt2 <- expression(paste(p <= 0.01, sep = ""))
 text(0.5, 0.4, txt2, cex=1.5)
}
quartz("",6,5) # this is for Mac
par(mar=c(5,4,1,1))
pairs(x[,c(11,12,14,15)], upper.panel = panel.cor)
```

<img src="figs/scatter_four.png" width="400">

How do r and d affect cluster quality? Note that P is used to refer to d below.

```R
cls <- c(r="numeric", d="numeric", n="numeric", ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls,na.strings="na")
x[x$df == 1 & x$alg == "kmeans" & x$n > 0 & x$k == 4, c(2,3,4,11)] -> y
colnames(y) = c("R", "P", "n", "ARI")

library(ggplot2)
library(magrittr) # for pipe operator
library(dplyr)    # for grouping

# compute mean by group
ag <- y %>% 
        group_by(R, P) %>% 
        summarise(ARI = mean(ARI))

# plot
quartz("",6,5) # this is for Mac
par(mar=c(5,4,1,1))
sp = ggplot(data=ag, mapping=aes(x=factor(R), y=factor(P), color=ARI)) + geom_point(alpha=.9, size=ag$ARI*30)
sp+scale_color_gradient(low="white", high="red") + theme_bw() + theme(panel.grid=element_blank()) + labs(x=expression(italic(R)),y=expression(italic(P)))
```

<img src="figs/r_and_p_abs.png" width="400">

How about n (number of dimensions)?

```R
cls <- c(r="numeric", d="numeric", n="numeric", ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls,na.strings="na")
x[x$df == 1 & x$alg == "kmeans" & x$n > 0 & x$k == 4, c(2,3,4,11)] -> y
colnames(y) = c("R", "P", "n", "ARI")

quartz("",6,5) # this is for Mac
par(mar=c(5,4,1,1))

sp2 = ggplot(data=y, mapping=aes(x=factor(n), y=ARI)) + geom_boxplot()
sp2 + geom_jitter(alpha=.5, color="tomato", height=0) + theme_bw() + theme(panel.grid=element_blank()) + labs(x=expression(paste("Number of dimensions ", italic(n))))
```

<img src="figs/n_and_ari.png" width="400">
