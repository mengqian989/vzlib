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
  - 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.55
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
nice python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval_sgl.csv --single
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order:

> df,r,d,n,alg,k,c,h,vd,v,ari,ami,fms,prec

where 

- df is the minimal document frequency
- r and d are VCGS's parameters
- n is the number of dimensions for SVD
- alg is an clustering algorithm (kmeans or maximin)
- k is the number of clusters. This is set beforehand for kNN but is determined by the algorithm for maximin. 
- the rest are evaluation measures: c = completeness, h = homogeneity, vd = v-measure-d, v = v-measure, ari = adjusted rand index, ami = adjusted mutual information, and fms = Fowlkes-Mallows index.  
- Precision is a variant of homogeneity (from Javed's JASIST paper)

Notes:

- v-measure-d and v-measure are different in how they treat multi-label cases.  The former treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.
- When df is greater than 1 (e.g., 10), VCGS is not applied, meaning that terms with document frequencies greater than this parameter are all treated as keywords.  This is for investigating the effectiness of VCGS in comparison with DF-based feature selection.

Now let's look at the five best parameter combinations based on adjusted rand index (ARI).

```bash
# ranking by ari 
less brca_med_top4_eval_sgl.csv | sort -t',' -k11 -nr | head
1,6,0.25,0,kmeans,4,0.4203,0.3812,0.3998,0.3998,0.3726,0.3810,0.6608,0.8236
1,5,0.20,0,kmeans,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8252
1,9,0.15,0,kmeans,4,0.3973,0.3685,0.3824,0.3824,0.3709,0.3683,0.6556,0.7971
1,8,0.20,0,kmeans,4,0.3950,0.3634,0.3786,0.3786,0.3626,0.3632,0.6524,0.7989
1,10,0.30,0,kmeans,4,0.3940,0.3647,0.3788,0.3788,0.3613,0.3645,0.6502,0.7992
1,5,0.10,0,kmeans,4,0.3959,0.3597,0.3769,0.3769,0.3612,0.3595,0.6544,0.8026
1,6,0.15,0,kmeans,4,0.4016,0.3575,0.3783,0.3783,0.3592,0.3573,0.6569,0.8099
1,8,0.30,0,kmeans,4,0.4035,0.3642,0.3828,0.3828,0.3586,0.3640,0.6537,0.8155
1,7,0.30,0,kmeans,4,0.4043,0.3662,0.3843,0.3843,0.3581,0.3660,0.6526,0.8177
1,5,0.15,0,kmeans,4,0.3962,0.3596,0.3770,0.3770,0.3569,0.3594,0.6521,0.8074

Observations:

- good ami seems to come with good prec, but the opposite doesn't hold.
- df = 1 dominates the top 10, which means VCGS is better than DF-based feature selection.
- kmeans works better than maximin.
- Good r and d values seem more or less random and may be difficult to find optimum settings.  More investigation is needed to see how sensitive the performance is to these parameters.
- SVD gives no advantage.

Let's look at precision-sorted results.

# ranking by prec
less brca_med_top4_eval_sgl.csv | grep kmeans | sort -t',' -k14 -nr | head
1,7,0.20,0,kmeans,4,0.3490,0.3160,0.3317,0.3317,0.2391,0.3143,0.5600,0.8274
1,8,0.15,16,kmeans,4,0.3168,0.2677,0.2902,0.2902,0.1676,0.2658,0.5345,0.8273
1,5,0.35,20,kmeans,4,0.2240,0.2043,0.2137,0.2137,0.0332,0.2022,0.4556,0.8258
1,5,0.30,20,kmeans,4,0.2240,0.2043,0.2137,0.2137,0.0332,0.2022,0.4556,0.8258
1,7,0.45,20,kmeans,4,0.2338,0.2239,0.2287,0.2287,0.0591,0.2219,0.4560,0.8257
1,7,0.40,16,kmeans,4,0.2287,0.2139,0.2211,0.2211,0.0524,0.2119,0.4582,0.8255
1,8,0.15,20,kmeans,4,0.3094,0.2698,0.2883,0.2883,0.2029,0.2680,0.5447,0.8252
1,5,0.20,16,kmeans,4,0.3423,0.2908,0.3145,0.3145,0.1508,0.2890,0.5322,0.8231
1,7,0.15,20,kmeans,4,0.3589,0.2717,0.3092,0.3092,0.2076,0.2697,0.5717,0.8216
1,6,0.35,12,kmeans,4,0.3467,0.3077,0.3260,0.3260,0.1816,0.3059,0.5382,0.8192
```

Good ami seems to come with good prec, but the opposite doesn't hold.

Then, let's see how good the DF-based feature selection is.  The following shows the ten best results in ari where minimum DF was set to other than 1.

```bash
less brca_med_top4_eval_sgl.csv | grep -vP '^1,' | sort -t',' -k11 -nr | head
100,na,na,20,kmeans,4,0.3676,0.3484,0.3577,0.3577,0.3374,0.3482,0.6311,0.7863
30,na,na,8,maximin,5,0.2145,0.2931,0.2477,0.2477,0.2161,0.2143,0.4821,0.6679
70,na,na,0,kmeans,4,0.2722,0.2835,0.2778,0.2778,0.2037,0.2720,0.5263,0.7058
50,na,na,0,kmeans,4,0.2693,0.2821,0.2756,0.2756,0.1978,0.2691,0.5209,0.7083
10,na,na,20,kmeans,4,0.2622,0.2721,0.2671,0.2671,0.1934,0.2620,0.5205,0.7104
30,na,na,20,kmeans,4,0.2619,0.2721,0.2669,0.2669,0.1900,0.2617,0.5179,0.7089
30,na,na,8,maximin,3,0.2165,0.2129,0.2147,0.2147,0.1880,0.2128,0.5080,   nan
30,na,na,8,maximin,3,0.2165,0.2129,0.2147,0.2147,0.1880,0.2128,0.5080,   nan
10,na,na,16,kmeans,4,0.2589,0.2705,0.2646,0.2646,0.1863,0.2587,0.5137,0.7131
50,na,na,20,kmeans,4,0.2598,0.2715,0.2655,0.2655,0.1854,0.2596,0.5133,0.7098
```

Their ari was found to be around 0.2 (except for 0.3374), which is pretty low.  So VCGS does work!  

How about v-measure or ami?

```bash
# v-measure
less brca_med_top4_eval_sgl.csv | sort -t',' -k10 -nr | grep ',4,0' | head -5
1,6,0.25,0,kmeans,4,0.4203,0.3812,0.3998,0.3998,0.3726,0.3810,0.6608,0.8236
1,5,0.20,0,kmeans,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8252
1,8,0.55,12,kmeans,4,0.4035,0.3774,0.3900,0.3900,0.3270,0.3773,0.6275,0.8467
1,6,0.45,20,kmeans,4,0.4036,0.3735,0.3880,0.3880,0.3238,0.3733,0.6282,0.8459
1,6,0.35,20,kmeans,4,0.4067,0.3666,0.3856,0.3856,0.3337,0.3664,0.6397,0.8404

# ami
less brca_med_top4_eval_sgl.csv | sort -t',' -k12 -nr | grep ',4,0' | head -5
1,6,0.25,0,kmeans,4,0.4203,0.3812,0.3998,0.3998,0.3726,0.3810,0.6608,0.8236
1,8,0.55,12,kmeans,4,0.4035,0.3774,0.3900,0.3900,0.3270,0.3773,0.6275,0.8467
1,5,0.20,0,kmeans,4,0.4236,0.3772,0.3990,0.3990,0.3713,0.3770,0.6636,0.8252
1,6,0.45,20,kmeans,4,0.4036,0.3735,0.3880,0.3880,0.3238,0.3733,0.6282,0.8459
1,7,0.55,12,kmeans,4,0.3911,0.3700,0.3802,0.3802,0.3040,0.3698,0.6115,0.8493
```

Observations:

- Overall, we see similar patterns to ari.
  - df = 1 still works better (VCGS is better).
  - kmeans still works better.
- LSA is sometimes effective.
- Two results (ranking) are quite similar.

## Full texts vs. abstracts (smaller data)

The aim of the following experiments is to show, if any, the advantage of full-text data over abstracts for clustering biomedical articles.  First, run eval.py script. (We can run them in parallel as follows. Takes less than an hour on miksa3.)

```bash
nice python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_all_sgl.csv --single &
nice python eval.py --input brca_pmc_top4.txt.gz --fields title,abstract --output brca_top4_eval_ta_sgl.csv --single &
nice python eval.py --input brca_pmc_top4.txt.gz --fields title --output brca_top4_eval_t_sgl.csv --single &
```

Let's look at the result based on ARI.

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
1,5,0.10,20,kmeans,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749
1,5,0.55,4,maximin,4,0.3128,0.3442,0.3277,0.3277,0.3433,0.3111,0.5845,0.7008
30,na,na,12,kmeans,4,0.3496,0.3078,0.3274,0.3274,0.3088,0.3060,0.5974,0.7224
1,7,0.05,0,kmeans,4,0.3205,0.3433,0.3315,0.3315,0.2729,0.3188,0.5486,0.7290
1,9,0.05,20,kmeans,4,0.3322,0.3269,0.3296,0.3296,0.2655,0.3252,0.5573,0.7568
1,5,0.15,0,kmeans,4,0.3478,0.3667,0.3570,0.3570,0.2648,0.3462,0.5453,0.7884
1,8,0.05,20,kmeans,4,0.3330,0.3256,0.3293,0.3293,0.2621,0.3238,0.5570,0.7598
1,7,0.15,0,kmeans,4,0.3332,0.3543,0.3434,0.3434,0.2619,0.3316,0.5394,0.7784
1,5,0.20,12,kmeans,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.8019
1,5,0.15,20,kmeans,4,0.3667,0.3689,0.3678,0.3678,0.2600,0.3651,0.5531,0.7921

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head
1,6,0.55,4,maximin,4,0.1876,0.2099,0.1981,0.1981,0.2780,0.1858,0.5440,0.6219
70,na,na,4,kmeans,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.8011
100,na,na,4,kmeans,4,0.3048,0.3681,0.3334,0.3334,0.2669,0.3033,0.5220,0.7994
100,na,na,0,kmeans,4,0.2920,0.3545,0.3202,0.3202,0.2644,0.2905,0.5188,0.7929
50,na,na,4,kmeans,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402,0.8001
100,na,na,8,kmeans,4,0.2923,0.3511,0.3190,0.3190,0.2457,0.2907,0.5096,0.7957
70,na,na,20,kmeans,4,0.3071,0.3397,0.3225,0.3225,0.2412,0.3054,0.5272,0.7998
70,na,na,8,kmeans,4,0.2977,0.3293,0.3127,0.3127,0.2317,0.2961,0.5212,0.7960
50,na,na,8,kmeans,4,0.3088,0.3223,0.3154,0.3154,0.2212,0.3071,0.5275,0.7972
70,na,na,12,kmeans,4,0.3035,0.3308,0.3165,0.3165,0.2178,0.3018,0.5174,0.8013
```

Observations:

- Using all fields (title+abstract+fulltext) achieved the best performance in ARI, followed by title+abs, then title.
- When using only titles, DF-based feature selection worked better than VCGS. This would be due to the small number of words from titles (therefore not many keywords were identified by VCGS).  This tendency is also seen in title+abstract.
- kmeans generally works better than maximin.
- LSA's effectiveness is not very clear.

Observations:

- The tendency (fulltext > abstract > title) didn't change.
- kmeans performs better than maximin.
- LSA generally helps.
- R is less sensitive than D, which means it's difficult to find good D value).
- VCGS doesn't work for titles (only).  If we look at the cases where VCGS was used... 

Sorted by precision.

```bash
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k14 -nr | head -5
1,7,0.20,0,kmeans,4,0.3490,0.3160,0.3317,0.3317,0.2391,0.3143,0.5600,0.8274
1,8,0.15,16,kmeans,4,0.3168,0.2677,0.2902,0.2902,0.1676,0.2658,0.5345,0.8273
1,8,0.45,20,kmeans,4,0.2341,0.2230,0.2284,0.2284,0.0613,0.2211,0.4581,0.8269
1,5,0.35,20,kmeans,4,0.2240,0.2043,0.2137,0.2137,0.0332,0.2022,0.4556,0.8258
1,5,0.30,20,kmeans,4,0.2240,0.2043,0.2137,0.2137,0.0332,0.2022,0.4556,0.8258

less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k14 -nr | head -5
1,5,0.10,20,kmeans,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749
1,7,0.55,8,kmeans,4,0.3600,0.3647,0.3623,0.3623,0.1880,0.3584,0.5139,0.8128
1,5,0.45,8,kmeans,4,0.3502,0.3374,0.3437,0.3437,0.1674,0.3357,0.5147,0.8073
1,6,0.55,16,kmeans,4,0.3494,0.3557,0.3525,0.3525,0.1794,0.3477,0.5076,0.8068
1,5,0.20,16,kmeans,4,0.3843,0.3861,0.3852,0.3852,0.2547,0.3828,0.5517,0.8064

less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k14 -nr | head -5
50,na,na,0,kmeans,4,0.3080,0.3669,0.3349,0.3349,0.2050,0.3066,0.4847,0.8194
30,na,na,0,kmeans,4,0.2894,0.3360,0.3110,0.3110,0.1654,0.2878,0.4673,0.8117
30,na,na,8,kmeans,4,0.3158,0.3093,0.3125,0.3125,0.2155,0.3075,0.5343,0.8094
70,na,na,12,kmeans,4,0.3035,0.3308,0.3165,0.3165,0.2178,0.3018,0.5174,0.8013
70,na,na,4,kmeans,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.8011
```

Sorted by adjusted mutual information?

```bash
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,7,0.40,0,kmeans,4,0.3300,0.3494,0.3394,0.3394,0.2150,0.3283,0.5189,0.7570
1,9,0.55,12,kmeans,4,0.3508,0.3272,0.3386,0.3386,0.2172,0.3255,0.5455,0.8208
1,8,0.55,0,kmeans,4,0.3290,0.3262,0.3276,0.3276,0.2256,0.3245,0.5400,0.7767
1,5,0.05,0,kmeans,4,0.3724,0.3243,0.3467,0.3467,0.3277,0.3226,0.6104,0.7807
1,10,0.40,0,kmeans,4,0.3240,0.3409,0.3322,0.3322,0.2065,0.3224,0.5154,0.7489

less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,5,0.10,20,kmeans,4,0.4377,0.3898,0.4123,0.4123,0.3473,0.3882,0.6198,0.8749
1,5,0.20,16,kmeans,4,0.3843,0.3861,0.3852,0.3852,0.2547,0.3828,0.5517,0.8064
1,5,0.20,20,kmeans,4,0.3734,0.3843,0.3788,0.3788,0.2490,0.3719,0.5430,0.8036
1,5,0.20,12,kmeans,4,0.3696,0.3862,0.3777,0.3777,0.2603,0.3681,0.5456,0.8019
1,6,0.45,20,kmeans,4,0.3672,0.3740,0.3705,0.3705,0.1970,0.3656,0.5179,0.7963

less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
50,na,na,4,kmeans,4,0.3228,0.3405,0.3314,0.3314,0.2476,0.3212,0.5402,0.8001
70,na,na,4,kmeans,4,0.3176,0.3555,0.3355,0.3355,0.2712,0.3160,0.5421,0.8011
30,na,na,8,kmeans,4,0.3158,0.3093,0.3125,0.3125,0.2155,0.3075,0.5343,0.8094
50,na,na,8,kmeans,4,0.3088,0.3223,0.3154,0.3154,0.2212,0.3071,0.5275,0.7972
50,na,na,0,kmeans,4,0.3080,0.3669,0.3349,0.3349,0.2050,0.3066,0.4847,0.8194
```

Observations:

- The tendency changed (abstract > fulltext > title).


# Evaluation metrics

To see the difference among different evaluation metrics empirically, the following shows Pearson's correlation coefficient between every pair of metrics **by R**, not python.

```R
cls <- c(ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls) 
cor(x[,9:13])
           vd         v       ari       ami       fms
vd  1.0000000 1.0000000 0.7603266 0.9333792 0.3347924
v   1.0000000 1.0000000 0.7603266 0.9333792 0.3347924
ari 0.7603266 0.7603266 1.0000000 0.7269075 0.7756461
ami 0.9333792 0.9333792 0.7269075 1.0000000 0.3483514
fms 0.3347924 0.3347924 0.7756461 0.3483514 1.0000000
```

ami and vd (or v) are found to be strongly correlated.  ari has relatively strong correlation with the three but it's not as strong as theirs.  On the other hand, fms has very weak to moderate correlations with the others.  The following shows the scatter plot for each pair of metrics, again by R.

```R
plot(x[,9:13])
```

<img src="figs/scatter_sgl.png" width="600">

Focusing on only V-measure, ARI and AMI...

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
pairs(x[,c(10,11,12)], upper.panel = panel.cor)
```

<img src="figs/scatter_three.png" width="400">

How do r and d affect cluster quality? Note that P is used to refer to d below.

```R
cls <- c(r="numeric", d="numeric", n="numeric", ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls,na.strings="na")
x[x$df == 1 & x$alg == "kmeans" & x$n > 0 & x$k == 4, c(2,3,4,11)] -> y
colnames(y) = c("R", "P", "n", "ARI")

library(magrittr) # for pipe operator
library(dplyr)    # for grouping

# compute mean by group
ag <- y %>% 
        group_by(R, P) %>% 
        summarise(ARI = mean(ARI))

# plot
quartz("",6,5) # this is for Mac
par(mar=c(5,4,1,1))
sp = ggplot(data=ag, mapping=aes(x=factor(R), y=factor(P), color=ARI)) + geom_point(alpha=.9, size=ag$ARI*40)
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

What if we look at only a certain range of r and d?

```R
cls <- c(r="numeric", d="numeric", n="numeric", ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric") 
x = read.csv("brca_med_top4_eval_sgl.csv",header=TRUE,colClasses=cls,na.strings="na")
x[x$df == 1 & x$alg == "kmeans" & x$n > 0 & x$k == 4 & x$d >= 0.08 & x$d <= 0.21 & x$r <= 8, c(2,3,4,11)] -> y
colnames(y) = c("R", "P", "n", "ARI")

quartz("",6,5) # this is for Mac
par(mar=c(5,4,1,1))

sp3 = ggplot(data=y, mapping=aes(x=factor(n), y=ARI)) + geom_boxplot()
sp3 + geom_jitter(alpha=.5, color="tomato", height=0, size=3) + theme_bw() + theme(panel.grid=element_blank()) + labs(x=expression(paste("Number of dimensions ", italic(n))))
```

<img src="figs/n_and_ari_with_limited_range_of_R_and_P.png" width="400">
