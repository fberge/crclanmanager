import clashroyale
from datetime import date, datetime

import utils
import conf

############################
### JSON FONCTIONS
############################

############################
### getJsonWithCache()
### get JSON  on CRAPI
### r : bolean : (true -> downloaded / false)
############################
def getJsonLiveData(i_apiToken, i_playerId, i_clanId):
     # initialise list of dico
    r_history = []
    r_warlog = []

    # create APIROYALE client
    client = clashroyale.RoyaleAPI(i_apiToken,cache_fp='cache.db',cache_expires=10)

    try:
        # get player data
        profile = client.get_player(i_playerId)
    except:
        print ('error profile ID')
    
    try:
        # get clan data from player ID
        clan = profile.get_clan()

        # get all clan members
        for member in clan.members:
            #if (int(member[conf.F_DONATIONS]) < conf.K_CLANLIMITE):
            r_history.append([
                            utils.removeSpecialChars(member[conf.F_NAME]),
                            int(member[conf.F_DONATIONSRECEIVED]),
                            int(member[conf.F_DONATIONS])
                            ])
        # get clan data
        r_clan ={conf.F_NAME:utils.removeSpecialChars(clan[conf.F_NAME]),
                 conf.F_CLANDESCRIPTION:utils.removeSpecialChars(clan[conf.F_CLANDESCRIPTION]),
                 conf.F_MEMBERCOUNT:int(clan[conf.F_MEMBERCOUNT]),
                 conf.F_REQUIREDSCORE:int(clan[conf.F_REQUIREDSCORE])
                 }
    except:
        print ('error clan ID')

    try:
        # get war log for clan ID
        warList = client.get_clan_war_log(i_clanId)

        # for all past wars
        war = warList[0]

        # decode war date (unix timestamp)
        r_dateWar = datetime.utcfromtimestamp(war['createdDate']).strftime('%Y-%m-%d')

        participant=[]
        prepaWar=[]
        finalWar=[]
        # for all members of the war
        for member in war['participants']:

            # if war war uncompleted (prepataion < 3 or war < 1)
            if ((member[conf.F_PREPAPLAYED] < 3) or (member[conf.F_BATTLESPLAYED] == 0)):
                participant.append(member[conf.F_NAME])
                prepaWar.append(int(member[conf.F_PREPAPLAYED]))
                finalWar.append(int(member[conf.F_BATTLESPLAYED]))

        r_warlog=[participant, prepaWar, finalWar]


    except:
        print ('error clan war')

    client.close()
    return r_clan, r_history, r_warlog, r_dateWar

############################
### getJsonDataForDb()
### get JSON data to be stored in DB
### r : bolean : (true -> downloaded / false)
############################
def getJsonDataForDb(i_apiToken, i_playerId, i_clanId):
     # initialise list of dico
    r_listeMembers = []
    r_history = []
    r_warlog = []

    # get current date
    today = date.today()

    # create APIROYALE client
    client = clashroyale.RoyaleAPI(i_apiToken,cache_fp='cache.db',cache_expires=10)

    try:
        # get player data
        profile = client.get_player(i_playerId)
    except:
        print ('error profile ID')
    
    try:
        # get clan data from player ID
        clan = profile.get_clan()

        # get all clan members
        for member in clan.members:
            # create the member list
            lineMember={conf.F_TAG:member[conf.F_TAG],
                        conf.F_NAME:utils.removeSpecialChars(member[conf.F_NAME])}

            # create the history
            lineHistory={conf.F_TAG:member[conf.F_TAG],
                        conf.F_DATE:str(today),
                        conf.F_ROLE:member[conf.F_ROLE],
                        conf.F_EXPLEVEL:int(member[conf.F_EXPLEVEL]),
                        conf.F_TROPHIES:int(member[conf.F_TROPHIES]),
                        conf.F_CLANRANK:int(member['rank']),
                        conf.F_DONATIONS:int(member[conf.F_DONATIONS]),
                        conf.F_DONATIONSRECEIVED:int(member[conf.F_DONATIONSRECEIVED])}
            r_listeMembers.append(lineMember)
            r_history.append(lineHistory)

        # get clan data
        r_clan ={conf.F_CLANNAME:utils.removeSpecialChars(clan[conf.F_NAME]),
                 conf.F_CLANDESCRIPTION:utils.removeSpecialChars(clan[conf.F_CLANDESCRIPTION]),
                 conf.F_MEMBERCOUNT:int(clan[conf.F_MEMBERCOUNT]),
                 conf.F_REQUIREDSCORE:int(clan[conf.F_REQUIREDSCORE])
                 }
    except:
        print ('error clan ID')

    try:
        # get war log for clan ID
        warList = client.get_clan_war_log(i_clanId)

        # for all past wars
        for war in warList:
            uncompleteWar = False

            # decode war date (unix timestamp)
            dateWar = datetime.utcfromtimestamp(war['createdDate']).strftime('%Y-%m-%d')

            # for all members of the war
            for member in war['participants']:

                # if war war uncompleted (prepataion < 3 or war < 1)
                if ((member[conf.F_PREPAPLAYED] < 3) or (member[conf.F_BATTLESPLAYED] == 0)):
                    # create a war log entry
                    lineWarLog={conf.F_TAG:member[conf.F_TAG],
                            conf.F_DATEWAR:dateWar,
                            conf.F_PREPAPLAYED:int(member[conf.F_PREPAPLAYED]),
                            conf.F_BATTLESPLAYED:int(member[conf.F_BATTLESPLAYED])
                            }
                    uncompleteWar = True
                    r_warlog.append(lineWarLog)

            # if all battles were done by all members
            if uncompleteWar == False:
                # create a fake complete entry in order to log the clan participation to the war
                # this entry will have a tag set to 'none' et had to be filterd in sql requests
                lineWarLog={conf.F_TAG:'none',
                            conf.F_DATEWAR:dateWar,
                            conf.F_PREPAPLAYED:3,
                            conf.F_BATTLESPLAYED:1}
                r_warlog.append(lineWarLog)

    except:
        print ('error clan war')

    client.close()
    return r_clan, r_listeMembers, r_history, r_warlog
