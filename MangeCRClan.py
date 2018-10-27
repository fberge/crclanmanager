import csv
import re
from datetime import date
import sqlite3
import requests
import os
import ConfigParser


###########################
### CONFIGURATION FILE
iniFile = "conf.ini"

############################
### FIELD NAMES
F_TAG = 'tag'
F_DATE = 'date'
F_ROLE = 'role'
F_EXPLEVEL = 'expLevel'
F_TROPHIES = 'trophies'
F_CLANRANK = 'clanRank'
F_DONATIONS = 'donations'
F_DONATIONSRECEIVED = 'donationsReceived'
F_NAME = 'name'
F_PRES = 'presentation'
F_INCLAN = 'inClan'

############################
### DB TABLES
T_HISTORY = 'hist'
T_MEMBER = 'membre'

############################
### global var
inputCsvFile = 'tmpCsvFile.csv'

######################################################################################
## FUNCTIONS
######################################################################################

############################
### initDb()
### Check DB existance and create it
############################
def initDb():
    # init var
    b_history = False
    b_member = False

    # connect db file
    conn = sqlite3.connect(dbFileName)
    c = conn.cursor()

    # get db tables
    c.execute("select * from SQLite_master")
    tables = c.fetchall()
    
    # parse tables to find T_MEMBER and T_HISTORY
    for table in tables:
        if table[1] == T_MEMBER:
            b_member = True
        if table[1] == T_HISTORY:
            b_history = True

    # if T_MEMBER table doesn't exist, create it
    if b_member == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} text, {} int)".format(T_MEMBER,
                                F_TAG, F_NAME, F_PRES, F_INCLAN)                                                     
        c.execute(reqCreate)

    # if T_HISTORY table doesn't  exist, create it
    if b_history == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} text, {} int, {} int,{} int,{} int,{} int)".format(T_HISTORY,
                                F_TAG, F_DATE, F_ROLE, F_EXPLEVEL, F_TROPHIES, F_CLANRANK, F_DONATIONS, F_DONATIONSRECEIVED)
        c.execute(reqCreate)

    # commit updates   
    conn.commit()

    # close db    
    conn.close()

############################
### is_downloadable(i_url)
### Check if url return downloadable file
### i :
###     i_url : string : url to check
### r : bolean : (true -> downloadable / false)
############################
def is_downloadable(i_url):
    # request header
    h = requests.head(i_url, allow_redirects=True)
    header = h.headers

    # get the content type
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True

############################
### getCsvFile()
### download CSV file on CRAPI
### r : bolean : (true -> downloaded / false)
############################
def getCsvFile():
    # build full URL
    url = apiUrl+clanId+'/'+fileType

    # check if url exists and is downloadable
    if is_downloadable(url) == True:
        # request with GET
        r = requests.get(url)

        # parse content into csv file
        with open(inputCsvFile, 'wb') as f:  
            f.write(r.content)

        return True
    return False

############################
### addHistory(i_history, i_conn)
### add history into db
### i :
###    i_history : dictionary list : full history
###    i_con : connector : db connector
############################
def addHistory(i_history, i_conn):
    # get DB cursor
    cursor = i_conn.cursor()
       
    # for each CVS entry, add as history line into db
    for hisoryLine in i_history:
        createHistoryInput(hisoryLine, cursor)

    # commit updates
    i_conn.commit()

############################
### createHistoryInput(i_hystoryInput, i_cursor):
### add a single history input into db
### i :
###    i_hystoryInput : dictionary : single history
###    i_cursor : cursor : db cursor
############################
def createHistoryInput(i_hystoryInput, i_cursor):
    # create DB request 
    reqAdd = '''INSERT INTO {}({},{},{},{},{},{},{},{})
                VALUES ('{}','{}','{}',{},{},{},{},{});'''.format(T_HISTORY,
                 F_TAG, F_DATE, F_ROLE, F_EXPLEVEL, F_TROPHIES, F_CLANRANK, F_DONATIONS, F_DONATIONSRECEIVED,
                 i_hystoryInput[F_TAG], i_hystoryInput[F_DATE], i_hystoryInput[F_ROLE], i_hystoryInput[F_EXPLEVEL],
                 i_hystoryInput[F_TROPHIES], i_hystoryInput[F_CLANRANK], i_hystoryInput[F_DONATIONS], i_hystoryInput[F_DONATIONSRECEIVED])
    
    # execute reques
    i_cursor.execute(reqAdd)

############################
### createMembers(i_memberList, i_conn)
### add members into db
### i :
###    i_memberList : dictionary list : full members list
###    i_conn : connector : db connector
############################
def createMembers(i_memberList, i_conn):
    # get DB cursor
    cursor = i_conn.cursor()
       
    # for each member in CSV file, add single member
    for member in i_memberList:
        createMember(member, cursor)

    # commit updates
    i_conn.commit()

############################
### createMember(i_member, i_cursor):
### add a single member input into db
### i :
###    i_member : dictionary : single member
###    i_cursor : cursor : db cursor
############################
def createMember(i_member, i_cursor):

    # build a requestion to know if current user already in the DB
    reqFound = "SELECT * FROM {} WHERE {} = '{}'".format(T_MEMBER, F_TAG, i_member[F_TAG])

    # execute the request
    i_cursor.execute(reqFound)

    # if current member is not in the DB, add him
    if (i_cursor.fetchone() == None):
        # build the add request
        reqAdd = '''INSERT INTO {}({},{},{},{}) VALUES ('{}','{}','',1);'''.format(T_MEMBER,
                    F_TAG, F_NAME, F_PRES, F_INCLAN,
                    i_member[F_TAG], i_member[F_NAME])
        # execute it
        i_cursor.execute(reqAdd)
            
############################
### memberInClan(i_listeMembres, i_conn):
### check members mouvements (quit clan / return to clan)
### i :
###    i_listeMembres : dictionary list : full members list
###    i_conn : connector : db connector
############################
def memberInClan(i_listeMembres, i_conn):
    # get the DB cursor
    cursor = i_conn.cursor()
    
    # build the request to get all members mark as in clan in the DB
    reqFound = "SELECT {} FROM {} WHERE {} = {};".format(F_TAG, T_MEMBER, F_INCLAN, 1)

    # for each member in clan
    for row in cursor.execute(reqFound):
        # check if always into the clan in CSV file
        b_found = False
        for member in i_listeMembres:
            if row[0] == member[F_TAG]:
                b_found = True
                break

        # if member quit clan (in DB as inclan and not in clan snapshot)    
        if b_found != True:
            # update inclan field in DB (set to 0)
            reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(T_MEMBER, F_INCLAN, 0, F_TAG, row[0])
            cursor.execute(reqUpdate)

    # build the request to get all members mark as not in clan in the DB
    reqFound = "SELECT {} FROM {} WHERE {} = {};".format(F_TAG, T_MEMBER, F_INCLAN, 0)

    # for each member in clan
    for row in cursor.execute(reqFound):
        # check if always into the clan in CSV file
        b_found = False
        for member in i_listeMembres:
            if row[0] == member[F_TAG]:
                b_found = True
                break
        # if member return in clan (in DB as not inclan and present in clan snapshot)     
        if b_found == True:
            reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(T_MEMBER, F_INCLAN, 1, F_TAG, row[0])
            cursor.execute(reqUpdate)

    # commit updates
    i_conn.commit()

############################
### getConfig():
### Read ini file
### r : boolean : true -> ini file read and correct / false
############################
def getConfig():
    # declare global var
    global dbFileName
    global apiUrl
    global clanId
    global fileType
        
    # read ini file
    config = ConfigParser.ConfigParser()
    config.read(iniFile)

    # try to get each ini files
    # in case of error, return false
    try:
        dbFileName = config.get('DEFAULT', 'dbFileName')
    except:
        return False;
    try:
        apiUrl = config.get('DEFAULT', 'apiUrl')
    except:
        return False;
    try:
        clanId = config.get('DEFAULT', 'clanId')
    except:
        return False;
    try:
        fileType = config.get('DEFAULT', 'fileType')
    except:
        return False;
    return True

############################
### main():
### main function
############################
def main():
    # initialise list of dico
    listeMembers = []
    history = []
    
    # get current date
    today = date.today()

    # read ini file
    print ("Read INI file: ")
    if getConfig() == True:
        print ("               OK")
        # if successfull, download CSV files
        print ("Download CSV file: ")
        if getCsvFile() == True:
            print ("                  OK")
            # if successfull, parse CSV file
            with open(inputCsvFile) as csvfile:
                reader = csv.DictReader(csvfile)

                # for each CSV row, build member list and history list
                for row in reader:
                    lineMember={F_TAG:row[F_TAG],
                                F_NAME:re.sub("[^a-zA-Z0-9_@ ]", "", row[F_NAME])}

                    lineHistory={F_TAG:row[F_TAG],
                                F_DATE:str(today),
                                F_ROLE:row[F_ROLE],
                                F_EXPLEVEL:int(row[F_EXPLEVEL]),
                                F_TROPHIES:int(row[F_TROPHIES]),
                                F_CLANRANK:int(row[F_CLANRANK]),
                                F_DONATIONS:int(row[F_DONATIONS]),
                                F_DONATIONSRECEIVED:int(row[F_DONATIONSRECEIVED])}
                    listeMembers.append(lineMember)
                    history.append(lineHistory)
            # check or create DB
            initDb()

            # open DB
            conn = sqlite3.connect(dbFileName)
         
            # add new members in DB
            createMembers(listeMembers, conn)
            # update member presence in clan in DB
            memberInClan(listeMembers, conn)
            # store history in DB
            addHistory(history,conn)

            # close DB
            conn.close()

            # remove temporary CSV file
            os.remove(inputCsvFile)

########################################################
########################################################
### ENTRY POINT
########################################################
########################################################        
if __name__ == "__main__":    
    main()    
    
