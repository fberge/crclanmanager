import csv
import re
from datetime import date
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
### i :
###     i_dbFile : string : db file
### r : conn : db connector
############################
def initDb(i_dbFile):
    # init var
    b_history = False
    b_member = False

    # connect db file
    conn = sqlite3.connect(i_dbFile)
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
### getJson()
### download CSV file on CRAPI
### r : bolean : (true -> downloaded / false)
############################
async def getJson():
     # initialise list of dico
    r_listeMembers = []
    r_history = []
    
    # get current date
    today = date.today()

    # Basic functionality
    client = clashroyale.RoyaleAPI(apiToken, is_async=True)

    try:
        profile = await client.get_player(playerId)
        #print(repr(profile))
        #print(profile.name)
    except:
        print ('error profile ID')

    try:
        await asyncio.sleep(1)
        clan = await profile.get_clan()
        #print(clan)
        #print(clan.member_count) 
        for member in clan.members:
            lineMember={F_TAG:member['tag'],
                        F_NAME:re.sub("[^a-zA-Z0-9_@ ]", "", member['name'])}

            lineHistory={F_TAG:member['tag'],
                        F_DATE:str(today),
                        F_ROLE:member['role'],
                        F_EXPLEVEL:int(member['expLevel']),
                        F_TROPHIES:int(member['trophies']),
                        F_CLANRANK:int(member['rank']),
                        F_DONATIONS:int(member['donations']),
                        F_DONATIONSRECEIVED:int(member['donationsReceived'])}
            r_listeMembers.append(lineMember)
            r_history.append(lineHistory)
    except:
        print ('error clan ID')

    client.close()
    return r_listeMembers, r_history

############################
### getJson()
### download CSV file on CRAPI
### r : bolean : (true -> downloaded / false)
############################
def getJsonWithCache():
     # initialise list of dico
    r_listeMembers = []
    r_history = []
    
    # get current date
    today = date.today()

    # Basic functionality
    client = clashroyale.RoyaleAPI(apiToken,cache_fp='cache.db',cache_expires=10)

    try:
        profile = client.get_player(playerId)
        #print(repr(profile))
        #print(profile.name)
    except:
        print ('error profile ID')
    
    try:
        clan = profile.get_clan()
        for member in clan.members:
            lineMember={F_TAG:member['tag'],
                        F_NAME:re.sub("[^a-zA-Z0-9_@ ]", "", member['name'])}

            lineHistory={F_TAG:member['tag'],
                        F_DATE:str(today),
                        F_ROLE:member['role'],
                        F_EXPLEVEL:int(member['expLevel']),
                        F_TROPHIES:int(member['trophies']),
                        F_CLANRANK:int(member['rank']),
                        F_DONATIONS:int(member['donations']),
                        F_DONATIONSRECEIVED:int(member['donationsReceived'])}
            r_listeMembers.append(lineMember)
            r_history.append(lineHistory)
    except:
        print ('error clan ID')

    try:
        warList = client.get_clan_war_log(clanId)
        print (warList[0]['participants'][0]['tag'])
        print (warList[0]['participants'][0]['name'])
        print (warList[0]['participants'][0]['collectionDayBattlesPlayed'])
        print (warList[0]['participants'][0]['battlesPlayed'])

    except:
        print ('error clan war')

    client.close()
    return r_listeMembers, r_history

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
                        F_NAME:re.sub("[^a-zA-Z0-9_@ ]", "", row[F_NAME])}

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
    listeMembers = []
    history = []

    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    sys.stdout.write ('read ini file : ')
    if getConfig(currentPath+iniFile) == True:
        print ('done')
        if (fileType == 'csv'):
            sys.stdout.write ('download CSV file : ')
            if getCsvFile(currentPath+inputCsvFile) == True:
                print ('done')
                sys.stdout.write ('parse CSV file : ')
                listeMembers, history = parseCsvFile(currentPath+inputCsvFile)
                 
                os.remove(currentPath+inputCsvFile)
            else:
                print ("failed")
        elif (fileType == 'json'):
            sys.stdout.write ('get JSON DATA : ')

            listeMembers, history = getJsonWithCache()
            #loop = asyncio.get_event_loop()
            #listeMembers, history = loop.run_until_complete(getJson())
            
        if ((len(listeMembers) > 0) and (len(history) > 0)):
            print ('done')
            
            #print (history)
            print ('init DB : ')
            # DEBUG conn = initDb(currentPath+dbFileName)

            print ('           . Create new members')
            # DEBUG createMembers(listeMembers, conn)
            print ('           . Remove old members')
            # DEBUG memberInClan(listeMembers, conn)
            print ('           . Update history')
            # DEBUG addHistory(history,conn)

            print ('Close DB')
            # DEBUG conn.close()
        else:
            print ("failed")
    else:
        print ("failed") 

#################################################
# ENTRY POINT
#################################################  
if __name__ == "__main__":  
    main()    
    
