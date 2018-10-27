import csv
import re
import datetime
import sqlite3

dbFileName = 'clanVieuxDeck.db'
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

T_HISTORY = 'hist'
T_MEMBER = 'membre'


def viewMembers(i_conn):
    cursor = i_conn.cursor()
    
    reqFound = "SELECT {} FROM {};".format(F_TAG, T_MEMBER)
    for row in cursor.execute(reqFound):
        viewMember(row[0], i_conn)
        viewHistory(row[0], i_conn)


def viewMember(i_tag, i_conn):
    cursor = i_conn.cursor()
    
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(T_MEMBER, F_TAG, i_tag)
    #print reqFound
    for row in cursor.execute(reqFound):
        print row        

def viewHistory(i_tag, i_conn):
    cursor = i_conn.cursor()
    
    reqFound = "SELECT * FROM {} WHERE {} = '{}';".format(T_HISTORY, F_TAG, i_tag)
    #print reqFound
    for row in cursor.execute(reqFound):
        print row    

def main():           
    conn = sqlite3.connect(dbFileName)
 
    viewMembers(conn)

    conn.close()
        
if __name__ == "__main__":    
    main()    
    
