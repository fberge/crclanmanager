import sqlite3
from datetime import date, datetime

import utils
import conf

############################
### DB FONCTIONS
############################

############################
### checkCreatetDb()
### Check DB existance and create it
### i :
###     i_dbFile : string : db file
### r : conn : db connector
############################
def checkCreatetDb(i_dbFile):
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
        if table[1] == conf.T_MEMBER:
            b_member = True
        if table[1] == conf.T_HISTORY:
            b_history = True
        if table[1] == conf.T_CLAN:
            b_clan = True
        if table[1] == conf.T_CLANWAR:
            b_clanwar = True

    # if T_MEMBER table doesn't exist, create it
    if b_member == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} text, {} int)".format(conf.T_MEMBER,
                                conf.F_TAG, conf.F_NAME, conf.F_PRES, conf.F_INCLAN)                                                     
        c.execute(reqCreate)

    # if T_HISTORY table doesn't  exist, create it
    if b_history == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} text, {} int, {} int,{} int,{} int,{} int)".format(conf.T_HISTORY,
                                conf.F_TAG, conf.F_DATE, conf.F_ROLE, conf.F_EXPLEVEL, conf.F_TROPHIES, 
                                conf.F_CLANRANK, conf.F_DONATIONS, conf.F_DONATIONSRECEIVED)
        c.execute(reqCreate)

    # if T_CLAN table doesn't  exist, create it
    if b_clan == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} int, {} int)".format(conf.T_CLAN,
                                conf.F_CLANNAME, conf.F_CLANDESCRIPTION, conf.F_MEMBERCOUNT, conf.F_REQUIREDSCORE)
        c.execute(reqCreate)

    # if T_CLANWAR table doesn't  exist, create it
    if b_clanwar == False:
        reqCreate = "CREATE TABLE {}({} text, {} text, {} int, {} int)".format(conf.T_CLANWAR,
                                conf.F_TAG, conf.F_DATEWAR, conf.F_PREPAPLAYED, conf.F_BATTLESPLAYED)
        c.execute(reqCreate)
    # commit updates   
    conn.commit()

    # return db    
    return conn

############################
### OpenDb(i_dbFile)
### Check DB existance and coherence
### i :
###     i_dbFile : string : db file
### r : conn : db connector
############################
def OpenDb(i_dbFile):
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
        if table[1] == conf.T_MEMBER:
            b_member = True
        if table[1] == conf.T_HISTORY:
            b_history = True
        if table[1] == conf.T_CLAN:
            b_clan = True
        if table[1] == conf.T_CLANWAR:
            b_clanwar = True

    if (b_member == False or b_history == False or b_clan == False or b_clanwar == False):
        return 0

    # return db    
    return conn

############################
### CloseDb(i_conn)
### Close DB
### i :
###     i_conn : db connector
############################
def CloseDb(i_conn):
    i_conn.close()

############################
### getGdcNbrOfFailsFromDb(i_conn):
### Return member list and tags, stored
### in DB
### i :
###     i_conn : db : db connector
### r : list : all names with number of fails
############################
def getGdcFailCountFromDb(i_conn):
    gdcFails = []
    # get DB cursor
    cursor = i_conn.cursor()

    # build a requestion to find if a date log is already done
    reqFound = "SELECT {}, {} FROM {} WHERE {} = {};".format(conf.F_TAG, conf.F_NAME, conf.T_MEMBER, conf.F_INCLAN, 1)
    
    # execute the request
    for row in cursor.execute(reqFound):
        # build a requestion to count
        reqCount = "SELECT COUNT(*) FROM {} WHERE {} = '{}';".format(conf.T_CLANWAR, conf.F_TAG, row[0])
        cursorCount = i_conn.cursor()
        cursorCount.execute(reqCount)
        result = cursorCount.fetchone()
        numberOfFail = result[0]
        if numberOfFail > 0:
            gdcFails.append([row[0], row[1],numberOfFail])

    return gdcFails

############################
### getPresFromDb(i_conn):
### Return member list and presentation, stored
### in DB
### i :
###     i_conn : db : db connector
### r : int : Number of members
###     list : all tags
###     list : all names
###     list : all presentations
############################
def getPresFromDb(i_conn):
    o_nbr = 0
    o_tags = []
    o_names = []
    o_presentations = []
    # get DB cursor
    cursor = i_conn.cursor()

    # build a requestion to find if a date log is already done
    reqFound = "SELECT * FROM {} WHERE {} = {};".format(conf.T_MEMBER, conf.F_INCLAN, 1)
    
    # execute the request
    for row in cursor.execute(reqFound):
        o_nbr = o_nbr + 1
        o_tags.append(row[0])
        o_names.append(row[1])
        o_presentations.append(row[2])

    return o_nbr, o_tags, o_names, o_presentations

############################
### getMemberListFromDb(i_conn):
### Return member list and tags, stored
### in DB
### i :
###     i_conn : db : db connector
### r : list : all tags
###     list : all names
############################
def getMemberListFromDb(i_conn):
    memberList = []
    # get DB cursor
    cursor = i_conn.cursor()

    # build a requestion to find if a date log is already done
    reqFound = "SELECT {}, {} FROM {} WHERE {} = {};".format(conf.F_TAG, conf.F_NAME, conf.T_MEMBER, conf.F_INCLAN, 1)
    
    # execute the request
    for row in cursor.execute(reqFound):
        memberList.append([row[0], row[1]])

    return memberList

############################
### getDatesFromDb(i_conn):
### Return min date, max date and all dates stored
### in DB
### i :
###     i_conn : db : db connector
### r : str : min date
###     str : max date
###     list : all dates
############################
def getDatesFromDb(i_conn):

    dateList = []
    datetime_object = datetime.strptime('2005-01-01', '%Y-%m-%d')
    maxDate = datetime.strptime('2005-01-01', '%Y-%m-%d')
    minDate = datetime.now()

    cursor = i_conn.cursor()
    # build a requestion to find if a date log is already done
    reqFound = "SELECT DISTINCT {} FROM {} ORDER BY {} ASC;".format(conf.F_DATE, conf.T_HISTORY, conf.F_DATE)
    
    # execute the request
    for row in cursor.execute(reqFound):
        datetime_object = datetime.strptime(row[0], '%Y-%m-%d')

        if datetime_object > maxDate:
            maxDate = datetime_object
        if datetime_object < minDate:
            minDate = datetime_object

        dateList.append(datetime_object.strftime('%Y-%m-%d'))

    return minDate.strftime('%Y-%m-%d'), maxDate.strftime('%Y-%m-%d'), dateList

############################
### getDonationReceptionsFromDb(i_conn, i_tag):
### Return donations and reception dor a given tag stored
### in DB
### i :
###     i_conn : db : db connector
###     i_tag : str : member tag
### r : str : donation list
###     list : reception list
############################
def getDonationReceptionsFromDb(i_conn, i_tag):
    donationList = []
    receptionList = []
    cursor = i_conn.cursor()
    # build a requestion to find if a date log is already done
    reqFound = "SELECT {}, {} FROM {} WHERE {} = '{}' ORDER BY {} ASC;".format(conf.F_DONATIONS, conf.F_DONATIONSRECEIVED, 
                conf.T_HISTORY, 
                conf.F_TAG, i_tag,
                conf.F_DATE)
    
    # execute the request
    for row in cursor.execute(reqFound):
        donationList.append(row[0])
        receptionList.append(row[1])

    return donationList, receptionList

############################
### getGdcFromDb(i_conn):
### Return GDC data stored
### in DB
### i :
###     i_conn : db : db connector
### r : int : nomber of records
###     list : list of dates
###     list : list of names
###     list : list of number of preparation wars
###     list : list of number of final wars
############################
def getGdcFromDb(i_conn):
    o_nbr = 0
    o_dates = []
    o_names = []
    o_prepaWar = []
    o_finalWar = []
    # get DB cursor
    cursor = i_conn.cursor()

    # build a requestion to find if a date log is already done
    reqFound = "SELECT {}, {}, {}, {} FROM {} INNER JOIN {} ON {}.{} = {}.{} ORDER BY {} DESC;".format(
        conf.F_DATEWAR, conf.F_NAME, conf.F_PREPAPLAYED, conf.F_BATTLESPLAYED,
        conf.T_CLANWAR, conf.T_MEMBER,conf.T_MEMBER,conf.F_TAG,conf.T_CLANWAR,conf.F_TAG,
        conf.F_DATEWAR)

        # execute the request
    for row in cursor.execute(reqFound):
        o_nbr = o_nbr + 1
        o_dates.append(row[0])
        o_names.append(row[1])
        o_prepaWar.append(row[2])
        o_finalWar.append(row[3])
    
    return o_nbr, o_dates, o_names, o_prepaWar, o_finalWar

def updatePresMember(i_conn, i_tag, i_desc):
    # get DB cursor
    cursor = i_conn.cursor()

    # build a requestion to find if a date log is already done
    reqUpdate = "UPDATE {} SET {}='{}' WHERE {} = '{}';".format(conf.T_MEMBER,
                                                                conf.F_PRES, i_desc,
                                                                conf.F_TAG,i_tag)

        # execute the request
    cursor.execute(reqUpdate)

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
    reqFound = "SELECT * FROM {} WHERE {} = '{}' and {} = '{}';".format(conf.T_CLANWAR, 
                                        conf.F_DATEWAR, i_clanWarLine[conf.F_DATEWAR],
                                        conf.F_TAG, i_clanWarLine[conf.F_TAG])

    #execute the request
    i_cursor.execute(reqFound)

    # if no entry is found for the given tag and date
    if (i_cursor.fetchone() == None):
        # build the add request to create new entry of chan war
        reqAdd = '''INSERT INTO {}({},{},{},{}) VALUES ('{}','{}',{},{});'''.format(conf.T_CLANWAR,
                    conf.F_TAG, conf.F_DATEWAR, conf.F_PREPAPLAYED, conf.F_BATTLESPLAYED,
                    i_clanWarLine[conf.F_TAG], i_clanWarLine[conf.F_DATEWAR], 
                    i_clanWarLine[conf.F_PREPAPLAYED], i_clanWarLine[conf.F_BATTLESPLAYED])
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
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(conf.T_HISTORY, conf.F_DATE, i_history[0][conf.F_DATE])
    
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
                VALUES ('{}','{}','{}',{},{},{},{},{});'''.format(conf.T_HISTORY,
                conf.F_TAG, conf.F_DATE, conf.F_ROLE, conf.F_EXPLEVEL, conf.F_TROPHIES, 
                conf.F_CLANRANK, conf.F_DONATIONS, conf.F_DONATIONSRECEIVED,
                i_hystoryInput[conf.F_TAG], i_hystoryInput[conf.F_DATE], 
                i_hystoryInput[conf.F_ROLE], i_hystoryInput[conf.F_EXPLEVEL],
                i_hystoryInput[conf.F_TROPHIES], i_hystoryInput[conf.F_CLANRANK], 
                i_hystoryInput[conf.F_DONATIONS], i_hystoryInput[conf.F_DONATIONSRECEIVED])
    
    # execute request
    i_cursor.execute(reqAdd)

############################
### updateHistoryInput(i_hystoryInput, i_cursor):
### add a single history input into db
### i :
###    i_hystoryInput : dictionary : single history
###    i_cursor : cursor : db cursor
############################
def updateHistoryInput(i_hystoryInput, i_cursor):

    # build a requestion to find if a date log is already done
    reqFound = "SELECT * FROM {} WHERE {} = '{}' AND {} = {};".format(conf.T_HISTORY, 
            conf.F_DATE, i_hystoryInput[conf.F_DATE],
            conf.F_TAG,  i_hystoryInput[conf.F_TAG])
    
    # execute the request
    cursor.execute(reqFound)

    # if no entry is found for the given date
    if (cursor.fetchone() == None):
        # create DB request to add an entry
        requestHist = '''INSERT INTO {}({},{},{},{},{},{},{},{})
                    VALUES ('{}','{}','{}',{},{},{},{},{});'''.format(conf.T_HISTORY,
                    conf.F_TAG, conf.F_DATE, conf.F_ROLE, conf.F_EXPLEVEL, conf.F_TROPHIES, 
                    conf.F_CLANRANK, conf.F_DONATIONS, conf.F_DONATIONSRECEIVED,
                    i_hystoryInput[conf.F_TAG], i_hystoryInput[conf.F_DATE], 
                    i_hystoryInput[conf.F_ROLE], i_hystoryInput[conf.F_EXPLEVEL],
                    i_hystoryInput[conf.F_TROPHIES], i_hystoryInput[conf.F_CLANRANK], 
                    i_hystoryInput[conf.F_DONATIONS], i_hystoryInput[conf.F_DONATIONSRECEIVED])
    else:
        # create DB request to update an entry
        requestHist = '''INSERT INTO {}({},{},{},{},{},{},{},{})
                    VALUES ('{}','{}','{}',{},{},{},{},{});'''.format(conf.T_HISTORY,
                    conf.F_TAG, conf.F_DATE, conf.F_ROLE, conf.F_EXPLEVEL, conf.F_TROPHIES, 
                    conf.F_CLANRANK, conf.F_DONATIONS, conf.F_DONATIONSRECEIVED,
                    i_hystoryInput[conf.F_TAG], i_hystoryInput[conf.F_DATE], 
                    i_hystoryInput[conf.F_ROLE], i_hystoryInput[conf.F_EXPLEVEL],
                    i_hystoryInput[conf.F_TROPHIES], i_hystoryInput[conf.F_CLANRANK], 
                    i_hystoryInput[conf.F_DONATIONS], i_hystoryInput[conf.F_DONATIONSRECEIVED])
    # execute request
    i_cursor.execute(requestHist)

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
    reqFound = "SELECT * FROM {} WHERE {} = '{}'".format(conf.T_MEMBER, conf.F_TAG, i_member[conf.F_TAG])

    # execute the request
    i_cursor.execute(reqFound)

    # if current member is not in the DB, add him
    if (i_cursor.fetchone() == None):
        # build the add request
        reqAdd = '''INSERT INTO {}({},{},{},{}) VALUES ('{}','{}','',1);'''.format(conf.T_MEMBER,
                    conf.F_TAG, conf.F_NAME, conf.F_PRES, conf.F_INCLAN,
                    i_member[conf.F_TAG], i_member[conf.F_NAME])
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
        reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(conf.T_MEMBER, conf.F_INCLAN, 1, conf.F_TAG, member[conf.F_TAG])
        cursor.execute(reqUpdate)

    # commit updates
    i_conn.commit()

    # build the request to get all members mark as not in clan in the DB
    reqFound = "SELECT {} FROM {} WHERE {} = {};".format(conf.F_TAG, conf.T_MEMBER, conf.F_INCLAN, 1)

    # for each member in clan
    for row in cursor.execute(reqFound):
        # check if always into the clan in CSV file
        b_found = False
        for member in i_listeMembres:
            if row[0] == member[conf.F_TAG]:
                b_found = True
                break
        # if member return in clan (in DB as not inclan and present in clan snapshot)     
        if b_found != True:
            reqUpdate="UPDATE {} SET {} = {} WHERE {} = '{}';".format(conf.T_MEMBER, conf.F_INCLAN, 0, conf.F_TAG, row[0])
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
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(conf.T_CLAN, conf.F_CLANNAME, i_clan[conf.F_CLANNAME])
    
    # execute the request
    cursor.execute(reqFound)

    # if a clan is already in the DB
    if (cursor.fetchone() != None):
        # update inclan field in DB (set to 0)
        reqUpdate="UPDATE {} SET {} = '{}', {} = '{}', {} = {}, {} = {};".format(conf.T_CLAN, 
                        conf.F_CLANNAME, i_clan[conf.F_CLANNAME], 
                        conf.F_CLANDESCRIPTION, i_clan[conf.F_CLANDESCRIPTION],
                        conf.F_MEMBERCOUNT, i_clan[conf.F_MEMBERCOUNT],
                        conf.F_REQUIREDSCORE, i_clan[conf.F_REQUIREDSCORE]
                        )
        cursor.execute(reqUpdate)
    # else, no clan data in the DB
    else:
        # build the add request
        reqAdd = "INSERT INTO {}({},{},{},{}) VALUES ('{}','{}',{},{});".format(conf.T_CLAN,
                    conf.F_CLANNAME, conf.F_CLANDESCRIPTION, conf.F_MEMBERCOUNT, conf.F_REQUIREDSCORE,
                    i_clan[conf.F_CLANNAME], i_clan[conf.F_CLANDESCRIPTION], i_clan[conf.F_MEMBERCOUNT], i_clan[conf.F_REQUIREDSCORE] )
        # execute it
        cursor.execute(reqAdd)
    # commit updates
    i_conn.commit()

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



