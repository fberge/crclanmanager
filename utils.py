############################
### (c) Frédéric BERGE 2018
### frederic.berge@gmail.com
############################

import re

############################
### removeSpecialChars(i_data):
### remove special chars
### i :
###     i_data : string
### r : string : string without special chars
############################
def removeSpecialChars(i_data):
    return re.sub("[^a-zA-Z0-9_@ ]", "", i_data)

    