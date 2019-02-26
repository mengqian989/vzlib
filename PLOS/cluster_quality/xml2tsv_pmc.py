'''
Excract information from Entrez (PMC) results and output as TSV
file. Only output articles included in the file specified by --med.

'''

import os
import logging, argparse
import glob, gzip
import xml.etree.ElementTree as etree
import re

# log file
logging.basicConfig(filename='.extract_pmc.log',
                    level=logging.DEBUG, filemode='w')

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", default='plos_pmc.xml.gz',
                    help="input file (default: "
                    "plos_pmc.xml.gz)")
parser.add_argument("--med", default='plos_med_top6.txt',
                    help="corresponding pubmed file (default: "
                    "plos_med_top6.txt)")
args = parser.parse_args()
logging.info(args)

# regular expression
spaces = re.compile('\s+')
delimiters = re.compile('[\|\+]')

def unescape(str):
    str = str.replace('&amp;', '&')
    str = str.replace('&apos;', "'")
    str = str.replace('&quot;', '"')
    str = str.replace('&gt;', '>')
    str = str.replace('&lt;', '<')
    return str

# read --med file
med = dict()
with gzip.open(args.med) as f:
    for line in f:
        pmid, title, abs, mesh, _ = line.decode().split('\t')
        mesh = '|'.join(list(set(delimiters.split(mesh))))
        if abs == '':
            abs = 'None'
        med[pmid] = [title, abs, mesh]


# read file
with gzip.open(args.input) as f:

    tree = etree.parse(f)
    root = tree.getroot()
    
    # extract pmid and body text
    for article in root:
        pmid = ''
        body = ''

        for e in article.find('front/article-meta'):
            if 'pub-id-type' in e.attrib and \
                    e.attrib['pub-id-type'] == 'pmid':
                pmid = e.text.replace(' ', '')
                #print(pmid)
        # skip if pmid is not in medline file
        if pmid not in med:
            continue

        # get body element. skip if not found 
        e_body = article.find('body')
        if e_body == None:
            sys.stderr.write(pmid + ": no body text found")
            continue

        # extract all text within <body>
        body = ' '.join(e_body.itertext())
        body = unescape(body)
        body = spaces.sub(' ', body)
        #print(body)

        # write out
        try:
            title, abs, mesh = med[pmid]
            print(pmid + "\t" + title + "\t" + abs \
                  + "\t" + body + "\t" + mesh)
            pmid = ''
            body = ''

        except TypeError:
            sys.stderr.write('TypeError')

