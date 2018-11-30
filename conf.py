
import configparser as ConfigParser
import os

################################
### DB FIELD NAMES
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


###########################
### CONFIGURATION FILE
iniFile = "conf.ini"

K_CLANLIMITE = 300

############################
### INI FILE FONCTIONS
############################

############################
### getConfig(i_iniFile):
### Read ini file
### i :
###     i_iniFile : string : configuration file
### r : boolean : true -> ini file read and correct / false
############################
def getConfig():    

    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    config = ConfigParser.ConfigParser()
    config.read(currentPath+iniFile)
    try:
        dbFileName = config.get('DEFAULT', 'dbFileName')
        apiUrl = config.get('DEFAULT', 'apiUrl')
        clanId = config.get('DEFAULT', 'clanId')
        playerId = config.get('DEFAULT', 'playerId')
        fileType = config.get('DEFAULT', 'fileType')
        apiToken = config.get('DEFAULT', 'apiToken')
    except:
        return False;
    return dbFileName, apiUrl, clanId, playerId, fileType, apiToken 