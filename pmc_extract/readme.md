# PMC XML Extraction and Indexing

## Description of the folders
* conf: the configuration files of building solr core for PMC data
* extract_pmc_7.py: the python script for extracting PMC data and indexing them in a format recognizable by solr


## Extraction
Use the following code to extract information from the articles in PMC dataset and write them in a format readbale by Solr.

`<python extract_pmc_7.py --input <the directory of your input files> --output <the directory of your output files>>`

**Notes:**
1. The input directory should contain the original artiles from PMC, which are in formats of xml/nxml/nxml.gz.
2. The output directory is for your outputs after doing the extraction. The output files will be in a format of xml. Make sure
   the output directory exists before you start extracting.
3. The output files contain the following fields: pmid, journal name, publication date, publication date in month(for faceting),
   subject, title, author, authors' affiliate, abstract and body.
4.The process may be time consuming depending on the size of the input. 


## Indexing
Use the following steps to build a Solr core and index the extracted data:

`< solr start 

solr create -c <name of your core> -d <directory containing conf folder> 
   
post -c <name of your core> <directory of the extracted files>>`

**Notes:**
1. Make sure you have Solr successfully installed before you start indexing.
2. The code above is for indexing on local server, make sure you have enough disk space before indexing.
3. Depending on the format of the original artiles, the output may be empty (fail to extract the information). In this
   situation, an error message will be given. Check the original articles to see if you want to ignore them.
4. The process may be time consuming depending on the size of the input. 
