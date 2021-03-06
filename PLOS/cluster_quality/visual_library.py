#! -*- coding: utf-8 -*-

"""
Visual library
"""

import logging, argparse
import sys, os
import re
import operator
import math
import gzip, bz2
import copy
import random

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm

import pandas as pd
#from beakerx import *

from sklearn import metrics
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.decomposition import TruncatedSVD
from sklearn import preprocessing
from sklearn.manifold import TSNE

from IPython.display import display, HTML

import plotly as py
import plotly.graph_objs as go
#py.offline.init_notebook_mode()

import matplotlib.pyplot as plt

import time

#import igraph as ig


# regular expression patterns
tokenize = re.compile("[^\w\-]+") # a token is composed of
                                  # alphanumerics or hyphens
exclude = re.compile("(\d+)$")    # numbers

# constant variables for web app
src2file = {"Inspec": "inspec-corrected.tsv",
            "Breast Neoplasms (PMC, 1.4k)": "brca_ch4_sub_pmc.tsv",
            "Breast Neoplasms (PubMed, 1.4k)": "brca_ch4_sub_med.tsv",
            "Breast Neoplasms (PubMed, 10k)": "brca_ch4_10k.tsv",
            "Breast Neoplasms (PubMed, 16k)": "brca_ch4.tsv"}


'''
main
'''

def main():

    data_dir = 'data'
    csv_dir = 'csv'

    # log output
    logging.basicConfig(filename='.visual_library.log',
                        format='%(asctime)s : %(levelname)s'
                        ': %(message)s', level=logging.INFO)

    # Parse commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rank", type=int, default=5,
                        help="Consider the top R ranked tokens in each "
                        "document (default: 5)")
    parser.add_argument("-d", "--p_docs", type=float, default=0.5,
                        help="The percentage of documents that must "
                        "contain a token ranked above R for the token "
                        "to be selected (default: 0.5)")
    parser.add_argument("--mindf", type=int, default=1,
                        help="Ignore terms below mindf "
                        "(default: 1)")
    parser.add_argument("--theta", type=float, default=0.9,
                        help="Theta for maxi-min clustering. "
                        "The greater the theta, the larger the clusters."
                        "(default: 0.9)")
    parser.add_argument("-i", "--input", default='data/inspec-corrected.tsv', 
                        help="Input file (default: data/inspec-corrected.tsv)")
    parser.add_argument("-w", "--weight", default='tfidf', 
                        help="Term weighting. Either 'tfidf' or "
                        "'binary' (default: tfidf)")
    parser.add_argument("-m", "--matrix", default=None, 
                        help="Output file name for produced "
                        "term-document matrix (default: None)")
    parser.add_argument("-s", "--sim", default=None, 
                        help="Output file name for similarity "
                        "matrix (default: None)")
    parser.add_argument("-c", "--cluster", default="document", 
                        help="Which to cluster, document or term "
                        "(default: document)")
    parser.add_argument("--clustering", default="maximin", 
                        help="Clustering algorithm, maximin or kmeans "
                        "(default: maximin)")
    parser.add_argument("-k", "--n_clusters", type=int, default=10,
                        help="Number of clusters (k) for k-means. "
                        "Not used for maximin "
                        "(default: 10)")
    parser.add_argument("--svd", type=int, default=0,
                        help="Number of components in applying SVD. "
                        "Not applied if 0 "
                        "(default: 0)")
    parser.add_argument("-f", "--fields", 
                        default="", 
                        help="Text fields to be used. One or any "
                        "combination of title, abstract, and body. "
                        "If not specified, all fields are used "
                        "(default: \"\")")
    parser.add_argument("--mesh", default=None, 
                        help="Mesh term file corresponding to "
                        "the input. Needed for PMC file "
                        "(default: None)")
    parser.add_argument("--format", default="abs", 
                        help="Input file format (line/abs/full) "
                        "(default: abs)")
    parser.add_argument('--single',
                        help='Evaluate only single-class instances '
                        '(default: False)',
                        action='store_true')
    parser.add_argument("--sample", 
                        default="0", type=int,
                        help="number of articles sampled. Use all "
                        "if 0 (default: 0)")
    parser.add_argument('--visualize',
                        help='Visualize results (default: False)',
                        action='store_true')
    parser.add_argument('--balance',
                        help='Balance the data (default: False)',
                        action='store_true')


    args = parser.parse_args()
    logging.info(args)

    # Read stopword list
    stopwords = read_stopwords()            

    # Balance the data
    if args.balance and re.search("(plos|pmc|med)", args.input):
        balance_data(file=args.input)
        input_file = ".balanced_"+args.input
    else:
        input_file = args.input

    # Read documents
    start = time.time() # measure processing time

    print("Reading documents...")
    docs, df, w2id, mesh = read_documents(
        data_dir, input=input_file, stopwords=stopwords,
        fields=args.fields, single_class=args.single,
        n_samples=args.sample, format=args.format)
    print("Finished reading %d documents" % len(docs))
    print("%d terms were identified" % len(df))

    # Read MeSH file if provided
    if args.mesh:
        print("Reading MeSH file...")
        mesh = read_mesh(args.mesh)

    # Remove terms whose df is lower than mindf
    del_low_high_df(df, mindf=args.mindf)

    # Compute tfidf and find key terms
    print("Computing TFIDF and finding key terms...")
    docs, dfr = compute_tfidf(docs, df, args.weight, args.rank)

    # Output matrix if output name is specified
    if args.matrix:
        print("Writing out TFIDF matrix...")
        output_matrix(csv_dir, args.matrix, docs, df.keys())

    # Sort and output results (discovered keywords)
    if args.p_docs <= 0:
        keywords = identify_n_keywords(
            dfr, df, args.rank*args.n_clusters)
    else:
        keywords = identify_keywords(
            len(docs), dfr, df, args.p_docs)
    print("Identified {} keywords".format(len(keywords)))

    # Create new matrix with the keywords (mesh is also needed
    # in case some docs are removed)
    print("Before: {} docs".format(len(docs)))
    docs, mesh = update(docs, keywords, mesh)
    print("After: {} docs".format(len(docs)))

    # clustering
    print()
    print("Clustering...")
    if args.clustering == "maximin":
        _, membership, _, sc, sct = \
            maximin(csv_dir, docs, args.sim, 
                    args.cluster, keywords, np.array(mesh).ravel(),
                    args.theta, args.svd)
        #visualize_network(sim, keywords, membership)
    elif args.clustering == "kmeans":
        membership, _, _, _, sc, sct = kmeans(
            docs, args.cluster, keywords, args.svd,
            args.n_clusters, np.array(mesh).ravel())

    end = time.time()
    print("Processing time (sec):", end - start)

    if args.cluster == "document" and len(mesh) > 0:
        print(" Silhouette   = %f" % sc)
        print(" Silhouette_t = %f" % sct)
        evaluate(mesh, membership)
        
        
    # visualization
    if args.visualize:
        print()
        print("Visualizing...")
        visualize(docs, args.cluster, mesh, membership, keywords, 'tsne')
        
'''
make balanced data
'''
def balance_data(file=None):

    # store data temporarily
    data = dict()

    # read file
    with open_by_suffix(file) as f:
        for line in f:
            if "plos" in file or "pmc" in file:
                _, _, _, _, m = \
                    line.rstrip().split('\t')
            else:
                _, _, _, m, _ = line.split('\t')

            # for skipping multi-class instances
            m = m.split('|')
            if len(m) > 1:
                continue

            if m[0] in data:
                data[m[0]].append(line)
            else:
                data[m[0]] = [line]

    min = sys.maxsize
    for k in data:
        if len(data[k]) < min:
            min = len(data[k])

    # write
    with gzip.open(".balanced_"+file, "wt") as f:
        for k in data:
            f.write(''.join(data[k][0:min]))


'''
visualize actual and predicted clusters.
'''
def visualize(docs, what_to_cluster, true_labels,
              preds, keywords, method="svd"):

    # add ids to keywords
    keywords.sort()
    w2id = {c:i for i,c in enumerate(keywords)}

    # add ids to true labels (mesh). only the first 
    # cluster label is considered.
    m2id = {m:i for i,m in enumerate(set([x[0] for x in true_labels]))}
    id2m = {i:m for m,i in m2id.items()}
    true_labels = [m2id[m[0]] for m in true_labels]

    # confusion matrix
    cm = metrics.confusion_matrix(true_labels, preds)
    print()
    print("Confusion matrix")
    print(cm)

    # find largest match column-wise
    h = {i:x for i,x in enumerate(cm.argmax(axis=0))}
    nclus = len(set(preds))
    preds = [h[x] for x in preds]
    '''
    # find largest match row-wise
    h = {x:i for i,x in enumerate(cm.argmax(axis=1))}
    nclus = len(set(preds))
    preds = [h[x] for x in preds]
    '''

    # aligned confusion matrix
    print()
    print("#col #row max homogeneity")
    for i in range(nclus):
        ho = cm[h[i],i]/cm[:,i].sum()
        print(i, h[i], cm[h[i],i], "%.3f" % (ho))

    # Convert to scipy matrix for faster calculation
    data = []
    row_idx = []
    col_idx = []
    for i in range(len(docs)):
        data += docs[i].values()
        col_idx += [w2id[w] for w in docs[i].keys()]
        row_idx += [i] * len(docs[i])

    data = csr_matrix((data, (row_idx, col_idx)), 
                      (len(docs), len(keywords)))

    # Normalize
    if what_to_cluster == "document":
        data = data / norm(data, axis=1)[:,np.newaxis]
    elif what_to_cluster == "term":
        data = data.transpose() / norm(data, axis=0)[:,np.newaxis]

    # SVD
    cluster_labels = []

    if method == "svd":
        svd_model = TruncatedSVD(n_components=2,
                                 random_state=42)
        svd_model.fit(data)
        reduced_data = svd_model.transform(data)
    else:
        if data.shape[1] > 20:
            # reduce dims first..
            svd_model = TruncatedSVD(
                n_components=20, random_state=42)
            reduced_data = svd_model.fit_transform(data)
        else:
            reduced_data = data
        # then apply tsne
        tsne = TSNE(n_components=2, 
                    n_iter=400, random_state=123)
        reduced_data = tsne.fit_transform(reduced_data)

    # sample data points to avoid clatters
    preds = np.array(preds)
    true_labels = np.array(true_labels)

    if len(preds) > 1000:
        indices = random.sample(range(len(preds)), 1000)
        indices.sort()
        preds = preds[indices]
        true_labels = true_labels[indices]
        reduced_data = reduced_data[indices]

    # Create a plot with subplots in a grid of 1X2
    fig, ax = plt.subplots(1, 2, figsize=(8, 4))

    # Add scatter plots to the subplots
    colors = ["C{}".format(x) for x in range(nclus)]

    # mesh class
    for i in range(len(m2id)):
        indices = true_labels == i
        ax[0].scatter(reduced_data[indices, 0], 
                      reduced_data[indices, 1], 
                      c=colors[i], alpha=.3, 
                      edgecolors='none', label=id2m[i])
    
    # cluster
    for i in range(len(m2id)):
        indices = preds == i
        ax[1].scatter(reduced_data[indices, 0], 
                      reduced_data[indices, 1], 
                      c=colors[i], alpha=.3, 
                      edgecolors='none')

    ax[0].set_title('Underlying MeSH classes')
    ax[1].set_title('Identified clusters')

    # add legend
    legends = [id2m[x] for x in range(len(id2m))]
    print(legends)
    ax[0].legend(loc='upper left', prop={'size': 6})

    # Show the plots
    plt.savefig('plot.pdf')


'''
Compute purity (macro-average is Javed's version of homogeneity)
'''
def compute_purity(mesh, membership):

    # add ids to true labels (mesh). only the first 
    # cluster label is considered.
    m2id = {m:i for i,m in enumerate(set([x[0] for x in mesh]))}
    id2m = {i:m for m,i in m2id.items()}
    labels = [m2id[m[0]] for m in mesh]

    # confusion matrix
    cm = metrics.confusion_matrix(labels, membership)

    # compute max
    sum_max = sum(cm.max(axis=0))

    # find largest match
    k2c = {i:x for i,x in enumerate(cm.argmax(axis=0))}
    preds = [k2c[x] for x in membership]
    nclus = len(set(preds))

    # compute
    sum_h = 0.0
    for i in range(nclus):
        h = cm[k2c[i],i]/cm[:,i].sum()
        sum_h += h
        #print(i, "%.3f" % (h))

    return sum_h/nclus, sum_max/len(membership) 


'''
Evaluation
'''
def evaluate(mesh, membership):

    if len(mesh) == 0:
        print("No labels (MeSH) provided. "
              "Cannot evaluate the clusters.")
        return

    # precision (Javed's version of homogeneity)
    prt_macro, prt_micro = compute_purity(mesh, membership)
    print(" Purity-macro = %f" % prt_macro)
    print(" Purity-micro = %f" % prt_micro)

    # v-score (variant for multilabels)
    c = compute_completeness(mesh, membership)
    h = compute_homogeneity(mesh, membership)
    vd = (2*h*c)/(h+c)
    print(" VD-score     = %f" % vd)

    # other metrics

    # treat a multi-labeled instance as multiple instances
    preds = []
    labels = []
    for i, l in enumerate(mesh):
        for l_ in l:
            labels.append(l_)
            preds.append(membership[i])

    # compute
    v = metrics.v_measure_score(labels, preds)
    ai = metrics.adjusted_rand_score(labels, preds)
    ami = metrics.adjusted_mutual_info_score(labels, preds, 'arithmetic')
    fms = metrics.fowlkes_mallows_score(labels, preds)

    print(" V-score      = %f" % v)
    print(" A-RAND-I     = %f" % ai)
    print(" A-MI         = %f" % ami)
    print(" FMS          = %f" % fms)

    return c, h, vd, v, ai, ami, fms, prt_macro, prt_micro


'''
File opener depending on suffix
'''
def open_by_suffix(filename):
    if filename.endswith('.gz'):
        return gzip.open(filename, 'rt')
    elif filename.endswith('.bz2'):
        return bz2.BZ2file(filename, 'r')
    else: # assume text file
        return open(filename, 'r')


'''
Read MeSH files
'''
def read_mesh(file_name):
    mesh = []
    with open(file_name) as f:
        for line in f:
            meshes = line.rstrip().split('|')
            tmp = []
            for m in meshes:
                tmp.append(m.split('/')[0])
            mesh.append(tmp)
            
    return mesh


'''
Compute completeness
'''
def compute_completeness(labels, pred):

    C = set()
    K = set(pred)

    # count
    N = float(0)
    a = dict()
    for i, l in enumerate(labels):
        for l_ in l:
            N += 1 / len(l)
            C.add(l_)
            key = l_+str(pred[i])
            if key in a:
                a[key] += 1 / len(l)
            else:
                a[key] = 1 / len(l)

    # compute H(K)
    hk = 0
    for k in K:
        s = 0
        for c in C:
            #print(c, k)
            key = c+str(k)
            if key in a:
                #print(a[key])
                s += a[key]
        s /= N
        hk += s * math.log(s, 2)
    hk = -hk
    #print("hk = %f" % hk)
            
    # compute H(K|C)
    hkc = 0
    for c in C:
        nc = 0
        for k in K:
            key = c+str(k)
            if key in a:
                nc += a[key]
        for k in K:
            #print(c, k)
            key = c+str(k)
            if key in a:
                #print(a[key])
                hkc += a[key]/N * math.log(a[key]/nc, 2)
    hkc = -hkc
    #print("hkc = %f" % hkc)
    c = 1 - hkc/hk
    print(" Completeness = %f" % c)

    return c


'''
Compute homogeneity
'''
def compute_homogeneity(labels, pred):

    C = set()
    K = set(pred)

    # count
    N = float(0)
    a = dict()
    for i, l in enumerate(labels):
        for l_ in l:
            N += 1 / len(l)
            C.add(l_)
            key = l_+str(pred[i])
            if key in a:
                a[key] += 1 / len(l)
            else:
                a[key] = 1 / len(l)

    # compute H(C) 
    hc = 0
    for c in C:
        nc = 0
        for k in K:
            #print(c, k)
            key = c+str(k)
            if key in a:
                #print(a[key])
                nc += a[key]
        nc /= N
        hc += nc * math.log(nc, 2)
    hc = -hc
    #print("hc = %f" % hc)
            
    # compute H(C|K)
    hck = 0
    for k in K:
        ac = 0
        for c in C:
            key = c+str(k)
            if key in a:
                ac += a[key]
        for c in C:
            #print(c, k)
            key = c+str(k)
            if key in a:
                #print(a[key])
                hck += a[key]/N * math.log(a[key]/ac, 2)
    hck = -hck
    #print("hck = %f" % hck)
    h = 1 - hck/hc
    print(" Homogeneity  = %f" % h)

    return h


'''
kmeans
'''
def kmeans(docs, what_to_cluster, keywords, n_components, k, true_labels):

    # add ids to keywords
    keywords.sort()
    w2id = {c:i for i,c in enumerate(keywords)}

    # Convert to scipy matrix for faster calculation
    data = []
    row_idx = []
    col_idx = []
    for i in range(len(docs)):
        data += docs[i].values()
        col_idx += [w2id[w] for w in docs[i].keys()]
        row_idx += [i] * len(docs[i])

    data = csr_matrix((data, (row_idx, col_idx)), 
                      (len(docs), len(keywords)))


    # Also create keyword vectors
    values = [1.0] * len(keywords)
    col_idx = []
    row_idx = []
    for i in range(len(keywords)):
        col_idx += [i]
        row_idx += [i]

    kwd_vecs = csr_matrix((values, (row_idx, col_idx)),
                          (len(keywords), len(keywords)))

    # Normalize
    if what_to_cluster == "document":
        data = data / norm(data, axis=1)[:,np.newaxis]
    elif what_to_cluster == "term":
        data = data.transpose() / norm(data, axis=0)[:,np.newaxis]
    
    # SVD
    cluster_labels = []
    if n_components == 0: # no svd
        km = KMeans(init='k-means++', n_clusters=k, n_init=10,
                    random_state=0)
        km.fit(data)
        # compute Silhouette Coefficient
        sc = metrics.silhouette_score(data, km.labels_, 
                                      metric='cosine')
        sct = metrics.silhouette_score(data, true_labels, 
                                       metric='cosine')

        # set cluster centers to get descriptions
        centers = km.cluster_centers_

    else: # apply svd then cluster
        svd_model = TruncatedSVD(n_components=n_components,
                                 random_state=42)
        svd_model.fit(data)
        reduced_data = svd_model.transform(data)

        '''
        # Normalize again
        reduced_data = reduced_data / \
                       np.linalg.norm(reduced_data, axis=1)[:,np.newaxis]
        '''

        kwd_vecs = svd_model.transform(kwd_vecs)
        km = KMeans(init='k-means++', n_clusters=k, 
                    n_init=10, random_state=0).fit(reduced_data)
        
        # compute Silhouette Coefficient
        sc = metrics.silhouette_score(reduced_data, km.labels_, 
                                      metric='cosine')
        sct = metrics.silhouette_score(reduced_data, true_labels, 
                                       metric='cosine')

        # inverse-transform cluster centers
        centers = svd_model.inverse_transform(km.cluster_centers_)

    # create cluster labels
    for j, c in enumerate(centers):

        # set num of keywords
        n_desc = min(10, len(c)-1)

        i = np.argpartition(c, -n_desc)[-n_desc:] # top n (unsorted)
        c_i = c[i]
        i_ = np.argsort(c_i)[::-1] # sort
        k_i = np.array(keywords)[i]
        labels_ = k_i[i_].tolist()
        print("C%d: " % (j+1) + ", ".join(labels_))
        cluster_labels.append(labels_)

    if n_components > 0:
        print("Formed %d clusters after reducing "
              "to %d dimensions by kmeans." % (k, n_components))
    else:
        print("Formed %d clusters w/o SVD by kmeans." % k)

    return km.labels_.tolist(), km.cluster_centers_,\
        kwd_vecs, cluster_labels, sc, sct
    

'''
spectral
'''
def spectral(docs, what_to_cluster, keywords, 
             n_components, k, true_labels):

    # add ids to keywords
    keywords.sort()
    w2id = {c:i for i,c in enumerate(keywords)}

    # Convert to scipy matrix for faster calculation
    data = []
    row_idx = []
    col_idx = []
    for i in range(len(docs)):
        data += docs[i].values()
        col_idx += [w2id[w] for w in docs[i].keys()]
        row_idx += [i] * len(docs[i])

    data = csr_matrix((data, (row_idx, col_idx)), 
                      (len(docs), len(keywords)))

    # Normalize
    if what_to_cluster == "document":
        data = data / norm(data, axis=1)[:,np.newaxis]
    elif what_to_cluster == "term":
        data = data.transpose() / norm(data, axis=0)[:,np.newaxis]

    # SVD
    cluster_labels = []
    if n_components == 0: # no svd
        spectral = SpectralClustering(
            n_clusters=k, random_state=0, n_jobs=-1)
        spectral.fit(data)
        # compute Silhouette Coefficient
        sc = metrics.silhouette_score(data, spectral.labels_, 
                                      metric='cosine')
        sct = metrics.silhouette_score(data, true_labels, 
                                       metric='cosine')

    else: # apply svd then cluster
        svd_model = TruncatedSVD(n_components=n_components,
                                 random_state=42)
        svd_model.fit(data)
        reduced_data = svd_model.transform(data)

        '''
        # Normalize again
        reduced_data = reduced_data / \
                       np.linalg.norm(reduced_data, axis=1)[:,np.newaxis]
        '''

        spectral = SpectralClustering(
            n_clusters=k, n_init=10, random_state=0, n_jobs=-1).\
            fit(reduced_data)
        
        # compute Silhouette Coefficient
        sc = metrics.silhouette_score(reduced_data, spectral.labels_, 
                                      metric='cosine')
        sct = metrics.silhouette_score(reduced_data, true_labels, 
                                       metric='cosine')

    if n_components > 0:
        print("Formed %d clusters after reducing "
              "to %d dimensions by spectral clustering." \
                  % (k, n_components))
    else:
        print("Formed %d clusters w/o SVD by spectral "
              "clustering." % k)

    return spectral.labels_.tolist(), sc, sct


'''
Read stopwords
'''
def read_stopwords(filename="data/stopwords.txt"):
    stopwords = set()
    with open(filename) as f:
        for term in f:
            if term.startswith("#"):
                continue
            stopwords.add(term.rstrip())
    return stopwords


'''
Read documents from simplejson instance (for SOLR)
'''
def read_json(input, stopwords=[]):

    docs = [] # store documents
    df = dict() # document frequency
    w2id = dict()
    cnt_w = 0

    for d in input['response']['docs']:
        terms = tokenize.split(\
            (d['title_display']+" "+" ".join(d['abstract'])).lower())
        terms = [w for w in terms if w != '' and \
                     w not in stopwords and \
                     not exclude.match(w)]
        # count df
        for w in set(terms):
            if w in df:
                df[w] += 1
            else:
                df[w] = 1
                w2id[w] = cnt_w
                cnt_w += 1
        # count tf
        tf = dict()
        for w in terms:
            if w in tf:
                tf[w] += 1
            else:
                tf[w] = 1
        docs.append(tf)

    return docs, df, w2id


''' 
Read documents
'''
def read_documents(data_dir, input=None, source=None, 
                   stopwords=[], fields="", single_class=False,
                   n_samples=sys.maxsize, format="abs"):

    docs = [] # store documents
    df = dict() # document frequency
    w2id = dict()
    cnt_w = 0

    # get file name
    if source:
        file = os.path.join(data_dir, src2file[source])
    else:
        file = input

    mesh = []
    cnt = 0
    with open_by_suffix(file) as f:
        for line in f:

            # break after reading n_samples lines
            if n_samples != 0 and cnt >= n_samples:
                break

            if format=="line":
                terms = tokenize.split(line.lower())
                cnt += 1

            elif format=="full":
                _, title, abs, body, m = \
                    line.rstrip().split('\t')
                text = ""
                if "title" in fields:
                    text += title
                if "abstract" in fields or "abs" in fields:
                    text += " " + abs
                if "body" in fields:
                    text += " " + body
                if text == "":
                    text = title+" "+abs+" "+body 
                terms = tokenize.split(text.lower())
                m = m.split('|')

                # for skipping multi-class instances
                if single_class and len(m) > 1:
                    continue

                mesh.append(m)
                cnt += 1

            else:
                pmid, title, abs, m, _ = line.split('\t')
                terms = tokenize.split((title+" "+abs).lower())
                m = m.split('|')

                # for skipping multi-class instances
                if single_class and len(m) > 1:
                    continue

                tmp = []
                for m_ in m:
                    tmp.append(m_.split('/')[0])
                mesh.append(tmp)
                cnt += 1

            terms = [w for w in terms if w not in stopwords and \
                         len(w) > 1 and not exclude.match(w)]
            # count df
            for w in set(terms):
                if w in df:
                    df[w] += 1
                else:
                    df[w] = 1
                    w2id[w] = cnt_w
                    cnt_w += 1

            # count tf
            tf = dict()
            for w in terms:
                if w in tf:
                    tf[w] += 1
                else:
                    tf[w] = 1

            docs.append(tf)

    return docs, df, w2id, mesh

'''
Compute tfidf and find key terms
'''
def compute_tfidf(docs, df, weight, rank=5):

    docs_ = copy.deepcopy(docs) # make copy

    dfr = dict() # df considering only top R terms per document
    for i in range(len(docs)):
        for w in docs[i]:
            # delete low DF term
            if w not in df:
                del docs_[i][w]
                continue
            # tfidf
            if weight == 'tfidf':
                docs_[i][w] *= math.log(len(docs)/df[w])
            else: # 'binary' if not 'tfidf'
                docs_[i][w] = 1
        
        # Ignore if rank = 0
        if rank > 0:
            # Sort and extract top R terms for this document
            terms_sorted = sorted(docs_[i].items(), reverse=True, 
                                  key=operator.itemgetter(1))
            top_r = terms_sorted[:rank]

            # Count new df for only top R
            for w, _ in top_r:
                if w in dfr:
                    dfr[w] += 1
                else:
                    dfr[w] = 1

    return docs_, dfr


'''
Output matrix
'''
def output_matrix(csv_dir, filename, docs, vocab):
        vocab = list(vocab)
        vocab.sort()
        with open(os.path.join(csv_dir, filename), 'wb') as f:
            # header
            f.write((','.join(vocab) + '\n').encode('utf8'))
            # values
            for i, d in enumerate(docs):
                out = ''
                for w in vocab:
                    if w in d:
                        out += "{:.5},".format(d[w])
                    else:
                        out += "0,"
                f.write((out.rstrip(',') + '\n').encode('utf8'))
                if i % int(len(docs)/20) == 0:
                    print("%d%% finished..." % (i/len(docs)*100))


''' 
Identify keywords appearing in more than p_docs% of docs
'''
def identify_keywords(num_docs, dfr, df, p_docs=0.5, html=False):
    min_dfr = num_docs * p_docs / 100
    terms_sorted = sorted(dfr.items(), reverse=True, 
                          key=operator.itemgetter(1))
    if not html:
        print("term\tDF\tDFR")

    keywords = []
    dfs = []
    dfrs = []
    for w, v in terms_sorted:
        if v < min_dfr:
            break
        if w not in df:
            continue

        keywords.append(w)
        dfs.append(df[w])
        dfrs.append(dfr[w])

        if not html:
            print("%s\t%d\t%d" % (w, df[w], dfr[w]))
        
    if html:
        d = pd.DataFrame(
            {"Term": keywords, "DF": dfs, "DFR": dfrs},
            columns=["Term", "DF", "DFR"])
        display(HTML(d.to_html(index=False)))

    return keywords

''' 
Identify up to num_terms keywords
'''
def identify_n_keywords(dfr, df, num_terms, html=False):

    terms_sorted = sorted(dfr.items(), reverse=True, 
                          key=operator.itemgetter(1))
    if not html:
        print("term\tDF\tDFR")

    keywords = []
    dfs = []
    dfrs = []
    c = 0
    for w, _ in terms_sorted:
        if c >= num_terms:
            break
        if w not in df:
            continue

        keywords.append(w)
        dfs.append(df[w])
        dfrs.append(dfr[w])
        c += 1

        if not html:
            print("%s\t%d\t%d" % (w, df[w], dfr[w]))
        
    if html:
        d = pd.DataFrame(
            {"Term": keywords, "DF": dfs, "DFR": dfrs},
            columns=["Term", "DF", "DFR"])
        display(HTML(d.to_html(index=False)))

    return keywords


'''
Normalize matrix (not used)
'''
def normalize(mat, axis='document'):
    if axis == 'document':
        for i in range(len(mat)):
            norm = 0
            for w in mat[i]:
                norm += mat[i][w] * mat[i][w]
            norm = math.sqrt(norm)
            for w in mat[i]:
                mat[i][w] /= norm
    elif axis == 'term':
        # not implemented
        pass
    return mat


'''
Maximin (core)
'''

def maximin_core(docs, m, what_to_cluster="document",
                 theta=0.9, verbose=False):

    sim = np.array(m.dot(m.transpose()))
    np.fill_diagonal(sim, -2) # need to set smaller than -1
    centroids = []
    candidates = list(range(sim.shape[0]))

    # pick the first centroid
    centroids.append(candidates.pop(\
            random.randint(0, len(docs)-1)))

    # Find next centroid iteratively
    while True:
        sim_max = sim[centroids,:].max(axis=0) # take max as this is
                                               # similarity
        sim_max[centroids] = 2 # need to be greater than 1
        maximin_id = sim_max.argmin()
        maximin = 1 - sim_max.min() # make similarity to distance

        if maximin > theta:
            centroids.append(candidates.pop(\
                    candidates.index(maximin_id)))
        else:
            break

    # Results
    print("%d clusters generated" % len(centroids))
    print()

    # Show clusters
    if what_to_cluster == "document":
        membership = sim[centroids,:].argmax(axis=0).tolist()
        if verbose:
            for i, id in enumerate(centroids):
                print('Doc %d cluster (%d members):' % \
                          (id, len([x for x in membership if x==i])))
                print(docs[id])
                print()
    else:
        membership = sim[centroids,:].argmax(axis=0)
        keywords = np.asarray([keywords])
        if verbose:
            for i, id in enumerate(centroids):
                print('Term %d cluster (%d members):' % \
                          (id, (membership==i).sum()))
                print(keywords[membership==i])
                print()
        membership = membership.tolist()[0]

    # renumber membership
    m2id = {me:i for i,me in enumerate(set(membership))}
    membership = [m2id[me] for me in membership]

    # compute Silhouette Coefficient. can't use sim
    # since diagonals were changed.
    if len(set(membership)) < 2:
        sc = float('nan')
    else:
        sc = metrics.silhouette_score(m, membership, 
                                      metric='cosine')

    return centroids, membership, sim, sc


'''
Maximin clustering wrapper
'''
def maximin(csv_dir, docs, file_sim, cluster, keywords,
            true_labels,
            theta=0.9, n_components=0, verbose=True):

    # add ids to keywords
    keywords.sort()
    w2id = {c:i for i,c in enumerate(keywords)}

    # Convert to scipy matrix for faster calculation
    data = []
    row_idx = []
    col_idx = []
    for i in range(len(docs)):
        data += docs[i].values()
        col_idx += [w2id[w] for w in docs[i].keys()]
        row_idx += [i] * len(docs[i])

    m = csr_matrix((data, (row_idx, col_idx)), 
                   (len(docs), len(keywords)))

    # Compute similarity matrix (cosine similarity)
    if cluster == "document":
        pass
    else: # assume 'term' if not 'document'
        m = m.transpose()

    # normalization
    m = m / norm(m, axis=1)[:,np.newaxis]

    # SVD
    cluster_labels = []
    if n_components == 0: # no svd
        # compute silhouette score
        sct = metrics.silhouette_score(m, true_labels, 
                                       metric='cosine')
        centroids, membership, sim, sc = \
            maximin_core(docs, m, cluster, theta, verbose)
    else: # apply svd then cluster
        svd_model = TruncatedSVD(n_components=n_components,
                                 random_state=42)
        svd_model.fit(m)
        reduced_m = svd_model.transform(m)
        # compute silhouette score (before normalization)
        sct = metrics.silhouette_score(reduced_m, true_labels, 
                                       metric='cosine')
        # normalization
        reduced_m = reduced_m / \
            np.linalg.norm(reduced_m, axis=1)[:,np.newaxis]
        centroids, membership, sim, sc = \
            maximin_core(docs, reduced_m, cluster,
                         theta, verbose)

    '''
    # create cluster labels by inverse-transforming
    # cluster centers and take 5 words with highest values
    centers = m[centroids]
    for c in centers:
        i = np.argpartition(c, -5)[-5:]
        labels_ = np.array(keywords)[i].tolist()
        print(labels_)
        cluster_labels.append(labels_)
    '''

    if n_components > 0:
        print("Formed %d clusters after reducing "
              "to %d dimensions by maximin." % (len(set(membership)),
                                     n_components))
    else:
        print("Formed %d clusters w/o SVD by maximin." % \
              len(set(membership)))

        
    # Write similarity matrix to csv file
    if file_sim:
        print("Writing similarity matrix to file...")
        with open(os.path.join(csv_dir, file_sim), 'wb') as f:
            # header
            if cluster == "document":
                f.write((",".join(\
                            [str(i) for i in range(len(docs))]))\
                            .encode('utf8'))
            else:
                f.write((",".join(keywords)).encode('utf8'))
            f.write("\n".encode('utf8'))
            # matrix
            for i in range(sim.shape[0]):
                row = sim[i,:].tolist()[0]
                f.write((','.join(\
                            ["{}".format(x) for x in row]))\
                            .encode('utf8'))
                f.write("\n".encode('utf8'))
                if i % int(len(docs)/20) == 0: # progress
                    print("%d%% finished..." % (i/len(docs)*100))

    return centroids, membership, sim, sc, sct



'''
Visualize similarity network
'''
def visualize_network(sim, labels, group):

    np.fill_diagonal(sim, 0)
    G = ig.Graph.Adjacency((sim > .1).tolist())
    G.es['weight'] = sim
    G.vs['label'] = labels

    Edges = [e.tuple for e in G.es]

    #labels = [range(sim.shape[0])]
    #group = [0] * sim.shape[0]

    layt = G.layout('kk', dim=3) 

    N = sim.shape[0]
    Xn = [layt[k][0] for k in range(N)]# x-coordinates of nodes
    Yn = [layt[k][1] for k in range(N)]# y-coordinates
    Zn = [layt[k][2] for k in range(N)]# z-coordinates
    Xe = []
    Ye = []
    Ze = []
    
    for e in Edges:
        Xe += [layt[e[0]][0],layt[e[1]][0], None]# x-coordinates of edge ends
        Ye += [layt[e[0]][1],layt[e[1]][1], None]  
        Ze += [layt[e[0]][2],layt[e[1]][2], None]  

    trace1=go.Scatter3d(x=Xe,
                   y=Ye,
                   z=Ze,
                   mode='lines',
                   line=dict(color='rgb(125,125,125)', width=1),
                   hoverinfo='none'
                   )

    trace2=go.Scatter3d(x=Xn,
                        y=Yn,
                        z=Zn,
                        mode='markers+text',
                        name='terms',
                        marker=dict(symbol='circle',
                                    size=6,
                                    color=group,
                                    colorscale='Viridis',
                                    line=dict(color='rgb(50,50,50)', width=0.5)
                                    ),
                        text=labels,
                        textposition='top center',
                        hoverinfo='x+y+z'
                        )

    axis=dict(showbackground=False,
              showline=False,
              zeroline=False,
              showgrid=False,
              showticklabels=False,
              title=''
              )

    layout = go.Layout(
        title="Network of the discovered keywords (3D visualization)",
        width=1000,
        height=1000,
        showlegend=False,
        scene=dict(
            xaxis=dict(axis),
            yaxis=dict(axis),
            zaxis=dict(axis),
            ),
        margin=dict(
            t=100
            ),
        hovermode='closest',
        )
    
    data = [trace1, trace2]
    fig = go.Figure(data=data, layout=layout)

    py.offline.iplot(fig, filename='network')

    
'''
Create new matrix with given keywords
'''
def update(docs, keywords, mesh=[]):
    docs_new = []
    mesh_new = []
    for i, d in enumerate(docs):
        h = dict()
        for w in keywords:
            if w in d:
                h[w] = d[w]
        if len(h) == 0: # exclude doc w/ no terms
            random.seed(i)
            # give random word if no word is found
            h[keywords[random.randint(0, len(keywords)-1)]] = 1
            
        docs_new.append(h)

        if len(mesh) != 0:
            mesh_new.append(mesh[i])

    return docs_new, mesh_new


'''
Delete low-df words
'''
def del_lowdf(df,mindf=1):
    inf = []
    for w in df:
        if df[w] <= mindf:
            inf.append(w)
    for w in inf:
        del df[w]

    print("%d terms were removed" % len(inf))

'''
Delete low and high df words
'''
def del_low_high_df(df, mindf=1, maxdf=sys.maxsize):
    inf = []
    for w in df:
        if df[w] <= mindf or df[w] >= maxdf:
            inf.append(w)
    for w in inf:
        del df[w]

    print("%d terms were removed" % len(inf))

    
'''
main
'''
if __name__ == "__main__":
    main()


    
