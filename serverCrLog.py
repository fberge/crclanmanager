################################
### IMPORTS
import dash
import dash_core_components as dcc
import dash_html_components as html
import configparser as ConfigParser
import clashroyale
import sqlite3
import re
import sys
import os
from datetime import date, datetime
from dash.dependencies import Input, Output


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
### TOOLS FONCTIONS
############################

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
### INI FILE FONCTIONS
############################

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
### JSON FONCTIONS
############################

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
            if (int(member[F_DONATIONS]) < K_CLANLIMITE):
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

############################
### DB FONCTIONS
############################

############################
### OpenDb()
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
        if table[1] == T_MEMBER:
            b_member = True
        if table[1] == T_HISTORY:
            b_history = True
        if table[1] == T_CLAN:
            b_clan = True
        if table[1] == T_CLANWAR:
            b_clanwar = True

    if (b_member == False or b_history == False or b_clan == False or b_clanwar == False):
        return 0

    # return db    
    return conn

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
    reqFound = "SELECT * FROM {} WHERE {} = {};".format(T_MEMBER, F_INCLAN, 1)
    
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
    reqFound = "SELECT {}, {} FROM {} WHERE {} = {};".format(F_TAG, F_NAME, T_MEMBER, F_INCLAN, 1)
    
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
    reqFound = "SELECT DISTINCT {} FROM {} ORDER BY {} ASC;".format(F_DATE, T_HISTORY, F_DATE)
    
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
    reqFound = "SELECT {}, {} FROM {} WHERE {} = '{}' ORDER BY {} ASC;".format(F_DONATIONS, F_DONATIONSRECEIVED, 
                T_HISTORY, 
                F_TAG, i_tag,
                F_DATE)
    
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
        F_DATEWAR, F_NAME, F_PREPAPLAYED, F_BATTLESPLAYED,
        T_CLANWAR, T_MEMBER,T_MEMBER,F_TAG,T_CLANWAR,F_TAG,
        F_DATEWAR)

        # execute the request
    for row in cursor.execute(reqFound):
        o_nbr = o_nbr + 1
        o_dates.append(row[0])
        o_names.append(row[1])
        o_prepaWar.append(row[2])
        o_finalWar.append(row[3])
    
    return o_nbr, o_dates, o_names, o_prepaWar, o_finalWar

############################
### IHM FONCTIONS
############################

############################
### buildHtmlDiv():
### Build and return HTML template
############################
def buildHtmlDiv():

    return html.Div([
        dcc.Tabs(id="tabs", children=[
            dcc.Tab(label='Stats instantanées', children=[
                tab_general()
            ]),
            dcc.Tab(label='Historique dons', children=[
                tab_dons()
            ]),
            dcc.Tab(label='Historique GDC', children=[
                tab_gdc()
            ]),
             dcc.Tab(label='Présentations membres', children=[
                tab_presentations()
            ]),
        ])
    ])

############################
### tab_dons():
### Build and return HTML donation TAB
############################
def tab_dons():

    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    conn = OpenDb(currentPath+dbFileName)
    memberList = getMemberListFromDb(conn)
    # close the DB
    conn.close()

    return html.Div(children=[
        html.Div([
            dcc.Dropdown(
                    id='member-filter',
                    options=[{'label': i[1], 'value': i[0]} for i in memberList],
                    value='Fertility rate, total (births per woman)'
                )
            ], style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='donation-graphic'),
    ])

############################
### tab_gdc():
### Build and return HTML GDC TAB
############################
def tab_gdc():
    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    conn = OpenDb(currentPath+dbFileName)
    nbr, dates, names, prepaWar, finalWar = getGdcFromDb(conn)
    # close the DB
    conn.close()

    return html.Div(children=[
        html.H4(children='Historique des GDC'),
        # Body
        html.Table(
            [
                html.Tr( [html.Th("Date"), html.Th("Nom"), html.Th("Préparation"), html.Th("Combat final")] )
            ] +
            [
                html.Tr([
                    html.Td(dates[i]), html.Td(names[i]), html.Td(prepaWar[i]), html.Td(finalWar[i])
                ])  for i in range(nbr)
            ]
        )
    ])

############################
### tab_presentations():
### Build and return HTML presentation TAB
############################
def tab_presentations():
    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    conn = OpenDb(currentPath+dbFileName)
    Nbr, Tags, Names, Presentations = getPresFromDb(conn)
    # close the DB
    conn.close()

    return html.Div(children=[
        html.H4(children='Présentation des membres'),
        # Body
        html.Table(
            [
                html.Tr( [html.Th("Tag"), html.Th("Nom"), html.Th("Pres")] )
            ] +
            [
                html.Tr([
                    html.Td(Tags[i]), html.Td(Names[i]), html.Td(Presentations[i])
                ])  for i in range(Nbr)
            ]
        )
    ])
############################
### tab_general():
### Build and return HTML first TAB : 
### live repport of donations and GDC
############################
def tab_general():
    clan, history, clanWar, dateWar = getJsonWithCache()
    currentDate = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    return html.Div(children=[
        html.Title('Clan '+clan[F_NAME]),
        html.H1(children=u'Statistiques du clan "'+clan[F_NAME]+'"'),
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
### INITIALIZE WEB SERVER
############################

# get the current path (unix)
currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

# read config file
if getConfig(currentPath+iniFile) == True:
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = buildHtmlDiv
    app.title = 'Statistiques de clan'

############################
### CALLBACK FONCTIONS
############################


@app.callback(
    dash.dependencies.Output('donation-graphic', 'figure'),
    [dash.dependencies.Input('member-filter', 'value')])
def update_graph(donationMemberTag):
    # get the current path (unix)
    currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

    conn = OpenDb(currentPath+dbFileName)
    donationList, receptionList = getDonationReceptionsFromDb(conn, donationMemberTag)
    minDate, maxDate, dateList = getDatesFromDb(conn)
    # close the DB
    conn.close()

    return {
            'data': [
                    {'x': dateList, 'y': receptionList, 'type': 'lines+markers', 'name': u'Dons reçus'},
                    {'x': dateList, 'y': donationList, 'type': 'lines+markers', 'name': u'Dons émis'},
                ],
            'layout': {
                    'title': u'Rapport dons reçus / dons émis'
                }
        }

############################
### MAIN FONCTIONS
############################
if __name__ == '__main__':

        # Start server
        app.run_server(host='0.0.0.0', debug=True)

