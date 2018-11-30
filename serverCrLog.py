################################
### IMPORTS
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import sys
import os
from datetime import date, datetime
from operator import itemgetter

import utils
import conf
import database as db
import clanjson as cr


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

    # Get DATA from DB
    conn = db.OpenDb(currentPath+dbFileName)
    memberList = db.getMemberListFromDb(conn)
    db.CloseDb(conn)

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

    # get DATA from DB
    conn = db.OpenDb(currentPath+dbFileName)
    nbr, dates, names, prepaWar, finalWar = db.getGdcFromDb(conn)
    gdcFailList = db.getGdcFailCountFromDb(conn)
    gdcFailList = sorted(gdcFailList, key=itemgetter(2), reverse = True)
    db.CloseDb(conn)

    listNames = []
    listFailCount = []

    for ligne in gdcFailList:
        listNames.append(ligne[1])
        listFailCount.append(ligne[2])

    return html.Div(children=[
        html.H4(children='Historique des GDC'),
        # Body
        dcc.Graph(
            id='graph-gdc',
            figure={
                'data': [
                    {'x': listNames, 'y': listFailCount, 'type': 'bar', 'name': u'Dons reçus'},
                ],
                'layout': {
                    'title': u'Nombre de fails'
                }
            }
        ),
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

    # get DATA from DB
    conn = db.OpenDb(currentPath+dbFileName)
    Nbr, Tags, Names, Presentations = db.getPresFromDb(conn)
    db.CloseDb(conn)

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
    clan, history, clanWar, dateWar = cr.getJsonWithCache(apiToken, playerId, clanId)
    currentDate = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    return html.Div(children=[
        html.Title('Clan '+clan[conf.F_NAME]),
        html.H1(children=u'Statistiques du clan "'+clan[conf.F_NAME]+'"'),
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
global dbFileName
global apiUrl
global clanId
global playerId
global fileType
global apiToken

# read config file
dbFileName, apiUrl, clanId, playerId, fileType, apiToken = conf.getConfig()

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

    # get DATA from DB
    conn = db.OpenDb(currentPath+dbFileName)
    donationList, receptionList = db.getDonationReceptionsFromDb(conn, donationMemberTag)
    minDate, maxDate, dateList = db.getDatesFromDb(conn)
    db.CloseDb(conn)

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

