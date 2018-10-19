# Data preparation

Got articles for the query "**breast neoplasms[MeSH Major Topic]**" from pubmed on September 21, 2018 and saved as brca_med.xml.  

- brca_med.xml contains 224,940 articles.  

Did the same for pmc (as pmc doesn't give mesh terms) and save as brca_pmc.xml. 

- brca_pmc.xml contains 39,332 articles.

So, 39,332 / 224,940 = 17.5% of the articles have full texts.

Look at the mesh term distribution. Note that only major mesh terms are considered (--major) and mesh terms are generalized (--generalize) up to the level specified by **target_mesh** variable in xml2tsv_med.py. 

```bash
python xml2tsv_med.py --input data/brca_med.xml.gz --generalize --major --code > brca_med.txt

cut -f 4 brca_med.txt | perl -npe 's/\|/\n/g' | sort | uniq -c | sort -nr | less
  11115 Carcinoma, Ductal, Breast
   3475 Carcinoma, Lobular
   2588 Triple Negative Breast Neoplasms
   1955 Breast Neoplasms, Male
    342 Inflammatory Breast Neoplasms
    155 Hereditary Breast and Ovarian Cancer Syndrome
    100 Unilateral Breast Neoplasms
     61 Breast Carcinoma In Situ
```

Use only top 4 frequent MeSH. (Specify **classes** variables as follows in extract.py.)

> classes = {"Carcinoma, Ductal, Breast",
>            "Carcinoma, Lobular",
>            "Triple Negative Breast Neoplasms",
>            "Breast Neoplasms, Male"}

Run extract.py again.  (Later found that --major didn't make difference since there were no MeSH terms under the top four MeSH terms in the MeSH tree.  So, --major and --code may be omitted.)

```bash
python xml2tsv_med.py --input data/brca_med.xml.gz --generalize --major --code --restrict > brca_med_top4.txt
```

This results in 16,576 articles annotated with at least one of the four mesh terms.

```bash
wc -l brca_med_top4.txt 
16576 brca_med_top4.txt
```

Make sure the distribution of the classes is the same as the above but only top four terms.

```bash
cut -f 4 brca_med_top4.txt | perl -npe 's/[\|\+]/\n/g' | sort | uniq -c | sort -nr
  11115 Carcinoma, Ductal, Breast
   3475 Carcinoma, Lobular
   2588 Triple Negative Breast Neoplasms
   1955 Breast Neoplasms, Male
```

Finally create the data set with full text by adding body text extracted from plos_pmc.xml.

```bash
python xml2tsv_pmc.py > brca_pmc_top4.txt
```

Count the number of articles and look at the distribution of classes.

```bash
wc -l brca_pmc_top4.txt
1932 brca_pmc_top4.txt

cut -f 5 brca_pmc_top4.txt | perl -npe 's/\|/\n/g' | sort | uniq -c | sort -nr
    935 Carcinoma, Ductal, Breast
    824 Triple Negative Breast Neoplasms
    290 Carcinoma, Lobular
    141 Breast Neoplasms, Male
```

# Experiments

## Abstracts (larger data)

Run an evaluation script for medline data created above. Different combinations of parameters are executed. (It takes about 10 hours to complete.)

```bash
nice python eval.py --input brca_med_top4.txt.gz --output brca_med_top4_eval.csv &
```

The resulting file has a set of given parameters and evaluation metric values for each line in the following order:

> df,r,d,n,k,c,h,vd,v,ari,ami,fms

where 

- df is a df cutoff threshold (words with document frequency equal or smaller than df are ignored)
- r and d are VCGS's parameters
- n is the number of dimensions (components) for SVD
- alg is an clustering algorithm (kmeans or maximin)
- k is the number of clusters
- the rest are evaluation measures: c = completeness, h = homogeneity, vd = v-measure-d, v = v-measure, ari = adjusted rand index, ami = adjusted mutual information, and fms = Fowlkes-Mallows index.  

Notes:

- v-measure-d and v-measure are different in how to treat multi-label cases.  The former treats (A, M1) and (A, M2) with evenly divided importance in evaluation, and the latter treats them as independent instances in evaluation.
- When df is greater than 1, VCGS is not applied.  This is for investigating the effectiness of VCGS in comparison with DF-based feature selection.

Now let's look at the five best parameter combinations based on adjusted rand index (ari).
Since we know there're four classes in advance, it would be more appropriate to look at only for four clusters (i.e., k=4).  The following show the results for k = any number and k = 4.

```bash
# any number of clusters
less brca_med_top4_eval.csv | sort -t',' -k11 -nr | head -5
1,9,0.01,20,kmeans,6,0.3274,0.3572,0.3417,0.2960,0.2540,0.2842,0.5637
1,8,0.34,20,kmeans,4,0.3402,0.2998,0.3187,0.2840,0.2343,0.2635,0.5754
1,10,0.47,20,kmeans,4,0.3351,0.3003,0.3168,0.2820,0.2326,0.2637,0.5706
1,8,0.34,16,kmeans,4,0.3382,0.2988,0.3173,0.2829,0.2311,0.2628,0.5731
1,9,0.40,12,kmeans,4,0.3347,0.2995,0.3161,0.2817,0.2298,0.2633,0.5693

# number of clusters = 4
less brca_med_top4_eval.csv | grep ',4,0' | sort -t',' -k11 -nr | head -5
1,8,0.34,20,kmeans,4,0.3402,0.2998,0.3187,0.2840,0.2343,0.2635,0.5754
1,10,0.47,20,kmeans,4,0.3351,0.3003,0.3168,0.2820,0.2326,0.2637,0.5706
1,8,0.34,16,kmeans,4,0.3382,0.2988,0.3173,0.2829,0.2311,0.2628,0.5731
1,9,0.40,12,kmeans,4,0.3347,0.2995,0.3161,0.2817,0.2298,0.2633,0.5693
1,6,0.27,20,kmeans,4,0.3338,0.2951,0.3133,0.2790,0.2279,0.2593,0.5706
```

Observations:

- df = 1 dominates the top ranked ones, which means VCGS is better than DF-based feature selection.
- kmeans works better than maximin.
- r = 9~10 and d = 0.34~0.47 worked generally well. More investigation is needed to see if performance is sensitive to these parameters (it's not a very good property if it is).
- SVD with the number of components (n) being 20 seem to be effective.  Hight n needs to be tested.
- k = 4 worked generally good, which is expected as we have four underlying classes (mesh terms)

Based on the first observation above, let's see how good the DF-based feature selection is.  The following shows the five best results in ari where minimum DF was set to other than 1.

```bash
# any number of clusters
less brca_med_top4_eval.csv | grep -vP '^1,' | sort -t',' -k11 -nr | head -5
30,na,na,0,kmeans,6,0.2424,0.3274,0.2786,0.2463,0.1478,0.2150,0.4321
10,na,na,0,kmeans,6,0.2424,0.3267,0.2783,0.2463,0.1474,0.2152,0.4325
10,na,na,0,kmeans,8,0.2395,0.3636,0.2888,0.2497,0.1469,0.2074,0.4182
10,na,na,8,kmeans,6,0.2346,0.3184,0.2701,0.2394,0.1461,0.2086,0.4294
50,na,na,0,kmeans,6,0.2402,0.3243,0.2760,0.2437,0.1450,0.2128,0.4309

# number of clusters = 4
less brca_med_top4_eval.csv | grep -vP '^1,' | grep ',4,0' | sort -t',' -k11 -nr | head -5
70,na,na,8,kmeans,4,0.2202,0.1977,0.2083,0.1867,0.1304,0.1771,0.4924
70,na,na,20,kmeans,4,0.2184,0.1939,0.2055,0.1841,0.1299,0.1737,0.4955
100,na,na,8,kmeans,4,0.2194,0.1975,0.2079,0.1863,0.1290,0.1769,0.4904
50,na,na,8,maximin,4,0.1592,0.1776,0.1679,0.1487,0.1192,0.1418,0.4344
30,na,na,20,kmeans,4,0.2039,0.2142,0.2089,0.1852,0.1136,0.1814,0.4458
```

The best ari was found to be 0.1478, which is pretty low.  So VCGS does work!  

What if we look at v-measure-d or ami? (showing k=4 only)

```bash
# v-measure
less brca_med_top4_eval.csv | sort -t',' -k9 -nr | grep ',4,0' | head -5
1,9,0.60,12,kmeans,4,0.3503,0.3181,0.3334,0.2967,0.2263,0.2790,0.5628
1,8,0.53,12,kmeans,4,0.3502,0.3175,0.3331,0.2963,0.2254,0.2783,0.5627
1,8,0.60,12,kmeans,4,0.3433,0.3153,0.3287,0.2920,0.2150,0.2760,0.5528
1,6,0.53,20,kmeans,4,0.3362,0.3135,0.3244,0.2888,0.2072,0.2749,0.5441
1,8,0.34,20,kmeans,4,0.3402,0.2998,0.3187,0.2840,0.2343,0.2635,0.5754

# ami
less brca_med_top4_eval.csv | sort -t',' -k12 -nr | grep ',4,0' | head -5
1,9,0.60,12,kmeans,4,0.3503,0.3181,0.3334,0.2967,0.2263,0.2790,0.5628
1,8,0.53,12,kmeans,4,0.3502,0.3175,0.3331,0.2963,0.2254,0.2783,0.5627
1,8,0.60,12,kmeans,4,0.3433,0.3153,0.3287,0.2920,0.2150,0.2760,0.5528
1,6,0.53,20,kmeans,4,0.3362,0.3135,0.3244,0.2888,0.2072,0.2749,0.5441
1,5,0.34,12,kmeans,4,0.3381,0.3011,0.3185,0.2829,0.2087,0.2637,0.5567
```

Observations:

- Overall, we see similar patterns to ari.
  - df = 1 still works better (VCGS is better).
  - r = 8~9 and d = 0.53~0.60 worked well.
  - kmeans still works better.
  - k = 4 still generally works good, which is not expected as v-measure tends to increase with the cluster number.
- v-measure and ami's rankings are almost the same.

## Full texts vs. abstracts (smaller data)

First, run eval.py script. (We can run them in parallel as follows. Takes about a couple of hours.)

```bash
nice python eval.py --input brca_pmc_top4.txt.gz --output brca_top4_eval_all.csv &
nice python eval.py --input brca_pmc_top4.txt.gz --fields title,abstract --output brca_top4_eval_ta.csv &
nice python eval.py --input brca_pmc_top4.txt.gz --fields title --output brca_top4_eval_t.csv &
```

Let's look at the result based on ARI.

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
1,9,0.08,4,kmeans,4,0.3461,0.2908,0.3161,0.2896,0.3154,0.2645,0.5786
1,10,0.08,4,kmeans,4,0.3312,0.2817,0.3045,0.2782,0.3046,0.2555,0.5703
1,5,0.01,0,kmeans,4,0.3268,0.2887,0.3066,0.2804,0.2980,0.2617,0.5627
1,7,0.08,8,kmeans,4,0.3296,0.2644,0.2935,0.2722,0.2917,0.2432,0.5697
1,10,0.27,4,kmeans,4,0.3476,0.2971,0.3204,0.2919,0.2873,0.2669,0.5697

# Evaluation for title+abstract.
less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
1,5,0.21,0,kmeans,4,0.3305,0.3292,0.3298,0.3014,0.2275,0.2942,0.5042
1,7,0.08,0,kmeans,4,0.3326,0.3148,0.3234,0.2963,0.2267,0.2824,0.5160
1,8,0.08,0,kmeans,4,0.3352,0.3164,0.3255,0.2991,0.2259,0.2845,0.5168
1,5,0.21,20,kmeans,4,0.3409,0.3269,0.3337,0.3042,0.2240,0.2916,0.5123
1,7,0.08,20,kmeans,4,0.3178,0.2973,0.3072,0.2847,0.2212,0.2699,0.5129

# Evaluation for title.
less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k11 -nr | head -5
100,na,na,4,kmeans,4,0.2932,0.3214,0.3067,0.2812,0.2282,0.2736,0.4914
70,na,na,4,kmeans,4,0.3034,0.3079,0.3056,0.2815,0.2261,0.2754,0.5108
100,na,na,8,kmeans,4,0.2797,0.3087,0.2935,0.2708,0.2237,0.2625,0.4862
50,na,na,4,kmeans,4,0.3167,0.2983,0.3072,0.2857,0.2176,0.2689,0.5228
100,na,na,12,kmeans,4,0.2834,0.3098,0.2960,0.2716,0.2176,0.2645,0.4852
```

Observations:

- Using all fields (title+abstract+fulltext) achieved the best performance in ari.  title+abs and using only title are not much different.
- When using only titles, DF-based feature selection worked better than VCGS which would be due to that titles are too short to identify good keywords based on the VCGS algorithm.
- The ari values for abstract+title (0.2275 at the maximum) is similar to the case for the larger data (medline) (0.2343), so we could expect that using full-text data would improve ari for the larger data, too, if they were available. 


### Evaluate only single-class instances

*I compiled the results for single-class instances in a [different page](single_class.md).*


# Evaluation metrics

Need to consider which metric is suitable for our purpose.
Here's my thought.

- V-measure:  Not suitable to measure cluster quality as it doesn't 
	take into account random labeling.

- Fowlkes-Mallows scores:  Not suitable as it doesn't consider true 
	negatives (pairs not in the same clusters in the predictions and
	in the ground truth).

- Adjusted mutual information: Preferred as it's adjusted against chance
	although it focuses on agreements (intersections) of true and predicted
	clusters.

- Adjusted Rand index:  Desirable as it's adjusted against chance and
	consider not only true positives but also true negatives.  I think it's 
	important to consider true negatives as it indicates cluster separation.

So, AMI and ARI would be the candidates of our evaluation metrics. If we look at the results above sorted by AMI, the tendency changes (i.e., title+abstract works the best).  The difference may be due to that

- ARI looks at true negatives (hence cluster separation) and AMI doesn't.  
- Full-text data helped to separate different underlying classes and ARI favors the separation. 

```bash
# Evaluation for title+abstract+fulltext
less brca_top4_eval_all.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,8,0.40,20,kmeans,4,0.3807,0.3121,0.3430,0.3131,0.2466,0.2807,0.5571
1,9,0.40,16,kmeans,4,0.3833,0.3131,0.3447,0.3133,0.2498,0.2805,0.5595
1,8,0.34,12,kmeans,4,0.3712,0.3000,0.3318,0.3009,0.2402,0.2681,0.5550
1,8,0.40,0,kmeans,4,0.3087,0.2996,0.3041,0.2781,0.1688,0.2679,0.4797
1,10,0.27,4,kmeans,4,0.3476,0.2971,0.3204,0.2919,0.2873,0.2669,0.5697

# Evaluation for title+abstract.
less brca_top4_eval_ta.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
1,5,0.21,0,kmeans,4,0.3305,0.3292,0.3298,0.3014,0.2275,0.2942,0.5042
1,5,0.21,20,kmeans,4,0.3409,0.3269,0.3337,0.3042,0.2240,0.2916,0.5123
1,5,0.21,12,kmeans,4,0.3394,0.3233,0.3312,0.3033,0.2126,0.2896,0.5078
1,5,0.21,16,kmeans,4,0.3328,0.3221,0.3274,0.2994,0.2142,0.2881,0.5045
1,6,0.40,16,kmeans,4,0.3296,0.3217,0.3256,0.2981,0.1717,0.2872,0.4796

# Evaluation for title.
less brca_top4_eval_t.csv | grep ",4,0." | sort -t',' -k12 -nr | head -5
70,na,na,0,kmeans,4,0.3035,0.3367,0.3193,0.2896,0.1787,0.2804,0.4557
70,na,na,4,kmeans,4,0.3034,0.3079,0.3056,0.2815,0.2261,0.2754,0.5108
100,na,na,4,kmeans,4,0.2932,0.3214,0.3067,0.2812,0.2282,0.2736,0.4914
50,na,na,4,kmeans,4,0.3167,0.2983,0.3072,0.2857,0.2176,0.2689,0.5228
30,na,na,12,kmeans,4,0.2826,0.3026,0.2922,0.2683,0.1515,0.2645,0.4502
```

To see their difference empirically, the following computes Pearson's correlation coefficient between every pair of metrics **by R**, not python.

```R
> cls <- c(r="numeric",d="numeric",ari="numeric", ami="numeric", vd="numeric",v="numeric",fms="numeric")
> x = read.csv("brca_med_top4_eval.csv",header=TRUE,colClasses=cls,na.strings="na") 
> cor(x[,9:13])
            vd         v       ari       ami        fms
vd  1.00000000 0.9981891 0.7830321 0.9301852 0.09800617
v   0.99818906 1.0000000 0.8028783 0.9274637 0.12680295
ari 0.78303209 0.8028783 1.0000000 0.7220926 0.56314491
ami 0.93018522 0.9274637 0.7220926 1.0000000 0.16094075
fms 0.09800617 0.1268030 0.5631449 0.1609407 1.00000000
```

ami and vd v are found to be strongly correlated.  ari has relatively strong correlation with the three but it's not as strong as theirs.  On the other hand, fms has weak to moderate correlations with the others.  The following shows the scatter plot for each pair of metrics, again by R.

```R
plot(x[,9:13])
```

<img src="scatter.png" width="600">


