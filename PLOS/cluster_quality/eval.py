"""
Evaluation script
"""

import re
import logging, argparse
import numpy as np
from numpy import linspace

import visual_library as vl

csv_dir = 'csv'

# log output
logging.basicConfig(filename='.eval.log',
                    format='%(asctime)s : %(levelname)s'
                    ': %(message)s', level=logging.INFO)

# Parse commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", 
                    default='brca_med_top4_10k.txt.gz', 
                    help="Input file (default: "
                    "brca_med_top4_10k.txt.gz)")
parser.add_argument("-o", "--output", 
                    default='eval_output.csv', 
                    help="Output file (default: eval_output.csv)")
parser.add_argument("-f", "--fields", 
                    default="", 
                    help="Text fields to be used. One or any "
                    "combination of title, abstract, and body. "
                    "If not specified, all fields are used "
                    "(default: \"\")")
parser.add_argument("-r", "--rank", 
                    default="6,8,10,12,14,16", 
                    help="Rank R value(s) to be used, separated "
                    "by comma. (default: \"6,8,10,12,14,16\")")
parser.add_argument("-d", "--relative_df", 
                    default="0.6,0.8,1.0,1.2,1.4,1.6", 
                    help="Relative DF value(s) to be used, separated "
                    "by comma. (default: \"0.6,0.8,1.0,1.2,1.4,1.6\")")
parser.add_argument("-n", "--dimensions", 
                    default="0,10,20,30,40,50", 
                    help="Number of components for SVD, separated "
                    "by comma. (default: \"0,10,20,30,40,50\")")
parser.add_argument("-t", "--theta", 
                    default="0.8,0.9,0.99", 
                    help="Theta values to be used for maximin, "
                    "separated by comma. (default: \"0.8,0.9,0.99\")")
parser.add_argument("-k", "--kmeans", 
                    default="4", 
                    help="k values to be used for kmeans, "
                    "separated by comma. (default: \"4\")")
parser.add_argument("--df", 
                    default="10,30,50,70,100", 
                    help="minimum df values to be considered, "
                    "separated by comma. (default: \"10,30,50,70,100\")")
parser.add_argument("--sample", 
                    default="0", type=int,
                    help="number of articles sampled. Use all "
                    "0 is given (default: 0)")
parser.add_argument("--format", default="abs", 
                    help="Input file format (line|abs|full) "
                    "(default: abs)")
parser.add_argument('--single',
                    help='Evaluate only single-class instances. '
                    '(default: False)',
                    action='store_true')
parser.add_argument('--balance',
                    help='Balance the data. (default: False)',
                    action='store_true')

args = parser.parse_args()

logging.info(args)


# Read stopword list
stopwords = vl.read_stopwords()            


# Balance the data
if args.balance and re.search("(plos|pmc|med)", args.input):
    vl.balance_data(file=args.input)
    input_file = ".balanced_"+args.input
else:
    input_file = args.input


# Read documents
print("Reading documents...")
docs, df, w2id, mesh = vl.read_documents(
    "", input=input_file, stopwords=stopwords,
    fields=args.fields, single_class=args.single,
    n_samples=args.sample, format=args.format)
print("Finished reading %d documents" % len(docs))
print("%d terms were identified" % len(df))

    
'''
try different parameter combinations
'''

with open(args.output, "w") as f:

    f.write("df,r,d,n,alg,theta,k,c,h,vd,v,ari,ami,fms,prtm,prt,sc,sct\n")

    '''
    Use VCGS for feature selection
    '''

    # Discard low and high DF terms
    mindf = 1
    vl.del_low_high_df(df, mindf, len(docs))
    
    # rank is R in vcgs
    for rank in [int(x) for x in args.rank.split(',')]:
        if rank == -1:
            break

        # Compute tfidf and extract top R (rank) terms
        docs_, dfr = vl.compute_tfidf(docs, df, "tfidf", rank)
        
        # p_docs is D in vcgs
        for p_docs in [float(x) for x in args.relative_df.split(',')]:
            if p_docs <= 0:
                
                try:
                    k = int(args.kmeans)
                except:
                    print("Error: k=\"%s\" is not valid" % args.kmeans)
                    exit()

                # Identify R*k keywords
                keywords = vl.identify_n_keywords(dfr, df, rank*k)

            else:
                # Identify keywords appearing in more than p_docs% of
                # docs
                keywords = vl.identify_keywords(
                    len(docs_), dfr, df, p_docs)

            print("%d keywords were found" % len(keywords))
            if len(keywords) < 2:
                print("Vocabulary is too small. Skipping.")
                break

            # Create new matrix with the keywords (mesh is also needed
            # in case some docs are removed)
            docs_small, mesh_small = vl.update(docs_, keywords, mesh)
            print("Document size reduced from %d to %d." % \
                  (len(docs_), len(docs_small)))

            # clustering
            for svd in [int(x) for x in args.dimensions.split(',')]:
                # error check
                if svd == -1 or svd >= len(keywords): 
                    break

                # maximin
                for theta in [float(x) for x in args.theta.split(',')]:
                    if theta <= 0:
                        break

                    _, membership, _, sc, sct = \
                        vl.maximin(csv_dir, docs_small, "", 
                                   "document", keywords,
                                   np.array(mesh_small).ravel(), 
                                   theta, svd)

                    # error check
                    if len(set(membership)) == 1:
                           print("# clusters = 1.  Skipping...")
                           continue

                    # output
                    
                    results = vl.evaluate(mesh_small, membership)
                    results = results + (sc,sct,)
                    print(" Silhouette   = %f" % sc)
                    print(" Silhouette_t = %f" % sct)

                    f.write("%d,%d,%.2f,%d,maximin,%.2f,%d," % \
                                (mindf,rank, p_docs, svd, theta, 
                                 len(set(membership))))
                    f.write(",".join(["{:.4f}".format(x) \
                                          for x in results]))
                    f.write("\n")

                # kmeans
                for n_clusters in [int(x) for x in args.kmeans.split(',')]:
                    # error check
                    if n_clusters <= 0 or \
                            n_clusters >= len(docs_small): 
                        break

                    membership, _, _, _, sc, sct = \
                        vl.kmeans(docs_small,
                                  "document", keywords, svd,
                                  n_clusters, np.array(mesh_small).ravel())

                    # output
                    results = vl.evaluate(mesh_small, membership)
                    results = results + (sc, sct,)
                    print(" Silhouette   = %f" % sc)
                    print(" Silhouette_t = %f" % sct)

                    f.write("%d,%d,%.2f,%d,kmeans,nan,%d," % \
                                (mindf,rank, p_docs, svd, n_clusters))
                    f.write(",".join(["{:.4f}".format(x) for x in results]))
                    f.write("\n")

                # spectral clustering
                for n_clusters in [int(x) for x in args.kmeans.split(',')]:
                    # error check
                    if n_clusters <= 0 or \
                            n_clusters >= len(docs_small): 
                        break

                    membership, sc, sct = vl.spectral(
                        docs_small, "document", keywords, svd,
                        n_clusters, np.array(mesh_small).ravel())

                    # output
                    results = vl.evaluate(mesh_small, membership)
                    results = results + (sc, sct,)
                    print(" Silhouette   = %f" % sc)
                    print(" Silhouette_t = %f" % sct)

                    f.write("%d,%d,%.2f,%d,spectral,nan,%d," % \
                                (mindf,rank, p_docs, svd, n_clusters))
                    f.write(",".join(["{:.4f}".format(x) for x in results]))
                    f.write("\n")

    
    '''
    simply use df for feature selection
    '''

    # Remove terms whose df is lower than mindf
    for mindf in [int(x) for x in args.df.split(',')]:
        
        if mindf == -1:
            break

        vl.del_low_high_df(df, mindf, len(docs))
        
        # Compute tfidf. Use rank=0 to disable VCGS
        docs_, _ = vl.compute_tfidf(docs, df, "tfidf", rank=0)

        # Use words remaining in df as keywords
        keywords = list(df.keys())
        print("%d keywords were found" % len(keywords))
        if len(keywords) < 2:
            print("Vocabulary is too small. Skipping.")
            break

        # Create new matrix with the keywords (mesh is also needed
        # in case some docs are removed)
        docs_small, mesh_small = vl.update(docs_, keywords, mesh)
        print("Document size reduced from %d to %d." % \
              (len(docs_), len(docs_small)))

        # clustering

        for svd in [int(x) for x in args.dimensions.split(',')]:
            # error check
            if svd == -1 or svd >= len(keywords): 
                break

            # maximin
            for theta in [float(x) for x in args.theta.split(',')]:
                if theta <= 0:
                    break

                _, membership, _, sc, sct = \
                        vl.maximin(csv_dir, docs_small, "", 
                                   "document", keywords,
                                   np.array(mesh_small).ravel(),
                                   theta, svd)

                # error check
                if len(set(membership)) == 1:
                       print("# clusters = 1.  Skipping.")
                       continue

                # output
                results = vl.evaluate(mesh_small, membership)
                results = results + (sc, sct,)
                print(" Silhouette   = %f" % sc)
                print(" Silhouette_t = %f" % sct)

                f.write("%d,nan,nan,%d,maximin,%.2f,%d," % \
                            (mindf, svd, theta, len(set(membership))))
                f.write(",".join(["{:.4f}".format(x) for x in results]))
                f.write("\n")

            # kmeans
            for n_clusters in [int(x) for x in args.kmeans.split(',')]:
                # error check
                if n_clusters == -1 or \
                        n_clusters >= len(docs_small): 
                    break

                membership, _, _, _, sc, sct = \
                    vl.kmeans(docs_small,
                              "document", keywords, svd,
                              n_clusters, np.array(mesh_small).ravel())

                # output
                results = vl.evaluate(mesh_small, membership)
                results = results + (sc, sct,)
                print(" Silhouette   = %f" % sc)
                print(" Silhouette_t = %f" % sct)

                f.write("%d,nan,nan,%d,kmeans,nan,%d," % \
                            (mindf, svd, n_clusters))
                f.write(",".join(["{:.4f}".format(x) for x in results]))
                f.write("\n")

            # spectral clustering
            for n_clusters in [int(x) for x in args.kmeans.split(',')]:
                # error check
                if n_clusters < 0 or \
                        n_clusters >= len(docs_small): 
                    break

                membership, sc, sct = vl.spectral(
                    docs_small, "document", keywords, svd,
                    n_clusters, np.array(mesh_small).ravel())

                # output
                results = vl.evaluate(mesh_small, membership)
                results = results + (sc, sct,)
                print(" Silhouette   = %f" % sc)
                print(" Silhouette_t = %f" % sct)

                if rank <= 0:
                    f.write("%d,nan,nan,%d,spectral,nan,%d," % \
                                (mindf, svd, n_clusters))
                else:
                    f.write("%d,%d,%.2f,%d,spectral,nan,%d," % \
                                (mindf,rank, p_docs, svd, n_clusters))
                f.write(",".join(["{:.4f}".format(x) for x in results]))
                f.write("\n")
