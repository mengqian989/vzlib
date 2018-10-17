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

- Minimal document frequencies: 1, 10, 30, 50, 70, 100
- R: 3, 5, 7, 9, 11
- D: 0.01 0.08 0.14 0.21 0.27 0.34 0.40 0.47 0.53 0.60
- Number of components for SVD: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20
  - When set to 0, SVD is not applied.
- Clustering algorithms: kNN or maximin
- Number of clusters for kNN: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20

## Abstracts (larger data)

Run an evaluation script for medline data created above. Different combinations of parameters are executed. (It takes about 10 hours to complete.)

```bash
python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval_sgl.csv --single
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order:

> df,r,d,n,alg,k,c,h,vd,v,ari,ami,fms

where 

- df is a df cutoff threshold (words with document frequency equal or smaller than df are ignored)
- r and d are VCGS's parameters
- n is the number of dimensions (components) for SVD
- alg is an clustering algorithm (kmeans or maximin)
- k is the number of clusters
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
less brca_top4_eval_all_sgl.csv | sort -t',' -k11 -nr | head -5
1,8,0.08,4,kmeans,4,0.3281,0.3056,0.3164,0.3164,0.3914,0.3038,0.6372
1,8,0.08,8,kmeans,4,0.3542,0.2850,0.3159,0.3159,0.3644,0.2831,0.6352
1,8,0.01,0,kmeans,6,0.2865,0.3238,0.3040,0.3040,0.3435,0.2838,0.5920
1,8,0.08,0,kmeans,2,0.3873,0.2491,0.3032,0.3032,0.3231,0.2485,0.6269
1,8,0.08,16,kmeans,4,0.3567,0.2922,0.3212,0.3212,0.3095,0.2903,0.6041

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | sort -t',' -k11 -nr | head -5
1,8,0.27,8,kmeans,4,0.3880,0.3374,0.3609,0.3609,0.3393,0.3356,0.6166
1,8,0.08,20,kmeans,6,0.3523,0.3981,0.3738,0.3738,0.2911,0.3498,0.5626
1,8,0.08,0,kmeans,2,0.3618,0.2306,0.2817,0.2817,0.2817,0.2299,0.6058
1,9,0.14,0,kmeans,4,0.2534,0.2636,0.2584,0.2584,0.2803,0.2516,0.5654
1,8,0.27,20,kmeans,2,0.3785,0.2370,0.2915,0.2915,0.2766,0.2364,0.6070

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | sort -t',' -k11 -nr | head -5
1,8,0.08,2,maximin,2,0.3521,0.2179,0.2692,0.2692,0.3256,0.2172,0.6370
1,8,0.01,2,maximin,2,0.3464,0.2137,0.2644,0.2644,0.3200,0.2131,0.6345
1,8,0.21,2,maximin,2,0.3419,0.2093,0.2597,0.2597,0.3107,0.2087,0.6310
1,8,0.14,2,maximin,2,0.3427,0.2087,0.2594,0.2594,0.3094,0.2080,0.6315
1,8,0.27,2,maximin,2,0.3301,0.1977,0.2473,0.2473,0.2904,0.1970,0.6246
```

Observations:

- Using all fields (title+abstract+fulltext) achieved the best performance in ARI, followed by title+abs, then title. But the difference between the latter two is small.
- Optimum number of clusters (k) became somewhat more incoherent (4, 6 and 2) and smaller (2) for title+abs and title. It may be because the data set is small and it's more difficult to identify underlying clusters.
- When using only titles, maximin clustering worked better than kmeans.

Since we know there're four classes in advance, it would be more appropriate to compare the three cases above only for four clusters (i.e., only look at k=4).

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
1,8,0.08,4,kmeans,4,0.3281,0.3056,0.3164,0.3164,0.3914,0.3038,0.6372
1,8,0.08,8,kmeans,4,0.3542,0.2850,0.3159,0.3159,0.3644,0.2831,0.6352
1,8,0.08,16,kmeans,4,0.3567,0.2922,0.3212,0.3212,0.3095,0.2903,0.6041
1,8,0.08,10,kmeans,4,0.3326,0.2593,0.2914,0.2914,0.3062,0.2573,0.6064
1,8,0.01,0,kmeans,4,0.3267,0.3071,0.3166,0.3166,0.3041,0.3053,0.5906

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
1,8,0.27,8,kmeans,4,0.3880,0.3374,0.3609,0.3609,0.3393,0.3356,0.6166
1,9,0.14,0,kmeans,4,0.2534,0.2636,0.2584,0.2584,0.2803,0.2516,0.5654
1,9,0.14,6,kmeans,4,0.3378,0.2837,0.3084,0.3084,0.2715,0.2818,0.5899
1,8,0.01,20,kmeans,4,0.3357,0.3300,0.3328,0.3328,0.2705,0.3282,0.5601
1,8,0.01,16,kmeans,4,0.3345,0.3283,0.3314,0.3314,0.2684,0.3265,0.5597

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
1,8,0.21,0,kmeans,4,0.2379,0.2503,0.2439,0.2439,0.1793,0.2361,0.4925
1,8,0.08,8,kmeans,4,0.2319,0.2372,0.2345,0.2345,0.1680,0.2299,0.4922
1,8,0.34,12,maximin,4,0.1671,0.2063,0.1846,0.1846,0.1610,0.1654,0.4434
1,8,0.08,2,kmeans,4,0.2206,0.2353,0.2277,0.2277,0.1610,0.2187,0.4800
1,8,0.01,2,kmeans,4,0.2197,0.2341,0.2267,0.2267,0.1598,0.2178,0.4795
```

Observations:

- The tendency (fulltext > abstract > title) didn't change.
- Now, kmeans dominates the top 5 for title, too.

What if we look at v-measure-d?

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
1,8,0.53,12,kmeans,4,0.3598,0.3289,0.3437,0.3437,0.2091,0.3272,0.5464
1,8,0.47,16,kmeans,4,0.3542,0.3181,0.3352,0.3352,0.1891,0.3163,0.5401
1,8,0.47,10,kmeans,4,0.3429,0.3119,0.3267,0.3267,0.1949,0.3101,0.5390
1,8,0.47,14,kmeans,4,0.3228,0.3254,0.3241,0.3241,0.1852,0.3211,0.5141
1,8,0.53,0,kmeans,4,0.3272,0.3204,0.3238,0.3238,0.2196,0.3187,0.5390

# Evaluation for title+abstract.
less brca_top4_eval_ta_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
70,na,na,6,kmeans,4,0.5718,0.2795,0.3754,0.3754,0.2093,0.2776,0.6541
70,na,na,4,kmeans,4,0.5643,0.2787,0.3731,0.3731,0.2080,0.2768,0.6524
70,na,na,18,kmeans,4,0.5687,0.2743,0.3701,0.3701,0.2033,0.2724,0.6523
70,na,na,10,kmeans,4,0.5631,0.2734,0.3681,0.3681,0.2047,0.2715,0.6524
70,na,na,16,kmeans,4,0.5667,0.2724,0.3679,0.3679,0.2017,0.2705,0.6519

# Evaluation for title.
less brca_top4_eval_t_sgl.csv | grep ",4,0." | sort -t',' -k9 -nr | head -5
1,8,0.60,0,kmeans,4,0.2485,0.2868,0.2663,0.2663,0.1266,0.2468,0.4439
1,8,0.34,20,kmeans,4,0.2377,0.2719,0.2536,0.2536,0.1141,0.2360,0.4387
1,8,0.21,0,kmeans,4,0.2379,0.2503,0.2439,0.2439,0.1793,0.2361,0.4925
1,8,0.21,6,kmeans,4,0.2368,0.2425,0.2396,0.2396,0.1536,0.2349,0.4855
1,8,0.08,8,kmeans,4,0.2319,0.2372,0.2345,0.2345,0.1680,0.2299,0.4922
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


