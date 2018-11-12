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

parser.add_argument("--input", default='data/pmc20180503',

                    help="input file/dir (default: data/pmc20180503)")

parser.add_argument("--output", default='pmc_xml',

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

f_date_r = '<field name="publication_date_range">'

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

    e_year = ''
            
    e_day = ''
                
    e_month = ''

    pub_date_facet = ''

    subj = []

    author_ = []

    author = []
    
    aff_pool = []
    
    not_match = []
    
    aff_set = []

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
            
            jour_name = escape(regex.sub(' ', jour_name)) 

            

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
                        
                        name = ''

                        if 'contrib-type' in e_.attrib and \
                                e_.attrib['contrib-type'] == \
                                "author":

                            for e_0 in e_:

                                if e_0.tag == 'name':

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
                            aff_pool += aff
                        #author_dict = dict(author_) 
                        # in the format of {'Smith, Jane': ['aff002', 'aff003']}
                    aff_id = ''
                    
                    #get affiliate when aff is under contrib-group
                    
                    for e_ in e.findall('aff'):
                        
                        aff_set = e_ 
                
                        aff_id = ''
                
                        if aff_set != []:
                        
                            if 'id' in aff_set.attrib:
                               
                               aff_id = aff_set.attrib['id']
                               
                            elif ''.join(aff_set.itertext()) != '':
                                
                               aff_id = 'aff_only'   
                               
                            label = ''
                               
                            for e_2 in aff_set:
                               
                               if 'label' in e_2.tag and e_2.text != None:
                                   
                                   label = e_2.text
                
                            if aff_id in aff_pool or \
                               aff_id.startswith('aff') or \
                                   aff_id.startswith('Aff'):
                                       
                               if aff_set.find('institution-wrap') != None:
                                   
                                   aff_set_1 = aff_set.find('institution-wrap')
                                   
                                   aff_wrap = ''
                                   
                                   for e_1 in aff_set_1:
                                       
                                       if e_1.tag == 'institution' and e_1.text != None:
                                           
                                           aff_wrap += e_1.text
                                    
                                   aff_wrap = escape(regex.sub(' ', aff_wrap)) 
                                   affiliate[aff_id] = aff_wrap 
                                   
                                       
                               elif aff_set.find('institution') != None:
                                   
                                   affiliate[aff_id] = \
                                        ''.join(aff_set.find('institution').itertext())
                                        
                                   affiliate[aff_id] = \
                                       escape(regex.sub(' ', affiliate[aff_id]))          
                       
                               
                               elif aff_set.find('addr-line') != None:
                                   
                                   affiliate[aff_id] = \
                                        ''.join(aff_set.find('addr-line').itertext())
                                        
                                   affiliate[aff_id] = \
                                       escape(regex.sub(' ', affiliate[aff_id]))
                                        # in the format of {'aff002': 'UNC-CH'}
                               
                               elif ''.join(aff_set.itertext()) != None:
                                   
                                   aff_ =  ''.join(aff_set.itertext())
                                   
                                   label = re.escape(label)
                                   
                                   if re.findall(label, aff_) != []:
                                       
                                       index = re.search(label, aff_).end()
                                   
                                       aff_ = aff_[index:]
                                   
                                   aff_ = escape(regex.sub(' ', aff_))
                                   
                                   affiliate[aff_id] = aff_ 
                            
                    
                # get affiliation

                elif e.tag == 'aff':
                    
                    aff_id = ''    
                        
                    aff_set = e
                    
                    if 'id' in aff_set.attrib:
               
                       aff_id = aff_set.attrib['id']
                       
                    elif ''.join(aff_set.itertext()) != '':
                        
                       aff_id = 'aff_only'   
                       
                    label = ''
                       
                    for e_ in aff_set:
                       
                       if 'label' in e_.tag and e_.text != None:
                           
                           label = e_.text
                           
                           
        
                    if aff_id in aff_pool or \
                       aff_id.startswith('aff') or \
                           aff_id.startswith('Aff'):
                       
                       if aff_set.find('institution-wrap') != None:
                           
                           aff_wrap = ''
                           
                           for e_ in aff_set:
                               
                               if 'institution' in e_.tag and e_.text != None:
                                   
                                   aff_wrap += e_.text
                            
                           affiliate[aff_id] = aff_wrap
                                        
                       elif aff_set.find('institution') != None:
                           
                           affiliate[aff_id] = \
                                ''.join(aff_set.find('institution').itertext())
                                
                           affiliate[aff_id] = \
                               escape(regex.sub(' ', affiliate[aff_id]))          
                               
                       elif aff_set.find('addr-line') != None:
                           
                           affiliate[aff_id] = \
                                ''.join(aff_set.find('addr-line').itertext())
                                
                           affiliate[aff_id] = \
                               escape(regex.sub(' ', affiliate[aff_id]))
                                # in the format of {'aff002': 'UNC-CH'}
                       
                       elif ''.join(aff_set.itertext()) != None:
                           
                           aff_ =  ''.join(aff_set.itertext())
                           
                           label = re.escape(label)
                           
                           if re.findall(label, aff_) != []:
                               
                               index = re.search(label, aff_).end()
                           
                               aff_ = aff_[index:]
                           
                           aff_ = escape(regex.sub(' ', aff_))
                           
                           affiliate[aff_id] = aff_ 
                       

                # get publication date

                elif e.tag == 'pub-date' :
                    
                    date_e = []
                    
                    for e_0 in e.attrib:
            
                        if 'epub' in e.attrib[e_0]:
                        
                            date_e = e
                            
                    if date_e == []:
                        
                       for e_0 in e.attrib:
                           
                           if 'pub' in e.attrib[e_0]:
                               
                               date_e = e
                            
                    if date_e != []:
                            
                        for e_ in date_e:
                
                            if e_.tag == 'year' and e_.text != None:
                
                                e_year = e_.text
                                
                                #e_year = escape(regex.sub(' ', e_.text))
                
                            elif e_.tag == 'month' and e_.text != None:
                                
                                e_month = e_.text
                                
                                #e_month = escape(regex.sub(' ', e_.text))

                            elif e_.tag == 'day' and e_.text != None:
                                
                                e_day = e_.text
                                
                                #e_day = escape(regex.sub(' ', e_.text))
            

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

                #continue



            # extract all text within <body>

            if e_body != None:
            
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
                
                if auth_name =='':
                    
                    auth_name = "Author Name Not Found"
                
                affs = []
            
                
                if aff_id == []:
                    
                    affs = ["Not found"]
                
                else:
                
                    for id_ in aff_id:
    
                        if id_ == "None":
        
                            author.append((auth_name, aff_id))
        
                        elif id_ in list(affiliate):
                            
                            affs.append(affiliate[id_])
                        
                        elif 'aff_only' in list(affiliate):
                                
                            affs.append(affiliate['aff_only'])
    
                author.append((auth_name, affs))
            
            for e in set(aff_pool):
                
                if e not in set(list(affiliate)):
                    
                    not_match += e
            
            if not_match != [] and len(set(list(affiliate))) == 1:
                
                print ("Warning: author ids don't match with affiliate: only one affiliate")
                    
            elif not_match != []:
                    
                print ("Warning: author ids don't match with affiliate")

            

            auth_n_aff_ = ''

            for tup in author:
                
                aff_temp = ""
                
                for aff in tup[-1]:
                    
                    aff_temp += aff+"; "

                auth_n_aff_temp = f_auth + tup[0] + close +\
                                f_authaf + aff_temp + close

                auth_n_aff_ += auth_n_aff_temp

            #create date field
            if len(e_month) == 1:
        
                e_month = "0"+ e_month
                        
            if e_year != '' and e_month != '':
        
                e_month = '-' + e_month
            
            if e_month != '' and e_day != '':
        
                e_day = '-' + e_day
    
            pub_date = e_year + e_month + e_day
            pub_date = regex.sub('', pub_date)

            
            pub_date_facet = e_year + e_month
            pub_date_facet = regex.sub('', pub_date_facet)
            


            # create subject fields

            subj_ = ""

            for s in subj:
                
                s = escape(regex.sub(' ', s))

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



