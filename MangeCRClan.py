############################
### (c) Frédéric BERGE 2018
### frederic.berge@gmail.com
############################

################################
### IMPORTS
import csv
import re
from datetime import date, datetime
import sqlite3
import requests
import asyncio
import os
import sys
import configparser as ConfigParser
import clashroyale

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

F_BATTLESPLAYED = 'battlesPlayed'
F_PREPAPLAYED = 'collectionDayBattlesPlayed'
F_DATEWAR = 'DateWar'

F_CLANNAME = 'clanName'
F_CLANDESCRIPTION = 'description'
F_MEMBERCOUNT = 'memberCount'
F_REQUIREDSCORE = 'requiredScore'
############################
### DB TABLES
T_HISTORY = 'hist'
T_MEMBER = 'membre'
T_CLAN = 'clan'
T_CLANWAR = 'clanWar'

############################
### global var
inputCsvFile = 'tmpCsvFile.csv'

######################################################################################
## FUNCTIONS
######################################################################################

def removeSpecialChars(i_data):
    return re.sub("[^a-zA-Z0-9_@ ]", "", i_data)

############################
### initDb()
### Check DB existance and create it
### i :
###     i_dbFile : string : db file
### r : conn : db connector
############################
def initDb(i_dbFile):
    # init var
    b_history = False
    b_member = False
    b_clan = False
    b_clanwar = False

    # connect db file
    conn = sqlite3.connect(i_dbFile)
    c = conn.cursor()

    # get db tables
    c.execute("select * from SQLite_master")
    tables = c.fetchall()
    
    # parse tables to find T_MEMBER, T_HISTORY, T_CLAN and T_CLANWAR
    for table in tables:
        if table[1] == T_MEMBER:
            b_member = True
        if table[1] == T_HISTORY:
            b_history = True
        if table[1] == T_CLAN:
            b_clan = True
        if table[1] == T_CLANWAR:
            b_clanwar = True

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

    # if T_CLAN table doesn't  exist, create it
    if b_clan == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} int, {} int)".format(T_CLAN,
                                F_CLANNAME, F_CLANDESCRIPTION, F_MEMBERCOUNT, F_REQUIREDSCORE)
        c.execute(reqCreate)

    # if T_CLANWAR table doesn't  exist, create it
    if b_clanwar == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} int, {} int)".format(T_CLANWAR,
                                F_TAG, F_DATEWAR, F_PREPAPLAYED, F_BATTLESPLAYED)
        c.execute(reqCreate)
    # commit updates   
    conn.commit()

    # return db    
    return conn

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
### addClanWarHistory(i_clanwarhistory, i_conn)
### add history into db
### i :
###    i_clanwarhistory : dictionary list : clan war history
###    i_con : connector : db connector
############################
def addClanWarHistory(i_clanwarhistory, i_conn):
    # get DB cursor
    cursor = i_conn.cursor()

    # for each clan war history
    for clanWarLine in i_clanwarhistory:
        createClanWarInput(clanWarLine, cursor)

    # commit updates
    i_conn.commit()

############################
### addClanWarHistory(i_clanWarLine, i_cursor)
### add single history line into db
### i :
###    i_clanWarLine : dictionary list : clan war history
###    i_cursor : cocursornnector : db cursor
############################
def createClanWarInput(i_clanWarLine, i_cursor):
    # build request : find clanwar history for given date and player tag
    reqFound = "SELECT * FROM {} WHERE {} = '{}' and {} = '{}';".format(T_CLANWAR, 
                                        F_DATEWAR, i_clanWarLine[F_DATEWAR],
                                        F_TAG, i_clanWarLine[F_TAG])

    #execute the request
    i_cursor.execute(reqFound)

    # if no entry is found for the given tag and date
    if (i_cursor.fetchone() == None):
        # build the add request to create new entry of chan war
        reqAdd = '''INSERT INTO {}({},{},{},{}) VALUES ('{}','{}',{},{});'''.format(T_CLANWAR,
                    F_TAG, F_DATEWAR, F_PREPAPLAYED, F_BATTLESPLAYED,
                    i_clanWarLine[F_TAG], i_clanWarLine[F_DATEWAR], 
                    i_clanWarLine[F_PREPAPLAYED], i_clanWarLine[F_BATTLESPLAYED])
        # execute it
        i_cursor.execute(reqAdd)

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

    # build a requestion to find if a date log is already done
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(T_HISTORY, F_DATE, i_history[0][F_DATE])
    
    # execute the request
    cursor.execute(reqFound)

    # if no entry is found for the given date
    if (cursor.fetchone() == None):
        # for each CVS entry, add as history line into db
        for historyLine in i_history:
            createHistoryInput(historyLine, cursor)

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

    # create DB request to add an entry
    reqAdd = '''INSERT INTO {}({},{},{},{},{},{},{},{})
                VALUES ('{}','{}','{}',{},{},{},{},{});'''.format(T_HISTORY,
                F_TAG, F_DATE, F_ROLE, F_EXPLEVEL, F_TROPHIES, F_CLANRANK, F_DONATIONS, F_DONATIONSRECEIVED,
                i_hystoryInput[F_TAG], i_hystoryInput[F_DATE], i_hystoryInput[F_ROLE], i_hystoryInput[F_EXPLEVEL],
                i_hystoryInput[F_TROPHIES], i_hystoryInput[F_CLANRANK], i_hystoryInput[F_DONATIONS], i_hystoryInput[F_DONATIONSRECEIVED])
    
    # execute request
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

    # for each member in clan
    for member in i_listeMembres:
        # update inclan field in DB (set to 1)
        reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(T_MEMBER, F_INCLAN, 1, F_TAG, member[F_TAG])
        cursor.execute(reqUpdate)

    # commit updates
    i_conn.commit()

    # build the request to get all members mark as not in clan in the DB
    reqFound = "SELECT {} FROM {} WHERE {} = {};".format(F_TAG, T_MEMBER, F_INCLAN, 1)

    # for each member in clan
    for row in cursor.execute(reqFound):
        # check if always into the clan in CSV file
        b_found = False
        for member in i_listeMembres:
            if row[0] == member[F_TAG]:
                b_found = True
                break
        # if member return in clan (in DB as not inclan and present in clan snapshot)     
        if b_found != True:
            reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(T_MEMBER, F_INCLAN, 0, F_TAG, row[0])
            cursor.execute(reqUpdate)

    # commit updates
    i_conn.commit()

############################
### updateClan(i_clan, i_conn):
### update clan information
### i :
###    i_clan : clan data : 
###    i_conn : connector : db connector
############################
def updateClan(i_clan, i_conn):
    # get the DB cursor
    cursor = i_conn.cursor()

    # build a request to find if an existing clan is recorded
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(T_CLAN, F_CLANNAME, i_clan[F_CLANNAME])
    
    # execute the request
    cursor.execute(reqFound)

    # if a clan is already in the DB
    if (cursor.fetchone() != None):
        # update inclan field in DB (set to 0)
        reqUpdate="UPDATE {} SET {} = '{}', {} = '{}', {} = {}, {} = {};".format(T_CLAN, 
                        F_CLANNAME, i_clan[F_CLANNAME], 
                        F_CLANDESCRIPTION, i_clan[F_CLANDESCRIPTION],
                        F_MEMBERCOUNT, i_clan[F_MEMBERCOUNT],
                        F_REQUIREDSCORE, i_clan[F_REQUIREDSCORE]
                        )
        cursor.execute(reqUpdate)
    # else, no clan data in the DB
    else:
        # build the add request
        reqAdd = "INSERT INTO {}({},{},{},{}) VALUES ('{}','{}',{},{});".format(T_CLAN,
                    F_CLANNAME, F_CLANDESCRIPTION, F_MEMBERCOUNT, F_REQUIREDSCORE,
                    i_clan[F_CLANNAME], i_clan[F_CLANDESCRIPTION], i_clan[F_MEMBERCOUNT], i_clan[F_REQUIREDSCORE] )
        # execute it
        cursor.execute(reqAdd)
    # commit updates
    i_conn.commit()


############################
### getConfig(i_iniFile):
### Read ini file
### i :
###     i_iniFile : string : configuration file
### r : boolean : true -> ini file read and correct / false
############################
def getConfig(i_iniFile):
    global dbFileName
    global apiUrl
    global clanId
    global playerId
    global fileType
    global apiToken
        
    config = ConfigParser.ConfigParser()
    config.read(i_iniFile)
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
        playerId = config.get('DEFAULT', 'playerId')
    except:
        return False;       
    try:
        fileType = config.get('DEFAULT', 'fileType')
    except:
        return False;
    try:
        apiToken = config.get('DEFAULT', 'apiToken')
    except:
        return False;
    return True

############################
### getJsonWithCache()
### download CSV file on CRAPI
### r : bolean : (true -> downloaded / false)
############################
def getJsonWithCache():
     # initialise list of dico
    r_listeMembers = []
    r_history = []
    r_warlog = []

    # get current date
    today = date.today()

    # create APIROYALE client
    client = clashroyale.RoyaleAPI(apiToken,cache_fp='cache.db',cache_expires=10)

    try:
        # get player data
        profile = client.get_player(playerId)
    except:
        print ('error profile ID')
    
    try:
        # get clan data from player ID
        clan = profile.get_clan()

        # get all clan members
        for member in clan.members:
            # create the member list
            lineMember={F_TAG:member[F_TAG],
                        F_NAME:removeSpecialChars(member[F_NAME])}

            # create the history
            lineHistory={F_TAG:member[F_TAG],
                        F_DATE:str(today),
                        F_ROLE:member[F_ROLE],
                        F_EXPLEVEL:int(member[F_EXPLEVEL]),
                        F_TROPHIES:int(member[F_TROPHIES]),
                        F_CLANRANK:int(member['rank']),
                        F_DONATIONS:int(member[F_DONATIONS]),
                        F_DONATIONSRECEIVED:int(member[F_DONATIONSRECEIVED])}
            r_listeMembers.append(lineMember)
            r_history.append(lineHistory)

        # get clan data
        r_clan ={F_CLANNAME:removeSpecialChars(clan[F_NAME]),
                 F_CLANDESCRIPTION:removeSpecialChars(clan[F_CLANDESCRIPTION]),
                 F_MEMBERCOUNT:int(clan[F_MEMBERCOUNT]),
                 F_REQUIREDSCORE:int(clan[F_REQUIREDSCORE])
                 }
    except:
        print ('error clan ID')

    try:
        # get war log for clan ID
        warList = client.get_clan_war_log(clanId)

        # for all past wars
        for war in warList:
            uncompleteWar = False

            # decode war date (unix timestamp)
            dateWar = datetime.utcfromtimestamp(war['createdDate']).strftime('%Y-%m-%d')

            # for all members of the war
            for member in war['participants']:

                # if war war uncompleted (prepataion < 3 or war < 1)
                if ((member[F_PREPAPLAYED] < 3) or (member[F_BATTLESPLAYED] == 0)):
                    # create a war log entry
                    lineWarLog={F_TAG:member[F_TAG],
                            F_DATEWAR:dateWar,
                            F_PREPAPLAYED:int(member[F_PREPAPLAYED]),
                            F_BATTLESPLAYED:int(member[F_BATTLESPLAYED])
                            }
                    uncompleteWar = True
                    r_warlog.append(lineWarLog)

            # if all battles were done by all members
            if uncompleteWar == False:
                # create a fake complete entry in order to log the clan participation to the war
                # this entry will have a tag set to 'none' et had to be filterd in sql requests
                lineWarLog={F_TAG:'none',
                            F_DATEWAR:dateWar,
                            F_PREPAPLAYED:3,
                            F_BATTLESPLAYED:1}
                r_warlog.append(lineWarLog)

    except:
        print ('error clan war')

    client.close()
    return r_clan, r_listeMembers, r_history, r_warlog

############################
### getCsvFile(i_csvFile)
### download CSV file on CRAPI
### i :
###     i_csvFile : string : csv file
### r : bolean : (true -> downloaded / false)
############################
def getCsvFile(i_csvFile):
    url = apiUrl+clanId+'/'+fileType

    if is_downloadable(url) == True:
    
        r = requests.get(url)

        with open(i_csvFile, 'wb') as f:  
            f.write(r.content)

        return True
    return False

############################
### parseCsvFile(i_csvFile):
### Read ini file
### i :
###     i_csvFile : string : csv file
### r : boolean : true -> ini file read and correct / false
############################
def parseCsvFile(i_csvFile):
    # initialise list of dico
    r_listeMembers = []
    r_history = []
    
    # get current date
    today = date.today()

    with open(i_csvFile, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # for each CSV row, build member list and history list
        for row in reader:
            lineMember={F_TAG:row[F_TAG],
                        F_NAME:removeSpecialChars(row[F_NAME])}

            lineHistory={F_TAG:row[F_TAG],
                        F_DATE:str(today),
                        F_ROLE:row[F_ROLE],
                        F_EXPLEVEL:int(row[F_EXPLEVEL]),
                        F_TROPHIES:int(row[F_TROPHIES]),
                        F_CLANRANK:int(row[F_CLANRANK]),
                        F_DONATIONS:int(row[F_DONATIONS]),
                        F_DONATIONSRECEIVED:int(row[F_DONATIONSRECEIVED])}
            r_listeMembers.append(lineMember)
            r_history.append(lineHistory)
    return r_listeMembers, r_history

############################
### main():
############################  
def main():
    # initialaze empty dictionary lists
    listeMembers = []
    history = []
    clanWar = []

    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    sys.stdout.write ('read ini file : ')

    # read config file
    if getConfig(currentPath+iniFile) == True:
        print ('done')
        # if in config file, CSV is requested
        if (fileType == 'csv'):
            sys.stdout.write ('download CSV file : ')
            # download CSV file from APIROYALE
            if getCsvFile(currentPath+inputCsvFile) == True:
                print ('done')
                sys.stdout.write ('parse CSV file : ')
                # parse the CSV file
                listeMembers, history = parseCsvFile(currentPath+inputCsvFile)
                 
                # remove temporary CSV file
                os.remove(currentPath+inputCsvFile)
            else:
                print ("failed")
        # if in config file, JSON is requested
        elif (fileType == 'json'):
            sys.stdout.write ('get JSON DATA : ')

            # get data from APIROYALE JSON
            clan, listeMembers, history, clanWar = getJsonWithCache()
            
        # if member list and history have to be recorded into DB
        if ((len(listeMembers) > 0) and (len(history) > 0)):
            print ('done')
            
            # initialize the DB
            print ('init DB : ')
            conn = initDb(currentPath+dbFileName)

            print ('           . Create new members')
            # create new members
            createMembers(listeMembers, conn)

            print ('           . Remove old members')
            # update member presence in clan
            memberInClan(listeMembers, conn)

            print ('           . Update history')
            # update members history
            addHistory(history,conn)

            # if a clan description exists
            if (len(clan) > 0):
               print ('           . Update clan') 
               # create or update the clan description
               updateClan(clan, conn)

            # if a clan war log exists
            if (len(clanWar) > 0):
               print ('           . Update clanWar')
               # update the clan war history
               addClanWarHistory(clanWar, conn) 

            print ('Close DB')
            # close the DB
            conn.close()
        else:
            print ("failed")
    else:
        print ("failed") 

#################################################
# ENTRY POINT
#################################################  
if __name__ == "__main__":  
    main()    
    
