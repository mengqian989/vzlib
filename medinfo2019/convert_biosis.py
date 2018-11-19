#! -*- coding: utf-8 -*-

import logging, argparse
import sys, os
import re
import glob

# log output
logging.basicConfig(filename='.convert_biosis.log',
                    format='%(asctime)s : %(levelname)s'
                    ': %(message)s', level=logging.INFO)

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default='biosis', 
                    help="Input directory (default: biosis)")
parser.add_argument("-o", "--output", default='biosis.txt', 
                    help="Output file (default: biosis.txt)")

args = parser.parse_args()
logging.info(args)

# get file names
files = glob.glob(args.input+"/*.txt")

with open(args.output, "w") as f_out:

    for file in files:

        with open(file) as f:
            # get class name
            cls = file.split("/")[-1].replace(".txt", "")

            # read
            for line in f:
                data = line.split("\t")

                # skip header
                if data[0] == "PT":
                    continue

                # write out title, abs, class
                f_out.write("dummy\t%s\t%s\t%s\tdummy\n" % \
                                (data[5], data[31], cls))

