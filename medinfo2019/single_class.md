# Data

Data set size (total number of documents).

```bash
# medline
less brca_med_top4.txt.gz | cut -f4 | grep -v '|' |  wc -l
14075

# pmc
less brca_pmc_top4.txt.gz | cut -f4 | grep -v '|' |  wc -l
1899
```

Distribution of classes (MeSH terms).

```bash
# medline
less brca_med_top4.txt.gz | cut -f4 | grep -v '|' |  sort | uniq -c 
   1653 Breast Neoplasms, Male
   8644 Carcinoma, Ductal, Breast
   1341 Carcinoma, Lobular
   2437 Triple Negative Breast Neoplasms

# pmc
less brca_pmc_top4.txt.gz | cut -f5 | grep -v '|' |  sort | uniq -c 
    124 Breast Neoplasms, Male
    687 Carcinoma, Ductal, Breast
     88 Carcinoma, Lobular
    783 Triple Negative Breast Neoplasms
```

# Experiments

## Parameters

Tested the combinations of the following parameters:

- Minimal document frequencies: words with document frequency equal or smaller than df are ignored.
  - 1, 10, 30, 50, 70, 100
- R: Parameter for VCGS.
  - 5, 6, 7, 8, 9, 10
- D: Parameter for VCGS.
  - 0.01 0.08 0.14 0.21 0.27 0.34 0.40 0.47 0.53 0.60
- Number of components (dimensions) for SVD: 
  - 0, 4, 8, 12, 16, 20
  - When set to 0, SVD is not applied.
- Clustering algorithms: 
  - kNN or maximin
- Number of clusters for kNN: 
  - 2, 4, 6, 8, 10

## Abstracts (larger data)

Run an evaluation script for medline data created above. Different combinations of parameters are executed. (It takes about 10 hours to complete.)

```bash
python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval_sgl.csv --single
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order:

> df,r,d,n,alg,k,c,h,vd,v,ari,ami,fms

where 

- df is the minimal document frequency
- r and d are VCGS's parameters
- n is the number of dimensions for SVD
- alg is an clustering algorithm (kmeans or maximin)
- k is the number of clusters. This is set beforehand for kNN but is determined by the algorithm for maximin. 
- the rest are evaluation measures: c = completeness, h = homogeneity, vd = v-measure-d, v = v-measure, ari = adjusted rand index, ami = adjusted mutual information, and fms = Fowlkes-Mallows index.  

Notes:

- v-measure-d and v-measure are different in how to treat multi-label cases.  The former treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.
- When df is greater than 1 (e.g., 10), VCGS is not applied, meaning that terms with document frequencies greater than this parameter are all treated as keywords.  This is for investigating the effectiness of VCGS in comparison with DF-based feature selection.

Now let's look at the five best parameter combinations based on adjusted rand index (ARI).

```bash
#  any number of clusters
less brca_med_top4_eval_sgl.csv | sort -t',' -k11 -nr | head -5
1,9,0.27,20,kmeans,4,0.5777,0.3748,0.4547,0.4547,0.4332,0.3746,0.7460
1,9,0.14,18,kmeans,4,0.4658,0.3038,0.3677,0.3677,0.3849,0.3035,0.7162
1,8,0.01,14,kmeans,6,0.3946,0.4463,0.4188,0.4188,0.3696,0.3943,0.6389
1,9,0.53,10,maximin,6,0.2867,0.3593,0.3189,0.3189,0.3629,0.2864,0.6082
1,8,0.21,0,kmeans,4,0.3947,0.3639,0.3787,0.3787,0.3629,0.3637,0.6521

#  number of clusters = 4
less brca_med_top4_eval_sgl.csv | grep ,4,0'' | sort -t',' -k11 -nr | head -5
1,9,0.27,20,kmeans,4,0.5777,0.3748,0.4547,0.4547,0.4332,0.3746,0.7460
1,9,0.14,18,kmeans,4,0.4658,0.3038,0.3677,0.3677,0.3849,0.3035,0.7162
1,8,0.21,0,kmeans,4,0.3947,0.3639,0.3787,0.3787,0.3629,0.3637,0.6521
1,8,0.27,20,kmeans,4,0.3990,0.3577,0.3772,0.3772,0.3527,0.3575,0.6517
1,8,0.14,8,kmeans,4,0.3921,0.3605,0.3757,0.3757,0.3523,0.3603,0.6471
```

Observations:

- df = 1 dominates the top ranked ones, which means VCGS is better than DF-based feature selection.
- kmeans generally works better than maximin.
- r = 8~9 worked good. On the other hand, good d value seems random.  More investigation is needed to see if how sensitive the performance is to these parameters.
- SVD seems to be effective.  More investigation is needed to see the relation between the number of components (n) and performance.
- k = 4 (and 6) produced high ARI, which is expected as we have four underlying classes (mesh terms)

Based on the first observation above, let's see how good the DF-based feature selection is.  The following shows the five best results in ari where minimum DF was set to other than 1.

```bash
# any number of clusters
less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | sort -t',' -k11 -nr | head -5
less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | sort -t',' -k11 -nr | head -5
10,na,na,4,kmeans,4,0.2107,0.1859,0.1975,0.1975,0.1410,0.1856,0.5146
50,na,na,10,kmeans,8,0.1537,0.1394,0.1462,0.1462,0.1316,0.1388,0.5230
100,na,na,20,kmeans,6,0.1464,0.1072,0.1238,0.1238,0.1303,0.1067,0.5657
70,na,na,18,kmeans,14,0.1167,0.1402,0.1273,0.1273,0.1267,0.1157,0.5003
70,na,na,20,kmeans,12,0.1291,0.1294,0.1292,0.1292,0.1259,0.1281,0.5290

# number of clusters = 4
less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | grep ',4,0' | sort -t',' -k11 -nr | head -5
10,na,na,4,kmeans,4,0.2107,0.1859,0.1975,0.1975,0.1410,0.1856,0.5146
100,na,na,20,kmeans,4,0.1902,0.0984,0.1297,0.1297,0.1182,0.0981,0.5990
50,na,na,4,kmeans,4,0.1629,0.1350,0.1476,0.1476,0.1137,0.1347,0.5106
10,na,na,10,kmeans,4,0.1783,0.1478,0.1616,0.1616,0.1080,0.1475,0.5040
100,na,na,12,kmeans,4,0.1733,0.1030,0.1292,0.1292,0.1069,0.1027,0.5655
```

The best ari was found to be 0.1410, which is pretty low.  So VCGS does work!  

Just out of curiosity, what if we look at v-measure-d?

```bash
less brca_med_top4_eval_sgl.csv | sort -t',' -k9 -nr | head -5
1,9,0.27,20,kmeans,4,0.5777,0.3748,0.4547,0.4547,0.4332,0.3746,0.7460
1,8,0.01,14,kmeans,6,0.3946,0.4463,0.4188,0.4188,0.3696,0.3943,0.6389
1,9,0.21,16,kmeans,6,0.4111,0.3856,0.3979,0.3979,0.3550,0.3853,0.6688
1,8,0.08,0,kmeans,6,0.3417,0.4695,0.3955,0.3955,0.2518,0.3414,0.5177
1,8,0.14,20,kmeans,6,0.3433,0.4658,0.3953,0.3953,0.2483,0.3431,0.5194
```

Observations:

- Overall, we see similar patterns to ari.
- df = 1 still works better (VCGS is better).
- r is more stable than d.
- kmeans still works better.
- k = 4 or 6 still generally works better, which is not expected as v-measure tends to increase with the number of clusters.

## Full texts vs. abstracts (smaller data)

First, run eval.py script. (We can run them in parallel as follows. Takes about a couple of hours.)

```bash
python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_all_sgl.csv --single &
python eval.py --input brca_pmc_top4.txt.gz --fields title,abstract --output brca_top4_eval_ta_sgl.csv --single &
python eval.py --input brca_pmc_top4.txt.gz --fields title --output brca_top4_eval_t_sgl.csv --single &
```

Let's look at the result based on ARI.

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | sort -t',' -k11 -nr | head 
1,6,0.08,8,kmeans,4,0.3853,0.3094,0.3432,0.3432,0.3999,0.3076,0.6559
1,8,0.08,4,kmeans,4,0.3311,0.3124,0.3215,0.3215,0.3934,0.3107,0.6370
1,6,0.08,0,kmeans,2,0.4437,0.2871,0.3486,0.3486,0.3887,0.2865,0.6626
1,9,0.08,4,kmeans,4,0.3227,0.3073,0.3148,0.3148,0.3858,0.3055,0.6311
1,10,0.08,4,kmeans,4,0.3180,0.3066,0.3122,0.3122,0.3787,0.3048,0.6254
1,7,0.08,8,kmeans,4,0.3678,0.2960,0.3280,0.3280,0.3772,0.2941,0.6426
1,7,0.08,0,kmeans,2,0.4299,0.2780,0.3376,0.3376,0.3744,0.2774,0.6546
1,8,0.08,12,kmeans,4,0.3801,0.3158,0.3450,0.3450,0.3707,0.3140,0.6357
1,9,0.08,8,kmeans,4,0.3449,0.2759,0.3065,0.3065,0.3560,0.2739,0.6310
1,7,0.08,12,kmeans,4,0.3531,0.2771,0.3105,0.3105,0.3468,0.2751,0.6277

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | sort -t',' -k11 -nr | head 
1,5,0.14,4,kmeans,2,0.4284,0.2776,0.3368,0.3368,0.3698,0.2770,0.6515
1,5,0.14,0,kmeans,2,0.4060,0.2596,0.3167,0.3167,0.3244,0.2590,0.6290
1,10,0.01,20,kmeans,4,0.3431,0.2997,0.3200,0.3200,0.3189,0.2979,0.6025
1,5,0.14,8,kmeans,2,0.3852,0.2458,0.3001,0.3001,0.3059,0.2451,0.6191
100,na,na,0,kmeans,2,0.3694,0.2331,0.2858,0.2858,0.2904,0.2324,0.6129
100,na,na,12,kmeans,2,0.3740,0.2349,0.2886,0.2886,0.2878,0.2343,0.6126
70,na,na,12,kmeans,2,0.3692,0.2331,0.2858,0.2858,0.2861,0.2325,0.6104
70,na,na,8,kmeans,2,0.3578,0.2274,0.2781,0.2781,0.2839,0.2267,0.6076
70,na,na,0,kmeans,2,0.3747,0.2355,0.2893,0.2893,0.2821,0.2349,0.6093
1,8,0.08,0,kmeans,2,0.3618,0.2306,0.2817,0.2817,0.2817,0.2299,0.6058

# Evaluation for title.
70,na,na,4,kmeans,4,0.3182,0.3560,0.3360,0.3360,0.2708,0.3166,0.5421
100,na,na,4,kmeans,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220
100,na,na,0,kmeans,4,0.2920,0.3545,0.3202,0.3202,0.2644,0.2905,0.5188
50,na,na,4,kmeans,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402
70,na,na,20,kmeans,4,0.3111,0.3444,0.3269,0.3269,0.2463,0.3095,0.5301
100,na,na,8,kmeans,4,0.2923,0.3511,0.3190,0.3190,0.2457,0.2907,0.5096
100,na,na,12,kmeans,4,0.2886,0.3461,0.3147,0.3147,0.2394,0.2870,0.5060
1,5,0.21,8,maximin,5,0.1697,0.2237,0.1930,0.1930,0.2287,0.1676,0.4871
70,na,na,16,kmeans,4,0.3079,0.3366,0.3216,0.3216,0.2255,0.3063,0.5212
50,na,na,12,kmeans,4,0.3112,0.3252,0.3181,0.3181,0.2251,0.3095,0.5294
```

Observations:

- Using all fields (title+abstract+fulltext) achieved the best performance in ARI, followed by title+abs, then title. But the difference between the latter two is small.
- Optimum number of clusters (k) became somewhat more incoherent (4, 6 and 2) and smaller (2) for title+abs and title. It may be because the data set is small and it's more difficult to identify underlying clusters.
- When using only titles, maximin clustering worked better than kmeans.

Since we know there're four classes in advance, it would be more appropriate to compare the three cases above only for four clusters (i.e., only look at k=4).

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head
1,6,0.08,8,kmeans,4,0.3853,0.3094,0.3432,0.3432,0.3999,0.3076,0.6559
1,8,0.08,4,kmeans,4,0.3311,0.3124,0.3215,0.3215,0.3934,0.3107,0.6370
1,9,0.08,4,kmeans,4,0.3227,0.3073,0.3148,0.3148,0.3858,0.3055,0.6311
1,10,0.08,4,kmeans,4,0.3180,0.3066,0.3122,0.3122,0.3787,0.3048,0.6254
1,7,0.08,8,kmeans,4,0.3678,0.2960,0.3280,0.3280,0.3772,0.2941,0.6426
1,8,0.08,12,kmeans,4,0.3801,0.3158,0.3450,0.3450,0.3707,0.3140,0.6357
1,9,0.08,8,kmeans,4,0.3449,0.2759,0.3065,0.3065,0.3560,0.2739,0.6310
1,7,0.08,12,kmeans,4,0.3531,0.2771,0.3105,0.3105,0.3468,0.2751,0.6277
1,9,0.08,20,kmeans,4,0.3291,0.2577,0.2891,0.2891,0.3362,0.2557,0.6214
1,5,0.01,0,kmeans,4,0.3724,0.3243,0.3467,0.3467,0.3277,0.3226,0.6104

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head 
1,10,0.01,20,kmeans,4,0.3431,0.2997,0.3200,0.3200,0.3189,0.2979,0.6025
1,9,0.01,20,kmeans,4,0.3326,0.3348,0.3337,0.3337,0.2756,0.3309,0.5589
1,7,0.01,0,kmeans,4,0.3205,0.3433,0.3315,0.3315,0.2729,0.3188,0.5486
1,5,0.14,20,kmeans,4,0.3744,0.3790,0.3767,0.3767,0.2725,0.3728,0.5590
1,9,0.01,16,kmeans,4,0.3353,0.3302,0.3327,0.3327,0.2713,0.3284,0.5607
1,8,0.01,16,kmeans,4,0.3381,0.3346,0.3364,0.3364,0.2710,0.3329,0.5594
1,8,0.01,20,kmeans,4,0.3339,0.3279,0.3309,0.3309,0.2703,0.3262,0.5604
1,8,0.08,20,kmeans,4,0.3353,0.3378,0.3366,0.3366,0.2660,0.3336,0.5535
1,5,0.14,12,kmeans,4,0.3721,0.3776,0.3748,0.3748,0.2659,0.3705,0.5555
1,5,0.14,0,kmeans,4,0.3478,0.3667,0.3570,0.3570,0.2648,0.3462,0.5453


# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head
70,na,na,4,kmeans,4,0.3182,0.3560,0.3360,0.3360,0.2708,0.3166,0.5421
100,na,na,4,kmeans,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220
100,na,na,0,kmeans,4,0.2920,0.3545,0.3202,0.3202,0.2644,0.2905,0.5188
50,na,na,4,kmeans,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402
70,na,na,20,kmeans,4,0.3111,0.3444,0.3269,0.3269,0.2463,0.3095,0.5301
100,na,na,8,kmeans,4,0.2923,0.3511,0.3190,0.3190,0.2457,0.2907,0.5096
100,na,na,12,kmeans,4,0.2886,0.3461,0.3147,0.3147,0.2394,0.2870,0.5060
70,na,na,16,kmeans,4,0.3079,0.3366,0.3216,0.3216,0.2255,0.3063,0.5212
50,na,na,12,kmeans,4,0.3112,0.3252,0.3181,0.3181,0.2251,0.3095,0.5294
70,na,na,12,kmeans,4,0.3001,0.3287,0.3138,0.3138,0.2214,0.2985,0.5181
```

Observations:

- The tendency (fulltext > abstract > title) didn't change.
- Now, kmeans dominates the top 5 for title, too.

What if we look at v-measure-d?

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
1,5,0.01,0,kmeans,4,0.3724,0.3243,0.3467,0.3467,0.3277,0.3226,0.6104
1,8,0.08,12,kmeans,4,0.3801,0.3158,0.3450,0.3450,0.3707,0.3140,0.6357
1,6,0.08,8,kmeans,4,0.3853,0.3094,0.3432,0.3432,0.3999,0.3076,0.6559
1,10,0.60,20,kmeans,4,0.3512,0.3320,0.3414,0.3414,0.2294,0.3303,0.5494
1,7,0.40,0,kmeans,4,0.3300,0.3494,0.3394,0.3394,0.2150,0.3283,0.5189

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
70,na,na,6,kmeans,4,0.5718,0.2795,0.3754,0.3754,0.2093,0.2776,0.6541
70,na,na,4,kmeans,4,0.5643,0.2787,0.3731,0.3731,0.2080,0.2768,0.6524
70,na,na,18,kmeans,4,0.5687,0.2743,0.3701,0.3701,0.2033,0.2724,0.6523
70,na,na,10,kmeans,4,0.5631,0.2734,0.3681,0.3681,0.2047,0.2715,0.6524
70,na,na,16,kmeans,4,0.5667,0.2724,0.3679,0.3679,0.2017,0.2705,0.6519

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
50,na,na,20,kmeans,4,0.3104,0.3690,0.3372,0.3372,0.2009,0.3089,0.4826
70,na,na,4,kmeans,4,0.3182,0.3560,0.3360,0.3360,0.2708,0.3166,0.5421
50,na,na,0,kmeans,4,0.3080,0.3669,0.3349,0.3349,0.2050,0.3066,0.4847
100,na,na,4,kmeans,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220
50,na,na,16,kmeans,4,0.3062,0.3639,0.3326,0.3326,0.1974,0.3047,0.4804
```

And adjusted mutual information?

```bash
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,10,0.40,20,kmeans,4,0.3341,0.3410,0.3375,0.3375,0.2403,0.3324,0.5426
1,10,0.60,20,kmeans,4,0.3512,0.3320,0.3414,0.3414,0.2294,0.3303,0.5494
1,10,0.53,12,kmeans,4,0.3326,0.3315,0.3320,0.3320,0.2228,0.3298,0.5366
1,7,0.40,0,kmeans,4,0.3300,0.3494,0.3394,0.3394,0.2150,0.3283,0.5189
1,5,0.01,0,kmeans,4,0.3724,0.3243,0.3467,0.3467,0.3277,0.3226,0.6104

less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,5,0.14,20,kmeans,4,0.3744,0.3790,0.3767,0.3767,0.2725,0.3728,0.5590
1,5,0.14,12,kmeans,4,0.3721,0.3776,0.3748,0.3748,0.2659,0.3705,0.5555
1,5,0.14,16,kmeans,4,0.3690,0.3704,0.3697,0.3697,0.2564,0.3674,0.5526
1,5,0.21,12,kmeans,4,0.3683,0.3773,0.3727,0.3727,0.2519,0.3667,0.5458
1,5,0.27,16,kmeans,4,0.3681,0.3773,0.3726,0.3726,0.2205,0.3665,0.5286

less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
50,na,na,4,kmeans,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402
70,na,na,4,kmeans,4,0.3182,0.3560,0.3360,0.3360,0.2708,0.3166,0.5421
70,na,na,20,kmeans,4,0.3111,0.3444,0.3269,0.3269,0.2463,0.3095,0.5301
50,na,na,12,kmeans,4,0.3112,0.3252,0.3181,0.3181,0.2251,0.3095,0.5294
50,na,na,20,kmeans,4,0.3104,0.3690,0.3372,0.3372,0.2009,0.3089,0.4826
```

Observations:

- The tendency changed (abstract > fulltext > title).
- r is stable and d is not.
- For title+abstract, DF-based feature selection worked better than VCGS.  I suspect that this inconsistency is caused by the small data size and shouldn't be paid attention.  The following is the top five results using VCGS.

```bash
# Evaluation for title+abstract using VCGS.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | grep -P "^1," | sort -t',' -k9 -nr | head -5
1,8,0.27,8,kmeans,4,0.3880,0.3374,0.3609,0.3609,0.3393,0.3356,0.6166
1,8,0.60,0,kmeans,4,0.3341,0.3589,0.3461,0.3461,0.2192,0.3326,0.5139
1,8,0.34,16,kmeans,4,0.3350,0.3546,0.3445,0.3445,0.2182,0.3334,0.5167
1,8,0.53,18,kmeans,4,0.3300,0.3568,0.3429,0.3429,0.2228,0.3284,0.5139
1,8,0.27,12,kmeans,4,0.3339,0.3508,0.3422,0.3422,0.2305,0.3323,0.5261
'''

# Evaluation metrics

To see their difference empirically, the following computes Pearson's correlation coefficient between every pair of metrics **by R**, not python.

```R
cls <- c(ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
> x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls) 
> cor(x[,9:13])
            vd          v       ari       ami        fms
vd  1.00000000 1.00000000 0.7504809 0.9504065 0.06378729
v   1.00000000 1.00000000 0.7504809 0.9504065 0.06378729
ari 0.75048089 0.75048089 1.0000000 0.8168620 0.60705975
ami 0.95040651 0.95040651 0.8168620 1.0000000 0.20693144
fms 0.06378729 0.06378729 0.6070598 0.2069314 1.00000000
```

ami and vd (or v) are found to be strongly correlated.  ari has relatively strong correlation with the three but it's not as strong as theirs.  On the other hand, fms has very weak to moderate correlations with the others.  The following shows the scatter plot for each pair of metrics, again by R.

```R
plot(x[,9:13])
```

<img src="scatter_sgl.png" width="600">


