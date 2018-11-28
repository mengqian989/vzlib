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
1,5,0.20,0,kmeans,nan,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8963,0.7805,0.0373,0.0304
1,8,0.20,0,kmeans,nan,4,0.3950,0.3634,0.3786,0.3786,0.3626,0.3632,0.6524,0.7374,0.7724,0.0293,0.0232
1,10,0.30,0,kmeans,nan,4,0.3940,0.3647,0.3788,0.3788,0.3613,0.3645,0.6502,0.8641,0.7722,0.0329,0.0259
1,5,0.10,0,kmeans,nan,4,0.3959,0.3597,0.3769,0.3769,0.3612,0.3595,0.6544,0.7427,0.7737,0.0253,0.0202
1,8,0.30,0,kmeans,nan,4,0.4035,0.3642,0.3828,0.3828,0.3586,0.3640,0.6537,0.7604,0.7753,0.0363,0.0291
1,7,0.30,0,kmeans,nan,4,0.4043,0.3662,0.3843,0.3843,0.3581,0.3660,0.6526,0.7632,0.7759,0.0395,0.0317
1,7,0.10,20,kmeans,nan,4,0.3898,0.3515,0.3696,0.3696,0.3521,0.3513,0.6507,0.8641,0.7702,0.1259,0.1064
1,10,0.50,20,kmeans,nan,4,0.3964,0.3670,0.3811,0.3811,0.3508,0.3668,0.6439,0.8801,0.7755,0.1355,0.1096
1,5,0.20,20,kmeans,nan,4,0.4077,0.3591,0.3819,0.3819,0.3490,0.3589,0.6530,0.7858,0.7725,0.1254,0.1098
1,6,0.10,20,kmeans,nan,4,0.3877,0.3473,0.3664,0.3664,0.3475,0.3471,0.6492,0.7873,0.7687,0.1241,0.1062
```

Observations:

- good ari seems to come with relatively good prt (but the opposite doesn't hold; see below).
- df = 1 dominates the top 10, which means VCGS works better than DF-based feature selection.
- kmeans worked better than maximin
- LSA did not improve the performance.
- Good parameter settings (r, d, n) seem more or less random and may be difficult to tune.  More investigation is needed to see how sensitive the performance is to these parameters.

Let's look at prt-sorted results.

```bash
# ranking by prt
less brca_med_top4_eval_sgl.csv | sort -t',' -k16 -nr | grep ",4,0" | head
1,7,0.20,4,maximin,0.80,4,0.3623,0.3961,0.3784,0.3784,0.2990,0.3621,0.5762,0.8244,0.7982,0.4748,0.0411
1,8,0.20,4,maximin,0.80,4,0.3260,0.3755,0.3490,0.3490,0.2869,0.3258,0.5534,0.7858,0.7981,0.5080,0.0429
1,8,0.90,8,kmeans,nan,4,0.3950,0.3927,0.3938,0.3938,0.3073,0.3925,0.6015,0.9042,0.7871,0.2557,0.1666
1,10,0.40,4,kmeans,nan,4,0.3314,0.3625,0.3463,0.3463,0.2455,0.3312,0.5378,0.7988,0.7858,0.4355,0.0448
1,8,1.00,16,maximin,0.99,4,0.3336,0.3667,0.3494,0.3494,0.2646,0.3335,0.5471,0.8209,0.7857,0.1772,0.1401
1,6,0.60,8,maximin,0.99,4,0.3235,0.3709,0.3456,0.3456,0.2735,0.3233,0.5452,0.7775,0.7857,0.2839,0.1341
1,6,0.60,8,maximin,0.90,4,0.3235,0.3709,0.3456,0.3456,0.2735,0.3233,0.5452,0.7775,0.7857,0.2839,0.1341
1,9,0.40,4,kmeans,nan,4,0.3307,0.3606,0.3450,0.3450,0.2447,0.3305,0.5379,0.8001,0.7854,0.4364,0.0406
1,9,1.00,8,kmeans,nan,4,0.3928,0.3874,0.3901,0.3901,0.3046,0.3872,0.6018,0.8141,0.7846,0.2569,0.1647
1,8,0.80,8,kmeans,nan,4,0.3958,0.3874,0.3916,0.3916,0.3102,0.3872,0.6071,0.8120,0.7841,0.2461,0.1669
```

Observations:

- Purity reached nearly 0.8 but ari is suboptimal (0.2990 at best)
- maximin was found competitive to kmeans.
- LSA generally works

Then, let's see how good the DF-based feature selection is.  The following shows the 10 best results in ari where minimum DF was set to other than 1.

```bash
less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | grep ",4,0" | sort -t',' -k12 -nr | head
100,nan,nan,20,kmeans,nan,4,0.3676,0.3484,0.3577,0.3577,0.3374,0.3482,0.6311,0.7893,0.7613,0.1357,0.1064
70,nan,nan,0,kmeans,nan,4,0.2722,0.2835,0.2778,0.2778,0.2037,0.2720,0.5263,0.6756,0.6696,0.0227,0.0151
50,nan,nan,0,kmeans,nan,4,0.2693,0.2821,0.2756,0.2756,0.1978,0.2691,0.5209,0.6231,0.6707,0.0209,0.0138
10,nan,nan,20,kmeans,nan,4,0.2622,0.2721,0.2671,0.2671,0.1934,0.2620,0.5205,0.6219,0.6704,0.1646,0.1044
30,nan,nan,20,kmeans,nan,4,0.2619,0.2721,0.2669,0.2669,0.1900,0.2617,0.5179,0.6748,0.6682,0.1659,0.1053
10,nan,nan,16,kmeans,nan,4,0.2589,0.2705,0.2646,0.2646,0.1863,0.2587,0.5137,0.6781,0.6704,0.1903,0.1187
50,nan,nan,20,kmeans,nan,4,0.2598,0.2715,0.2655,0.2655,0.1854,0.2596,0.5133,0.7972,0.6677,0.1684,0.1071
70,nan,nan,16,kmeans,nan,4,0.2583,0.2717,0.2648,0.2648,0.1820,0.2581,0.5094,0.5647,0.6682,0.1891,0.1172
10,nan,nan,8,kmeans,nan,4,0.2543,0.2703,0.2620,0.2620,0.1815,0.2541,0.5070,0.6287,0.6747,0.2727,0.1586
50,nan,nan,12,kmeans,nan,4,0.2572,0.2712,0.2640,0.2640,0.1812,0.2570,0.5082,0.7465,0.6684,0.2206,0.1339
```

It was found that kmeans with LSA worked better than maximin. In any case, the best ARI is 0.3374 and VCGS generally works better.  

How about ami?

```bash
less brca_med_top4_eval_sgl.csv | sort -t',' -k13 -nr | grep ",4,0" | head
1,8,0.90,8,kmeans,nan,4,0.3950,0.3927,0.3938,0.3938,0.3073,0.3925,0.6015,0.9042,0.7871,0.2557,0.1666
1,9,1.00,8,kmeans,nan,4,0.3928,0.3874,0.3901,0.3901,0.3046,0.3872,0.6018,0.8141,0.7846,0.2569,0.1647
1,8,0.80,8,kmeans,nan,4,0.3958,0.3874,0.3916,0.3916,0.3102,0.3872,0.6071,0.8120,0.7841,0.2461,0.1669
1,8,0.90,20,kmeans,nan,4,0.3969,0.3862,0.3915,0.3915,0.3129,0.3860,0.6101,0.8101,0.7835,0.1592,0.1194
1,8,0.90,16,kmeans,nan,4,0.3950,0.3847,0.3898,0.3898,0.3096,0.3845,0.6078,0.8106,0.7828,0.1773,0.1349
1,10,0.70,16,kmeans,nan,4,0.4079,0.3842,0.3957,0.3957,0.3316,0.3840,0.6285,0.8039,0.7823,0.1632,0.1236
1,8,0.80,20,kmeans,nan,4,0.4006,0.3835,0.3919,0.3919,0.3188,0.3834,0.6175,0.9051,0.7817,0.1525,0.1184
1,6,0.60,0,kmeans,nan,4,0.3870,0.3817,0.3844,0.3844,0.2932,0.3816,0.5945,0.8155,0.7827,0.0958,0.0688
1,6,0.60,16,kmeans,nan,4,0.3874,0.3797,0.3835,0.3835,0.2942,0.3795,0.5970,0.8154,0.7824,0.1751,0.1382
1,9,1.00,0,kmeans,nan,4,0.3902,0.3793,0.3847,0.3847,0.3021,0.3791,0.6038,0.8100,0.7803,0.1031,0.0710
```
Observations:

- kmeans with LSA works
- The ranking seems to be more correlated with the ranking by prt.

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
# full text
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head
1,6,0.40,8,maximin,0.90,4,0.4015,0.4389,0.4193,0.4193,0.4637,0.4001,0.6637,0.8125,0.8036,0.3521,0.1424
1,9,0.60,16,maximin,0.99,4,0.3563,0.4013,0.3774,0.3774,0.3830,0.3548,0.6079,0.7311,0.7589,0.2206,0.1767
1,8,0.50,8,maximin,0.99,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,8,0.50,8,maximin,0.90,4,0.3493,0.3840,0.3658,0.3658,0.4236,0.3478,0.6405,0.7494,0.7720,0.3620,0.1490
1,5,0.30,8,maximin,0.99,4,0.3469,0.3906,0.3674,0.3674,0.4166,0.3454,0.6304,0.7398,0.7780,0.3780,0.1563
1,9,0.60,8,maximin,0.99,4,0.3426,0.3779,0.3594,0.3594,0.4196,0.3411,0.6375,0.7420,0.7690,0.3640,0.1471
1,9,0.60,8,maximin,0.90,4,0.3426,0.3779,0.3594,0.3594,0.4196,0.3411,0.6375,0.7420,0.7690,0.3640,0.1471
1,8,0.70,8,maximin,0.90,4,0.3409,0.3849,0.3616,0.3616,0.4077,0.3394,0.6230,0.6933,0.7686,0.3681,0.1303
1,7,0.60,12,maximin,0.99,4,0.3387,0.4024,0.3678,0.3678,0.3742,0.3373,0.5925,0.7663,0.7673,0.2663,0.1461
1,7,0.60,12,maximin,0.90,4,0.3387,0.4024,0.3678,0.3678,0.3742,0.3373,0.5925,0.7663,0.7673,0.2663,0.1461

# title+abstract
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head
1,5,0.10,20,kmeans,nan,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749,0.7562,0.1655,0.1334
1,5,0.20,16,kmeans,nan,4,0.3843,0.3861,0.3852,0.3852,0.2547,0.3828,0.5517,0.8414,0.7081,0.1533,0.1513
1,5,1.00,8,maximin,0.90,4,0.3814,0.4461,0.4112,0.4112,0.4227,0.3797,0.6235,0.7277,0.7663,0.5386,0.1918
1,5,0.20,20,kmeans,nan,4,0.3734,0.3843,0.3788,0.3788,0.2490,0.3719,0.5430,0.7381,0.7045,0.1382,0.1303
1,5,0.20,12,kmeans,nan,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.7358,0.7111,0.1967,0.1790
1,5,0.80,12,kmeans,nan,4,0.3661,0.3885,0.3770,0.3770,0.2119,0.3644,0.5114,0.8162,0.6703,0.2882,0.1530
1,5,0.20,8,kmeans,nan,4,0.3632,0.3758,0.3694,0.3694,0.2523,0.3616,0.5426,0.7573,0.7063,0.2335,0.1729
1,9,1.00,20,kmeans,nan,4,0.3621,0.3794,0.3706,0.3706,0.2007,0.3606,0.5120,0.8168,0.6659,0.1635,0.1307
1,6,0.50,16,kmeans,nan,4,0.3617,0.3664,0.3641,0.3641,0.1904,0.3601,0.5159,0.9084,0.6415,0.1543,0.1434
1,7,0.60,20,kmeans,nan,4,0.3615,0.3709,0.3661,0.3661,0.1965,0.3599,0.5157,0.7376,0.6570,0.1448,0.1338

# title
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k13 -nr | head
1,5,0.90,20,kmeans,nan,4,0.3283,0.3233,0.3258,0.3258,0.2285,0.3216,0.5415,0.9621,0.7505,0.1742,0.0747
50,nan,nan,4,kmeans,nan,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402,0.7901,0.7598,0.5600,-0.0528
70,nan,nan,4,kmeans,nan,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.6358,0.7706,0.6073,-0.0047
1,10,0.90,0,kmeans,nan,4,0.3416,0.3149,0.3277,0.3277,0.1544,0.3131,0.5210,0.8239,0.6313,0.0574,0.0278
30,nan,nan,8,kmeans,nan,4,0.3158,0.3093,0.3125,0.3125,0.2155,0.3075,0.5343,0.9492,0.7443,0.3025,0.0357
50,nan,nan,8,kmeans,nan,4,0.3088,0.3223,0.3154,0.3154,0.2212,0.3071,0.5275,0.9633,0.7483,0.3317,0.0017
50,nan,nan,0,kmeans,nan,4,0.3080,0.3669,0.3349,0.3349,0.2050,0.3066,0.4847,0.7581,0.7489,0.1757,0.0780
70,nan,nan,20,kmeans,nan,4,0.3071,0.3397,0.3225,0.3225,0.2412,0.3054,0.5272,0.6271,0.7585,0.2594,0.0652
50,nan,nan,12,kmeans,nan,4,0.3065,0.3194,0.3128,0.3128,0.2172,0.3048,0.5256,0.7987,0.7465,0.2732,0.0573
100,nan,nan,4,kmeans,nan,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220,0.6188,0.7685,0.6613,-0.0112
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
