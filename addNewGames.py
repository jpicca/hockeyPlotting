import requests
import pandas as pd
from datetime import datetime, timedelta
from glob import glob
import apiDataGrab

# Read in the main game csv
df = pd.read_csv('./gameMetaData/gamesOverview.csv',index_col=0)

# Set base_url to get game endpoints
url = 'https://statsapi.web.nhl.com/api/v1/schedule?'

# Get last game date by pulling the date from the game dataframe
beginDate = df.iloc[-1,:]['Dates'][0:10]

# Get today's date
endDate = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# Set parameters for request
params = {
    'teamId': apiDataGrab.teamID,
    'startDate': beginDate,
    'endDate': endDate
}

# Get list of game endpoints for team
response = requests.get(url, params)
gameList = response.json()['dates']

# Loop through games
for idx,game in enumerate(gameList):
    path = './gameplayData/'
    numFiles = len(glob(f'{path}*'))

    gameEndpoint = game['games'][0]['link']
    game_url = "https://statsapi.web.nhl.com" + gameEndpoint
    
    print(f'Grabbing: {game_url}')
    gameResponse = requests.get(game_url)
    
    # Run gameOverview to make meta df, but also return the playlist for each game
    playList, defendingDict, starsLoc, opposingLoc = apiDataGrab.gameOverview(gameResponse)
    
    # Run getplays on the playlist and return the df
    playdf = apiDataGrab.getPlays(playList, defendingDict, starsLoc, opposingLoc)
    
    playdf.to_csv(f'./gameplayData/game_{numFiles + idx}.csv',index=False)

# Create dataframe and save to a csv    
gamedf = pd.DataFrame({'Dates':apiDataGrab.gameDates,
                        'Opposition':apiDataGrab.opposingTeam,
                        'Location':apiDataGrab.homeAway,
                        'Outcome': apiDataGrab.outcome, 
                        'goalsFor': apiDataGrab.goalsTotFor,
                        'goalsAgainst': apiDataGrab.goalsTotAgainst,
                        'starsPlayers': apiDataGrab.playersFor, 
                        'opposingPlayers': apiDataGrab.playersAgainst, 
                        'defendingDict':apiDataGrab.defendingDictList})

# Add new games to old df
updatedf = pd.concat([df,gamedf]).reset_index(drop=True)

# Save to file
updatedf.to_csv('./gameMetaData/gamesOverview.csv')