'''

Excract information from Medline to be indexed for Solar.

Resulting data (pmc_xml) can be sent to Solar as follows:



$ solr create -c pmc -d conf

$ post -c pmc pmc_xml



Solr server may need to be restarted before retrieving

documents.


'''



import os

import shutil

import logging, argparse

import glob, gzip

import xml.etree.ElementTree as etree

import re



# log file

logging.basicConfig(filename='.extract_pmc.log',

                    level=logging.DEBUG, filemode='w')



# arguments

parser = argparse.ArgumentParser()

parser.add_argument("--input", default='/Users/mikawang/works/Health Informatics/work/plos/PMC2875553.nxml',

                    help="input file/dir (default: data/pmc20180503)")

parser.add_argument("--output", default='/Users/mikawang/Desktop/data/pmc_xml',

                    help="output directory (default: pmc_xml)")

parser.add_argument("--verbose", type=int, default=0,

                    help="verbose level (default: 0)")

args = parser.parse_args()

logging.info(args)





# get input file list

files = [args.input]

if(os.path.isdir(args.input)):

    files = glob.glob(args.input + '/**/*.xml', recursive=True)

    files += glob.glob(args.input + '/**/*.nxml', recursive=True)

    files += glob.glob(args.input + '/**/*.xml.gz', recursive=True)

    files += glob.glob(args.input + '/**/*.nxml.gz', recursive=True)



    

# create output directory

if os.path.exists(args.output):

    shutil.rmtree(args.output)

os.mkdir(args.output)





# tags

f_pmid = '<field name="pmid">'

f_title = '<field name="title">'

f_abs = '<field name="abstract">'

f_body = '<field name="body">'

f_subj = '<field name="subject">'

f_auth = '<field name="author">'

f_authaf = '<field name="author_affiliate">'

f_date = '<field name="publication_date">'

f_date_f = '<field name="publication_date_facet">'

f_jour = '<field name="journal_name">'

close = '</field>\n'





# regular expression

regex = re.compile('\s+')





# unescape special characters

def unescape(str):

    str = str.replace('&amp;', '&')

    str = str.replace('&apos;', "'")

    str = str.replace('&quot;', '"')

    str = str.replace('&gt;', '>')

    str = str.replace('&lt;', '<')

    return str





# escape special characters

def escape(str):

    str = str.replace('&', ' &amp; ')

    str = str.replace('\'', ' &apos; ')

    str = str.replace('"', ' &quot; ')

    str = str.replace('>', ' &gt; ')

    str = str.replace('<', ' &lt; ')

    return str





# file opener depending on suffix

def open_by_suffix(filename):

    if filename.endswith('.gz'):

        return gzip.open(filename, 'rb')

    elif filename.endswith('.bz2'):

        return bz2.BZ2file(filename, 'r')

    else:

        return open(filename, 'r')





# process each file

for file in files:



    if args.verbose >= 0:

        print("Reading " + file + "...")



    pmid = ''

    pubid = ''

    title = ''

    abs = ''

    body = ''

    pub_date = ''

    pub_date_facet = ''

    subj = []

    author_ = []

    author = []

    affiliate = dict()



    # open input file

    with open_by_suffix(file) as f:



        # output file name

        file_out = re.sub("nxml(\.gz)?", "xml",

                          os.path.split(file)[-1])

        if args.verbose >= 2:

            print("output: " + file_out)



        # create output file

        with open(os.path.join(args.output, file_out), 'w') as f_out:



            tree = etree.parse(f)

            root = tree.getroot()

            

            #get journal name
            
            
            if root.find('front/journal-meta/'

                         'journal-title-group/'
                                  
                         'journal-title') != None:
                
               jour_name = root.find('front/journal-meta/'

                                  'journal-title-group/'

                                  'journal-title').text
                                     
            elif root.find('front/journal-meta/'
                                  
                           'journal-title') != None:
                
               jour_name = root.find('front/journal-meta/'

                                     'journal-title').text                    
                                   
            if jour_name == "" or jour_name == None:
                file_out = file_out+".jour"
                print("No Journal Name: "+ jour_name)
            

            

            for e in root.find('front/article-meta'):

                

                # get pmid and publisher id

                if 'pub-id-type' in e.attrib:

                    if e.attrib['pub-id-type'] == 'pmid':

                        pmid = e.text

                        if pmid == None:

                            pmid = 'not_found'

                        else:

                            pmid = pmid.replace(' ', '')

                        if args.verbose >= 1:

                            print(pmid)

                    elif e.attrib['pub-id-type'] == "publisher-id":

                        pubid = e.text

                        if pubid == None:

                            pubid = 'not_found'

                        else:

                            pubid = pubid.replace(' ', '')

                        if args.verbose >= 1:

                            print(pubid)

                        

                # get author name and affiliation

                elif e.tag == 'contrib-group':

                    for e_ in e.findall('contrib'):

                        author_tuple_ = []
                        
                        aff = []
                        
                        aff_ = "None"

                        if 'contrib-type' in e_.attrib and \
                                e_.attrib['contrib-type'] == \
                                "author":

                            for e_0 in e_:

                                if e_0.tag == 'name':

                                    name = ''

                                    for e_name in e_0:

                                        if e_name.tag == 'surname':
                                            
                                            surname = e_name.text
                                            
                                            if surname == None:
                                                
                                                name += 'No surname'
                                                
                                            else:

                                                name += e_name.text

                                        elif e_name.tag == 'given-names':
                                            
                                            given = e_name.text
                                            
                                            if given == None:
                                                
                                                name +=', No given name'
                                            
                                            else:

                                                name += ', ' + e_name.text
                                    
                                    name = escape(regex.sub(' ', name))

                                elif e_0.tag == 'xref':
                                    
                                    if"ref-type" in e_0.attrib and \
                                        e_0.attrib['ref-type'] == 'aff':
                                        
                                        if 'rid' in e_0.attrib:
                                            
                                            aff_ = e_0.attrib['rid']
                                        
                                            aff += [aff_]          
                                
                                

                            author_tuple_ = [(name, aff)]

                        author_ += author_tuple_
                        #author_dict = dict(author_) 
                        # in the format of {'Smith, Jane': ['aff002', 'aff003']}



                # get affiliation



                elif e.tag == 'aff':
                    
                   if 'id' in e.attrib:
                       
                       aff_id = e.attrib['id']
            
                       if aff_id.startswith('aff'):
                           
                           if e.find('addr-line') != None:
                               
                               affiliate[aff_id] = \
                                    ''.join(e.find('addr-line').itertext())
                                    
                               affiliate[aff_id] = \
                                   escape(regex.sub(' ', affiliate[aff_id]))
                                    # in the format of {'aff002': 'UNC-CH'}
                           
                           elif ''.join(e.itertext()) != None:
                               
                                affiliate[aff_id] = \
                                        ''.join(e.itertext())                     
                               
                                if re.findall("^[0-9] ",''.join(e.itertext())) != []:
                                   
                                    affiliate[aff_id] = \
                                        ''.join(e.itertext())[2:]                       
                              
                                affiliate[aff_id] = \
                                   escape(regex.sub(' ', affiliate[aff_id]))               
                           else: 
                               print("No address line")
                                

                   

                # get publication date

                

                elif e.tag == 'pub-date' :
                    
                    e_year = '0000'
            
                    e_day = '00'
                
                    e_month = '00'
                    
                    date_e = []
                    
                    for e_0 in e.attrib:
            
                        if 'epub' in e.attrib[e_0]:
                            
                            date_e = e
                            
                            break
                            
                        elif 'pub' in e.attrib[e_0]:
                            
                            date_e = e
                            
                    if date_e != []:
                            
                        for e_ in date_e:
                
                            if e_.tag == 'year':
                
                                e_year = e_.text
                
                            elif e_.tag == 'day':
                
                                e_day = e_.text
                
                            elif e_.tag == 'month':
                
                                e_month = e_.text
                
                                if len(e_month) == 1:
                
                                    e_month = "0"+ e_month

            

                # get categories

                elif e.tag == 'article-categories':

                    for e_ in e.findall('subj-group'):

                        if 'subj-group-type' in e_.attrib and \
                                e_.attrib['subj-group-type'] != \
                                'heading':

                            subj_ = []

                            for s in e_.itertext():

                                s = s.strip()

                                if s != '':

                                    subj_.append(s)

                            subj.append('/'.join(subj_))

                    if args.verbose >= 1:

                        print('\n'.join(subj))



                # get title

                elif e.tag == 'title-group':

                    title = ''.join(e.find('article-title').itertext())

                    if title == None:

                        print(pmid + ': no title')

                        title = ""

                    title = escape(regex.sub(' ', title))

                    if args.verbose >= 1:

                        print(title)



                # get abstract

                elif e.tag == 'abstract' and \
                        'abstract-type' not in e.attrib:

                    abs = ''

                    for p in e:

                        t = ' '.join(p.itertext())

                        if t != None:

                            abs += ' ' + t

                    if abs == None:

                        print(pmid + ': no abstract')

                        abs = ""

                    abs = escape(regex.sub(' ', abs))

                    if args.verbose >= 2:

                        print(abs)



            if args.verbose >= 1:

                print('\n'.join([str(x) for x in author_]))

                print('\n'.join([str((x, affiliate[x])) \
                                 for x in affiliate]))





            # get body element. skip if not found 

            e_body = root.find('body')

            if e_body == None:

                if args.verbose >= 2:

                    print(pmid + ': no body text')

                continue



            # extract all text within <body>

            body = ' '.join(e_body.itertext())

            body = escape(regex.sub(' ', body))

            if args.verbose >= 3:

                print(body)



            if args.verbose > 0:

                print()



            # use pubid as pmid if pmid is not found

            if pmid == "" and pubid != "":

                pmid = pubid



            # create author and affiliation fields

            for auth_tup in author_:

                aff_id = auth_tup[-1]

                auth_name = auth_tup[0]
                
                affs = []
            
                
                if aff_id == []:
                    
                    affs = ["Not found"]
                
                else:
                
                    for id_ in aff_id:
    
                        if id_ == "None":
        
                            author.append((auth_name, aff_id))
        
                        elif id_ in list(affiliate):
                            
                            affs.append(affiliate[id_])
    
                author.append((auth_name, affs))

            

            auth_n_aff_ = ''

            for tup in author:
                
                aff_temp = ""
                
                for aff in tup[-1]:
                    
                    aff_temp += aff+"; "

                auth_n_aff_temp = f_auth + tup[0] + close +\
                                f_authaf + aff_temp + close

                auth_n_aff_ += auth_n_aff_temp


            #create date field
            pub_date += e_year + '-' + e_month + '-' + e_day

            pub_date_facet += e_year + '-' + e_month
            


            # create subject fields

            subj_ = ""

            for s in subj:

                subj_ += f_subj + s + close

            if args.verbose >= 2:

                print("subjects: " + subj_)



            # output

            try:

                f_out.write('<add>\n<doc>\n' +\

                            f_jour + jour_name + close +\

                            f_pmid + pmid + close +\

                            f_title + title + close +\

                            subj_ +\

                            auth_n_aff_ +\

                            f_date + pub_date + close +\

                            f_date_f + pub_date_facet + close +\

                            f_abs + abs + close +\

                            f_body + body + close +\

                            '</doc>\n</add>\n')

            except TypeError:

                print('TypeError')



