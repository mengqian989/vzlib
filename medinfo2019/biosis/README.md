# BIOSIS data set

This data set was created as follows:

1. Using their web search interface, queried each of the following phrases (using double quotations before and after them) as "topic":

* Carcinoma, Lobular
* Breast Neoplasms, Male
* Hereditary Breast and Ovarian Cancer Syndrome
* Breast Carcinoma In Situ

Note that the last two are direct children of "Breast Neoplasms" in MeSH hierarchy but are different from the MeSH terms we used for creating the PubMed (and PMC) data set.  This is because "Carcinoma, Ductal, Breast" and "Triple Negative Breast Neoplasms" used for the PubMed data set were not found in biosis databases.

2. Downloaded the results by choosing 

* "Save to other file formats" and then
* Record contents = "Author, Title, Source, Abstract" and 
* File Format = "Tab-Delimited"

Note that the interface allows us download only 500 records at once, so it may need to be repeated by specifying record numbers to fetch.

The number of records for class.

Class | Number of records
------|:----------------:
Carcinoma, Lobular | 1410
Breast Neoplasms, Male | 496
Hereditary Breast and Ovarian Cancer Syndrome | 114
Breast Carcinoma In Situ | 178
