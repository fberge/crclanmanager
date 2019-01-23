############################
### (c) Frédéric BERGE 2018
### frederic.berge@gmail.com
############################

################################
### IMPORTS
import utils
import conf
import database as db
import os

global dbFileName

# read config file
dbFileName, apiUrl, clanId, playerId, fileType, apiToken = conf.getConfig()

currentPath = os.path.dirname(os.path.abspath(__file__))+'/'

# get DATA from DB
conn = db.OpenDb(currentPath+dbFileName)
Nbr, Tags, Names, Presentations = db.getPresFromDb(conn)

memberList = []
for i in range (Nbr):
    memberList.append([Tags[i],Names[i],Presentations[i]])

for member in memberList:
    if len(member[2]) < 1:
        member[2] = input('saisir presentation du membre '+ member[1] + ' : ')
        print ('presentation du membre '+ member[1]+' : '+ member[2])
        db.updatePresMember(conn, member[0], member[2])

db.CloseDb(conn)