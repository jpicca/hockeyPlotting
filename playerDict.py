## This file serves only to create a dictionary of players

import requests

# Stars are 25
teamID = 25

url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamID}/roster'
response = requests.get(url).json()

playerDict = {}

for player in response['roster']:

    #print(player['person'])
    lastName = player['person']['fullName'].split(" ")[-1]
    playerDict[lastName] = player['person']['id']



