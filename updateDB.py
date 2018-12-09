import csv
import re
from datetime import date, datetime
import requests
import asyncio
import os
import sys

import utils
import conf
import database as db
import clanjson as cr


######################################################################################
## FUNCTIONS
######################################################################################




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

    # read config file
    dbFileName, apiUrl, clanId, playerId, fileType, apiToken = conf.getConfig()

    sys.stdout.write ('get JSON DATA : ')

    # get data from APIROYALE JSON
    clan, listeMembers, history, clanWar = cr.getJsonDataForDb(apiToken, playerId, clanId)
        
    # if member list and history have to be recorded into DB
    if ((len(listeMembers) > 0) and (len(history) > 0)):
        print ('done')
        
        # initialize the DB
        print ('init DB : ')
        conn = db.checkCreatetDb(currentPath+dbFileName)

        print ('           . Create new members')
        # create new members
        db.createMembers(listeMembers, conn)

        print ('           . Remove old members')
        # update member presence in clan
        db.memberInClan(listeMembers, conn)

        print ('           . Update history')
        # update members history
        db.addHistory(history,conn)

        # if a clan description exists
        if (len(clan) > 0):
            print ('           . Update clan') 
            # create or update the clan description
            db.updateClan(clan, conn)

        # if a clan war log exists
        if (len(clanWar) > 0):
            print ('           . Update clanWar')
            # update the clan war history
            db.addClanWarHistory(clanWar, conn) 

        print ('Close DB')
        # close the DB
        db.CloseDb(conn)

#################################################
# ENTRY POINT
#################################################  
if __name__ == "__main__":  
    main()    
    
