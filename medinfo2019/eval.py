"""
Evaluation script
"""

import logging, argparse
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
                    default='data/plos_top6_100.txt.gz', 
                    help="Input file (default: "
                    "data/plos_top6_100.txt.gz)")
parser.add_argument("-o", "--output", 
                    default='eval_output.csv', 
                    help="Output file (default: eval_output.csv)")
parser.add_argument("--mindf", type=int, default=1,
                    help="Ignore terms below mindf "
                    "(default: 1)")
parser.add_argument("-f", "--fields", 
                    default="", 
                    help="Text fields to be used. One or any "
                    "combination of title, abstract, and body. "
                    "If not specified, all fields are used "
                    "(default: \"\")")

args = parser.parse_args()

logging.info(args)

# Read stopword list
stopwords = vl.read_stopwords()            

# Read documents
print("Reading documents...")
docs, df, w2id, mesh = \
        vl.read_documents("", input=args.input,
                          stopwords=stopwords,
                          fields=args.fields)
print("Finished reading %d documents" % len(docs))
print("%d terms were identified" % len(df))

# Remove terms whose df is lower than mindf
inf = []
if args.mindf:
    for w in df:
        if df[w] <= args.mindf:
            inf.append(w)
    for w in inf:
        del df[w]
print("%d terms were removed" % len(inf))

with open(args.output, "w") as f:
    f.write("r,d,n,k,c,h,vd,v,ai,fms\n")

    for rank in range(8, 10):  # rank is R in vcgs
        # Compute tfidf and find key terms
        docs_, dfr = vl.compute_tfidf(docs, df, "tfidf", rank)
        
        for p_docs in linspace(0.01, 0.6, 10): # p_docs is D in vcgs
            # Sort and output results (discovered keywords)
            keywords = vl.output_keywords(len(docs_), dfr, df, p_docs)
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

            '''
            # maximin
            centroids, membership, sim = \
                maximin(csv_dir, docs, args.sim, 
                        args.cluster, keywords, args.theta)
            '''

            # svd + kmeans
            for svd in range(0, 21, 2):  # dimensionality
                if svd >= len(keywords): # error check
                    break
                for n_clusters in range(2, 21, 2):
                    if n_clusters >= len(docs_small): # error check
                        break
                    membership, _, _, _ = \
                        vl.kmeans(docs_small,
                                  "document", keywords, svd,
                                  n_clusters)

                    results = vl.evaluate(mesh_small, membership)

                    f.write("%d,%.2f,%d,%d," % \
                                (rank, p_docs, svd, n_clusters))
                    f.write(",".join(["{:6.4f}".format(x) for x in results]))
                    f.write("\n")
