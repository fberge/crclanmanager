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
def getJsonWithCache(i_apiToken, i_playerId, i_clanId):
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