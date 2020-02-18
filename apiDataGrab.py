import requests
import pandas as pd
from datetime import datetime

def gameOverview(gameResponse):
    if (gameResponse.status_code == 200):

        # Get various json data if the game response is valid
        playList = gameResponse.json()['liveData']['plays']['allPlays']
        boxScore = gameResponse.json()['liveData']['boxscore']
        metaData = gameResponse.json()['gameData']
        periods = gameResponse.json()['liveData']['linescore']['periods']

    # Append game date/time
    gameDates.append(metaData['datetime']['dateTime'])

    # Get data from both teams
    # In this for loop, 'team' is either 'home' or 'away'
    for team in metaData['teams']:

        # teamID currently set to 25 for stars
        if (metaData['teams'][team]['id'] == teamID):

            # Set True/False if the Stars are home
            homeAway.append(team)

            starsLoc = team

        else:

            opposingTeam.append(metaData['teams'][team]['id'])

            opposingLoc = team
    
    # Check if the game went to a shootout. If so, we have to add a goal to the winner
    if (playList[-1]['about']['periodType'] == 'SHOOTOUT'):     
        starsSOGoals = gameResponse.json()['liveData']['linescore']['shootoutInfo'][starsLoc]['scores']
        opposingSOGoals = gameResponse.json()['liveData']['linescore']['shootoutInfo'][opposingLoc]['scores']
        
        if (starsSOGoals > opposingSOGoals):    
            # Append goals for/against 
            goalsTotFor.append(playList[-1]['about']['goals'][starsLoc] + 1)
            goalsTotAgainst.append(playList[-1]['about']['goals'][opposingLoc])
        else:
            goalsTotAgainst.append(playList[-1]['about']['goals'][opposingLoc] + 1)
            goalsTotFor.append(playList[-1]['about']['goals'][starsLoc])
            
    else:
        # Append goals for/against 
        goalsTotFor.append(playList[-1]['about']['goals'][starsLoc])
        goalsTotAgainst.append(playList[-1]['about']['goals'][opposingLoc])
        

    # Check outcome of the game by comparing goals from last entry of For/Against lists
    if (goalsTotFor[-1] > goalsTotAgainst[-1]):
        outcome.append('W')
    else:
        outcome.append('L')

    # Get stars skaters and goalies
    starsSkaters = boxScore['teams'][starsLoc]['skaters']
    starsGoalies = boxScore['teams'][starsLoc]['goalies']

    # Get opposing skaters and goalies
    opposingSkaters = boxScore['teams'][opposingLoc]['skaters']
    opposingGoalies = boxScore['teams'][opposingLoc]['goalies']

    # Append each team's active players for that game to lists
    playersFor.append([starsSkaters,starsGoalies])
    playersAgainst.append([opposingSkaters,opposingGoalies])

    defendingDict = {}

    for period in periods:

        periodNum = period['num']

        defendingDict[periodNum] = period[starsLoc]['rinkSide']

    defendingDictList.append(defendingDict)
    
    return playList, defendingDict, starsLoc, opposingLoc

def getPlays(playList, defendingDict, starsLoc, opposingLoc):
    playType, player, period, time = [],[],[],[]
    goalsFor, goalsAgainst, x_coord, y_coord = [],[],[],[]

    # For the time being, I'm not including missed or blocked shots
    acceptablePlays = ['SHOT','GOAL','GIVEAWAY','TAKEAWAY']

    for play in playList:

        try:
            if ((play['team']['id'] == teamID) & (play['result']['eventTypeId'] in acceptablePlays)):

                playType.append(play['result']['eventTypeId'])
                player.append(play['players'][0]['player']['id'])
                period.append(play['about']['period'])
                time.append(play['about']['periodTime'])
                goalsFor.append(play['about']['goals'][starsLoc])
                goalsAgainst.append(play['about']['goals'][opposingLoc])
                
                #if (defendingDict[play['about']['period']] == 'right'):
                #    x_coord.append(play['coordinates']['x']*-1)
                #else:
                #    x_coord.append(play['coordinates']['x'])
                
                x_coord.append(play['coordinates']['x'])
                y_coord.append(play['coordinates']['y'])

        # Stoppage plays don't have the above properties so we have to catch those errors
        except(KeyError):
            
            pass
            #print("stoppage or some nonsense")

    plays = pd.DataFrame({'play':playType, 'player':player, 'period':period, 'time':time,
                 'goalsFor': goalsFor, 'goalsAgainst': goalsAgainst,'x': x_coord, 'y': y_coord})
    
    # Drop shootout plays
    playsNoSO = plays.loc[plays['period'] < 5,:].copy()
    
    # Check which side the Stars are playing on. If it's the right side, then flip the x coordinates
    # Want x to be positive for attacking end and negative for defending end
    for row in playsNoSO.itertuples():
        if (defendingDict[row[3]] == 'right'):
            playsNoSO.loc[row[0],'x'] = playsNoSO.loc[row[0],'x']*-1
    
    return playsNoSO

# Set up empty lists
gameDates, opposingTeam, homeAway, outcome, goalsTotFor = [],[],[],[],[]
goalsTotAgainst, playersFor, playersAgainst, defendingDictList = [],[],[],[]

# Dallas Stars are ID 25
teamID = 25

# Do not run if this script is invoked by another script
if __name__ == '__main__':

    # Get today's date
    endDate = datetime.now().strftime('%Y-%m-%d')

    # Set base_url to get game endpoints
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?'

    # Set parameters for request
    params = {
        'teamId': teamID,
        'startDate': '2019-10-01',
        'endDate': endDate
    }

    # Get list of game endpoints for team
    response = requests.get(url, params)
    gameList = response.json()['dates']

    # Loop through games
    for idx,game in enumerate(gameList):
        gameEndpoint = game['games'][0]['link']
        game_url = "https://statsapi.web.nhl.com" + gameEndpoint
        
        print(f'Grabbing: {game_url}')
        gameResponse = requests.get(game_url)
        
        # Run gameOverview to make meta df, but also return the playlist for each game
        playList, defendingDict, starsLoc, opposingLoc = gameOverview(gameResponse)
        
        # Run getplays on the playlist and return the df
        playdf = getPlays(playList, defendingDict, starsLoc, opposingLoc)
        
        playdf.to_csv(f'./gameplayData/game_{idx}.csv',index=False)

    # Create dataframe and save to a csv    
    gamedf = pd.DataFrame({'Dates':gameDates,'Opposition':opposingTeam,'Location':homeAway,
                'Outcome': outcome, 'goalsFor': goalsTotFor, 'goalsAgainst': goalsTotAgainst,
                'starsPlayers': playersFor, 'opposingPlayers': playersAgainst, 
                'defendingDict':defendingDictList})

    gamedf.to_csv('./gameMetaData/gamesOverview.csv',index=False)