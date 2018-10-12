'''
Extract title, abstract, and mesh from PubMed XML data

'''

import os, sys
import logging, argparse
import gzip
import xml.etree.ElementTree as etree
import re

# regular expression
regex = re.compile('\s+')

# class filter for --restrict
classes = {"Carcinoma, Ductal, Breast",
           "Carcinoma, Lobular",
           "Triple Negative Breast Neoplasms",
           "Breast Neoplasms, Male"}

# generalize to MeSH one-level below the targe 
target_mesh = "Breast Neoplasms" 

# log file
logging.basicConfig(filename='.extract.log',
                    level=logging.DEBUG, filemode='w')

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", default='brca_med.xml.gz',
                    help="input file (default: brca_med.xml.gz)")
parser.add_argument('--restrict',
                    help='Restrict output by classes. '
                    '(default: False)',
                    action='store_true')
parser.add_argument('--code',
                    help='Output MeSH tree number (code) too '
                    '(default: False)', action='store_true')
parser.add_argument('--generalize',
                    help='Output MeSH generalized tree number '
                    '(code) by ascending up to target MeSH given'
                    '(default: False). Must be used with --code',
                    action='store_true')
parser.add_argument('--major',
                    help='Consider only major MeSH terms'
                    '(default: False)', action='store_true')
args = parser.parse_args()
logging.info(args)


'''
Read MeSH tree numbers
'''

mesh2code = dict()
code2mesh = dict()
if args.code:
    with open("MeSH/d2018.bin") as f:
        cnt = 0
        mh = ''
        mn = []
        for line in f:
            cnt += 1
            line = line.rstrip()
            if line == "*NEWRECORD":
                continue
            if line == "":
                if mh == '' or len(mn) == 0:
                    sys.stderr.write(\
                        "No MeSH heading or code found "
                        "at line %d\n" % cnt)
                    continue
                mesh2code[mh] = mn
                for c in mn:
                    code2mesh[c] = mh
                mh = ''
                mn = []
                continue

            try:
                k, v = re.split(" = ", line, maxsplit=1)
            except ValueError as e:
                sys.stderr.write("line %d: %s\n" % (cnt, str(e)))
            if k == "MH":
                mh = v
            elif k == "MN":
                mn.append(v)

    # Add Female and Male since they're replaced with Women and Men,
    # respectively, and not associated with their codes in the current
    # MeSH file.
    mesh2code["Female"] = ["M01.975"]
    mesh2code["Male"] = ["M01.390"]

    # Get target code(s)
    if args.generalize:
        target_codes = mesh2code[target_mesh]


'''
Generalize given codes up to right below target_codes
'''

def generalize(codes):
    parents = []
    for c in codes:
        for tc in target_codes:
            m = re.match('(' + tc+'\.\d+)', c)
            if m:
                parents.append(m.group(1))
    return list(set(parents))


'''
Read file and extract information
'''

with gzip.open(args.input) as f:
    tree = etree.parse(f)
    root = tree.getroot()
    for article in root:
        # get PMID
        mc = article.find('MedlineCitation')
        pmid = mc.find('PMID').text
        # get title
        art = mc.find('Article')
        title = ''.join(art.find('ArticleTitle').itertext())
        title = regex.sub(' ', title)
        # get abstract
        try:
            abstract = ''.join(art.find('Abstract/AbstractText').itertext())
            abstract = regex.sub(' ', abstract)
        except AttributeError:
            abstract = ''
        # get MeSH terms (only major)
        mesh_list = []
        code_list = []
        try:
            for mh in mc.find('MeshHeadingList'):
                d = mh.find('DescriptorName')
                isMajor = False
                for q in mh.findall('QualifierName'): # check all quals
                    if q.attrib['MajorTopicYN'] == 'Y':
                        isMajor = True
                if not args.major or \
                        d.attrib['MajorTopicYN'] == 'Y' or \
                        isMajor:
                    if args.code:
                        out_codes = mesh2code[d.text]
                        if args.generalize:
                            out_codes = generalize(out_codes)
                        if len(out_codes) != 0:
                            code_list.append('+'.join(out_codes))
                            mesh_ = list(set([code2mesh[x] \
                                              for x in out_codes]))
                            mesh_list.append('+'.join(mesh_))
                    else:
                        mesh_list.append(d.text)
        except TypeError:
            pass

        # Retain only target classes
        if args.restrict:
            mesh_list = list(\
                set('+'.join(mesh_list).split('+')) & classes)

        # Skip if there's no MeSH term
        if len(mesh_list) == 0:
            continue

        # Prepare output
        output = pmid + "\t" + title + "\t" + abstract +\
                 "\t" + '|'.join(mesh_list)

        if args.code:
            output += "\t" + '|'.join(code_list)

        print(output)

