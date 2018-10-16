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
import random

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm

import pandas as pd
#from beakerx import *

from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn import preprocessing

from IPython.display import display, HTML

import plotly as py
import plotly.graph_objs as go
#py.offline.init_notebook_mode()

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
    parser.add_argument("--mesh", default=None, 
                        help="Mesh term file corresponding to "
                        "the input. Needed for PMC file "
                        "(default: None)")


    args = parser.parse_args()
    logging.info(args)

    # Read stopword list
    stopwords = read_stopwords()            

    # Read documents
    print("Reading documents...")
    docs, df, w2id, mesh = read_documents(data_dir, 
                                          input=args.input,
                                          stopwords=stopwords)
    print("Finished reading %d documents" % len(docs))
    print("%d terms were identified" % len(df))

    # Read MeSH file if provided
    if args.mesh:
        print("Reading MeSH file...")
        mesh = read_mesh(args.mesh)

    # Remove terms whose df is lower than mindf
    inf = []
    if args.mindf:
        for w in df:
            if df[w] <= args.mindf:
                inf.append(w)
        for w in inf:
            del df[w]
    print("%d terms were removed" % len(inf))

    # Compute tfidf and find key terms
    print("Computing TFIDF and finding key terms...")
    docs, dfr = compute_tfidf(docs, df, args.weight, args.rank)

    # Output matrix if output name is specified
    if args.matrix:
        print("Writing out TFIDF matrix...")
        output_matrix(csv_dir, args.matrix, docs, df.keys())

    # Sort and output results (discovered keywords)
    keywords = output_keywords(len(docs), dfr, df, args.p_docs)

    # Create new matrix with the keywords (mesh is also needed
    # in case some docs are removed)
    docs, mesh = update(docs, keywords, mesh)

    # clustering
    print()
    print("Clustering...")
    if args.clustering == "maximin":
        _, membership, _ = \
            maximin(csv_dir, docs, args.sim, 
                        args.cluster, keywords, args.theta,
                        args.svd)
        #visualize_network(sim, keywords, membership)
    elif args.clustering == "kmeans":
        membership, _, _, _ = kmeans(docs, args.cluster, keywords, 
                                  args.svd, args.n_clusters)

    if args.cluster == "document" and len(mesh) > 0:
        evaluate(mesh, membership)
        
        
    '''
    # visualization
    print()
    print("Visualizing...")
    
    visualize(data, centroids, membership)
    '''

'''
Evaluation
'''
def evaluate(mesh, membership):

    if len(mesh) == 0:
        print("No labels (MeSH) provided. "
              "Cannot evaluate the clusters.")
        return

    c = compute_completeness(mesh, membership)
    h = compute_homogeneity(mesh, membership)
    vd = (2*h*c)/(h+c)
    print(" VD-score     = %f" % vd)

    preds = []
    labels = []
    for i, l in enumerate(mesh):
        for l_ in l:
            labels.append(l_)
            preds.append(membership[i])

    v = metrics.v_measure_score(labels, preds)
    ai = metrics.adjusted_rand_score(labels, preds)
    ami = metrics.adjusted_mutual_info_score(labels, preds)
    fms = metrics.fowlkes_mallows_score(labels, preds)

    print(" V-score      = %f" % v)
    print(" A-RAND-I     = %f" % ai)
    print(" A-MI         = %f" % ami)
    print(" FMS          = %f" % fms)

    return c, h, vd, v, ai, ami, fms


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
def kmeans(docs, what_to_cluster, keywords, n_components, k):

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
    else: # apply svd then cluster
        svd_model = TruncatedSVD(n_components=n_components)
        svd_model.fit(data)
        reduced_data = svd_model.transform(data)
        kwd_vecs = svd_model.transform(kwd_vecs)
        km = KMeans(init='k-means++', n_clusters=k, 
                    n_init=10).fit(reduced_data)

        # create cluster labels by inverse-transforming
        # cluster centers and take 5 words with highest values
        centers = svd_model.inverse_transform(km.cluster_centers_)
        for c in centers:
            i = np.argpartition(c, -5)[-5:]
            labels_ = np.array(keywords)[i].tolist()
            print(labels_)
            cluster_labels.append(labels_)

    if n_components > 0:
        print("Formed %d clusters after reducing "
              "to %d dimensions." % (k, n_components))
    else:
        print("Formed %d clusters w/o SVD." % k)

    return km.labels_.tolist(), km.cluster_centers_, kwd_vecs, cluster_labels
    

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
                   stopwords=[], fields=""):

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
    with open_by_suffix(file) as f:
        for line in f:
            if "inspec" in file:
                terms = tokenize.split(line.lower())
            elif "plos" in file or "pmc" in file:
                _, title, abs, body, m = \
                    line.rstrip().split('\t')
                text = ""
                if "title" in fields:
                    text += title
                if "abstract" in fields:
                    text += " " + abs
                if "body" in fields:
                    text += " " + body
                if text == "":
                    text = title+" "+abs+" "+body 
                terms = tokenize.split(text.lower())
                mesh.append(m.split('|'))
            else:
                pmid, title, abs, m, _ = line.split('\t')
                terms = tokenize.split((title+" "+abs).lower())
                meshes = m.split('|')
                tmp = []
                for m in meshes:
                    tmp.append(m.split('/')[0])
                mesh.append(tmp)
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
def compute_tfidf(docs, df, weight, rank=0):

    dfr = dict() # df considering only top R terms per document
    for i in range(len(docs)):
        for w in docs[i]:
            # set infrequent term's tf to 0
            if w not in df:
                docs[i][w] = 0
                continue
            # tfidf
            if weight == 'tfidf':
                docs[i][w] *= math.log(len(docs)/df[w])
            elif docs[i][w] != 0: # 'binary' if not 'tfidf'
                docs[i][w] = 1

        
        # Ignore if rank = 0
        if rank > 0:
            # Sort and extract top R terms for this document
            terms_sorted = sorted(docs[i].items(), reverse=True, 
                                  key=operator.itemgetter(1))
            top_r = terms_sorted[:rank]

            # Count new df for only top R
            for w, _ in top_r:
                if w in dfr:
                    dfr[w] += 1
                else:
                    dfr[w] = 1

    return docs, dfr


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
Sort and output results (discovered keywords)
'''
def output_keywords(num_docs, dfr, df, p_docs=0.5, html=False):
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
        if not html:
            print("%s\t%d\t%d" % (w, df[w], dfr[w]))
        keywords.append(w)
        dfs.append(df[w])
        dfrs.append(dfr[w])

    d = pd.DataFrame({"Term": keywords, "DF": dfs, "DFR": dfrs},
                     columns=["Term", "DF", "DFR"])
    
    if html:
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
Maximin clustering (old, not used)
'''
def maximin_old(csv_dir, docs, file_sim, cluster, keywords, 
                theta=0.9, verbose=True):

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
        m = m / norm(m, axis=1)[:,np.newaxis]
        sim = m * m.transpose()
    else: # assume 'term' if not 'document'
        m = m.transpose() / norm(m, axis=0)[:,np.newaxis]
        sim = m * m.transpose()

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


    # Maximin
    centroids = []
    candidates = list(range(sim.shape[0]))

    # pick the first centroid
    centroids.append(candidates.pop(0)) # pick the first
    #centroids.append(candidates.pop(\
    #        random.randint(0, len(docs)))) # pick randomly

    # Find next centroid iteratively
    while True:
        sim_max = sim[centroids,:].max(axis=0) # take max as this is
                                               # similarity
        maximin_id = sim_max.argmin()
        maximin = 1 - sim_max.min() # make similarity to distance
        
        if maximin > theta:
            #print(maximin)
            centroids.append(candidates.pop(\
                    candidates.index(maximin_id)))
            #print(centroids)
        else:
            break

    # Results
    print("%d clusters generated" % len(centroids))
    print()

    # Show clusters
    if cluster == "document":
        membership = sim[centroids,:].argmax(axis=0).tolist()[0]
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
                
    return centroids, membership, sim

'''
Maximin (core)
'''

def maximin_core(docs, m, cluster="document", theta=0.9, verbose=False):
    sim = np.array(m.dot(m.transpose()))
    np.fill_diagonal(sim, -2) # need to set smaller than -1
    centroids = []
    candidates = list(range(sim.shape[0]))

    # pick the first centroid
    centroids.append(candidates.pop(0)) # pick the first
    #centroids.append(candidates.pop(\
    #        random.randint(0, len(docs)))) # pick randomly

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
    if cluster == "document":
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

    return centroids, membership, sim


'''
Maximin clustering wrapper
'''
def maximin(csv_dir, docs, file_sim, cluster, keywords, 
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
        #m = m / norm(m, axis=1)[:,np.newaxis]
    else: # assume 'term' if not 'document'
        #m = m.transpose() / norm(m, axis=0)[:,np.newaxis]
        m = m.transpose()

    # SVD
    cluster_labels = []
    if n_components == 0: # no svd
        m = m / norm(m, axis=1)[:,np.newaxis]
        centroids, membership, sim = \
            maximin_core(docs, m, cluster, theta, verbose)
    else: # apply svd then cluster
        svd_model = TruncatedSVD(n_components=n_components)
        svd_model.fit(m)
        reduced_m = svd_model.transform(m)
        reduced_m = reduced_m / \
            np.linalg.norm(reduced_m, axis=1)[:,np.newaxis]
        centroids, membership, sim = \
            maximin_core(docs, reduced_m, cluster, theta, verbose)

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
              "to %d dimensions." % (len(set(membership)),
                                     n_components))
    else:
        print("Formed %d clusters w/o SVD." % \
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
                
    return centroids, membership, sim



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
        if len(h) > 0: # exclude doc w/ no terms
            docs_new.append(h)
            if len(mesh) != 0:
                mesh_new.append(mesh[i])

    return docs_new, mesh_new

'''
main
'''
if __name__ == "__main__":
    main()
