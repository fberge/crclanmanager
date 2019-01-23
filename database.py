############################
### (c) Frédéric BERGE 2018
### frederic.berge@gmail.com
############################

################################
### IMPORTS
import sqlite3
from datetime import date, datetime

import utils
import conf

############################
### DB FONCTIONS
############################

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