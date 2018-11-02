# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import configparser as ConfigParser
import clashroyale
import re
import sys
import os
from datetime import date, datetime

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

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

F_CLANDESCRIPTION = 'description'
F_MEMBERCOUNT = 'memberCount'
F_REQUIREDSCORE = 'requiredScore'

############################
### removeSpecialChars(i_data):
### remove special chars
### i :
###     i_data : string
### r : string : string without special chars
############################
def removeSpecialChars(i_data):
    return re.sub("[^a-zA-Z0-9_@ ]", "", i_data)

############################
### buildHtmlDiv():
### Build and return HTML template
############################
def buildHtmlDiv():
    clan, history, clanWar, dateWar = getJsonWithCache()
    currentDate = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    return html.Div(children=[
        html.Title('Clan '+clan[F_NAME]),
        html.H1(children=u'Statistique du clan "'+clan[F_NAME]+'"'),
        html.Div('Last update: ' + currentDate),
        

        dcc.Graph(
            id='graph-dons',
            figure={
                'data': [
                    {'x': history[0], 'y': history[1], 'type': 'bar', 'name': u'Dons reçus'},
                    {'x': history[0], 'y': history[2], 'type': 'bar', 'name': u'Dons émis'},
                ],
                'layout': {
                    'title': u'Rapport dons reçus / dons émis'
                }
            }
        ),
        dcc.Graph(
            id='graph-war',
            figure={
                'data': [
                    {'x': clanWar[0], 'y': clanWar[1], 'type': 'bar', 'name': u'Préparations'},
                    {'x': clanWar[0], 'y': clanWar[2], 'type': 'bar', 'name': u'Guerre finale'},
                ],
                'layout': {
                    'title': u'Rapport de guerre du ' + dateWar
                }
            }
        )
    ])

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
### get JSON  on CRAPI
### r : bolean : (true -> downloaded / false)
############################
def getJsonWithCache():
     # initialise list of dico
    r_history = []
    r_warlog = []

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

        noms=[]
        donsRecus=[]
        donsEmis=[]
        # get all clan members
        for member in clan.members:
            noms.append(removeSpecialChars(member[F_NAME]))
            donsRecus.append(int(member[F_DONATIONSRECEIVED]))
            donsEmis.append(int(member[F_DONATIONS]))

        r_history=[noms, donsRecus, donsEmis]
        # get clan data
        r_clan ={F_NAME:removeSpecialChars(clan[F_NAME]),
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
        war = warList[0]

        # decode war date (unix timestamp)
        r_dateWar = datetime.utcfromtimestamp(war['createdDate']).strftime('%Y-%m-%d')

        participant=[]
        prepaWar=[]
        finalWar=[]
        # for all members of the war
        for member in war['participants']:

            # if war war uncompleted (prepataion < 3 or war < 1)
            if ((member[F_PREPAPLAYED] < 3) or (member[F_BATTLESPLAYED] == 0)):
                participant.append(member[F_NAME])
                prepaWar.append(int(member[F_PREPAPLAYED]))
                finalWar.append(int(member[F_BATTLESPLAYED]))

        r_warlog=[participant, prepaWar, finalWar]


    except:
        print ('error clan war')

    client.close()
    return r_clan, r_history, r_warlog, r_dateWar

if __name__ == '__main__':
    history = []
    clanWar = []

    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'
   
    sys.stdout.write ('read ini file : ')

    # read config file
    if getConfig(currentPath+iniFile) == True:
        print ('done')
        clan, history, clanWar, dateWar = getJsonWithCache()

        app.layout = buildHtmlDiv
        app.run_server(debug=True)