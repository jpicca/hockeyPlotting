import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
from datetime import datetime
from gridder import Gridder
from glob import glob
from scipy.ndimage import gaussian_filter
from playerDict import playerDict

# Get today's date since we may need it for plot titles, etc
#now = datetime.now().strftime('%Y-%m-%d')
lastGame = pd.read_csv('./gameMetaData/gamesOverview.csv').iloc[-1,:]['Dates'][0:10]

playType = 'SHOT'
plotType = 'Diff' # Win, Loss, Diff, or All
player = 'Heiskanen'
filename=f'./images/{player}ShotDiff.png'
#filename = f'./images/stars{playType}PGHeatMap{plotType}_test.png'

def createGrid(dx=10,dy=10):

    # Create arrays for gridding
    x_axis = np.arange(-100,100,dx)
    y_axis = np.arange(-42.5,42.5,dy)

    # Create our meshgrid from our arrays
    X, Y = np.meshgrid(x_axis, y_axis)

    # Set up the grid
    G = Gridder(X,Y)

    return G

def plotter(data,cmap,filename,title='',vmin=-0.04,vmax=0.04,annot=''):
    #cmap = sns.cubehelix_palette(light=1, as_cmap=True)

    fig, ax = plt.subplots(figsize=(14.12,6))
    sns.heatmap(data,ax=ax,xticklabels=False,yticklabels=False, cmap=cmap, alpha=0.8, zorder=2,
                vmin=vmin,vmax=vmax,cbar_kws={'label': 'Relative Frequency Difference (Warmer: Clutch, Colder: Regular)'})

    # Get rink image array
    map_img = mpimg.imread('./rinkDiagram_edit.png') 

    # Show the image on our created ax object, but set it beneath the heatmap (zorder = 1)
    ax.imshow(map_img,
            aspect = ax.get_aspect(),
            extent = ax.get_xlim() + ax.get_ylim(),
            zorder = 1) #put the map under the heatmap

    #plt.annotate('boob',xy=(100,10),zorder=3)
    ax.annotate(annot,(3,9.3))
    plt.annotate('Clutch defined as 3rd Period within One Goal or OT', (3,9.6))
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename,dpi=300)

# Get the difference map (wins minus losses) for a certain play
def winLossDiff(play,filter=True,name=None):

    path = './gameplayData/'
    numFiles = len(glob(f'{path}*'))

    # Use this to subset games
    masterGameDF = pd.read_csv('./gameMetaData/gamesOverview.csv')

    G = createGrid()

    # Get player ID from dictionary
    player = playerDict[name]

    if player:
        print(player)

        # Create our grids
        total_grid = np.zeros(G.tx.shape)
        totalGridReg = np.zeros(G.tx.shape)
        totalGridClutch = np.zeros(G.tx.shape)

        i = 0 

        while i < numFiles:
        
            df = pd.read_csv(f'./gameplayData/game_{i}.csv')

            # Use this to set score on 'GOAL' plays to previous play score
            for idx,row in enumerate(df.itertuples()):
                if (row[1] == 'GOAL'):
                    df.loc[idx, 'goalsFor'] = prevGoalsFor
                    #print(prevGoalsFor)
                prevGoalsFor = row[5]

            # If user inputs shot, we also need to include goals
            if (play == 'SHOT'):
                justPlay = df.loc[(df['play'] == play) | (df['play'] == 'GOAL'),:].copy()
            else:
                justPlay = df.loc[df['play'] == play,:].copy()

            if (i == 0):
                allGames = justPlay
            else:
                allGames = pd.concat([justPlay,allGames]).reset_index(drop=True)
            
            i += 1


        # Currently, clutch goals are those scored in the 3rd when the team is down by no
        # more than 2 goals or the game is tied
        # The issue is that the goals for/against

        playerAllPlays = allGames.loc[allGames['player'] == player, :].copy()
        playerRegPlays = playerAllPlays.loc[(playerAllPlays['period'] < 3) |
                        ((playerAllPlays['period'] > 2) &
                        (abs(playerAllPlays['goalsFor']-playerAllPlays['goalsAgainst'])>1)),:].copy()
        playerClutchPlays = playerAllPlays.loc[((playerAllPlays['period'] > 2)
                        & (abs(playerAllPlays['goalsFor']-playerAllPlays['goalsAgainst'])<2)),:].copy()

        points = G.grid_points(playerAllPlays['x'], playerAllPlays['y'])  # Run the Gridder!
        regPoints = G.grid_points(playerRegPlays['x'], playerRegPlays['y'])  # Run the Gridder!
        cluPoints = G.grid_points(playerClutchPlays['x'], playerClutchPlays['y'])  # Run the Gridder!
        
        # Loop through the returned points and increment
        # that grid cell by 1.

        for point in points:
            total_grid[point] += 1

        for point in regPoints:
            totalGridReg[point] += 1

        for point in cluPoints:
            totalGridClutch[point] += 1

        # Depending on the filter keyword, either filter or not. Default is filter.
        print(f'Non-clutch Situation Shots: {np.sum(totalGridReg)}')
        print(f'Clutch Situation Shots: {np.sum(totalGridClutch)}')
        
        if filter:
            playTotal = gaussian_filter(total_grid,sigma=1)
            playReg = gaussian_filter(totalGridReg,sigma=1)
            playClu = gaussian_filter(totalGridClutch,sigma=1)
        else:
            playTotal = total_grid
            playReg = totalGridReg
            playClu = totalGridClutch

        # Relative distributions by game situation (regular v clutch)
        playRegNorm = playReg/np.sum(playReg)
        playCluNorm = playClu/np.sum(playClu)
        playDiffNorm = playCluNorm - playRegNorm
        
        #if filter:
        #    playRegNorm = gaussian_filter(playRegNorm,sigma=1)
        #    playCluNorm = gaussian_filter(playCluNorm,sigma=1)
        #    playDiffNorm = gaussian_filter(playCluNorm - playRegNorm,sigma=1)
            

        # Diverging
        cmap = sns.color_palette("RdBu_r", 21)
        
        # Sequential
        #cmap = sns.color_palette("Reds", 18)
        #cmap[0] = (1,1,1)

        vmin = -0.035
        vmax = 0.035
        title = f'Difference in Relative Shot Selection between Regular and Clutch Situations for {name}'
        annot = f'Shots in Regular Situations: {np.sum(totalGridReg)}; Shots in Clutch Situations: {np.sum(totalGridClutch)}'

        return playDiffNorm, cmap, title, vmin, vmax, annot

    else:
        
        # Create our grids
        total_grid = np.zeros(G.tx.shape)
        totalGridLoss = np.zeros(G.tx.shape)
        totalGridWin = np.zeros(G.tx.shape)

        i = 0 

        while i < numFiles:
        
            df = pd.read_csv(f'./gameplayData/game_{i}.csv')

            # If user inputs shot, we also need to include goals
            if (play == 'SHOT'):
                justPlay = df.loc[(df['play'] == play) | (df['play'] == 'GOAL'),:].copy()
            else:
                justPlay = df.loc[df['play'] == play,:].copy()
            
            points = G.grid_points(justPlay['x'], justPlay['y'])  # Run the Gridder!
            
            # Loop through the returned points and increment
            # that grid cell by 1.
            if (masterGameDF.loc[i,'Outcome'] == 'W'): 
                for point in points:
                    total_grid[point] += 1
                    totalGridWin[point] += 1
            else:
                for point in points:
                    total_grid[point] += 1
                    totalGridLoss[point] += 1 
                    
            i += 1

        # Get the win and loss count
        wins = masterGameDF.groupby('Outcome').count().loc['W','Dates']
        losses = masterGameDF.groupby('Outcome').count().loc['L','Dates']

        # Depending on the filter keyword, either filter or not. Default is filter.
        if filter:
            PerGameTotal = gaussian_filter(total_grid/(wins+losses),sigma=1)
            PerGameWin = gaussian_filter(totalGridWin/wins,sigma=1)
            PerGameLoss = gaussian_filter(totalGridLoss/losses,sigma=1)
        else:
            PerGameTotal = total_grid/(wins+losses)
            PerGameWin = totalGridWin/wins
            PerGameLoss = totalGridLoss/losses

        # Decide the cmap,title in the function creating the data, since it's data specific    
        
        # Diverging
        cmap = sns.color_palette("RdBu_r", 13)
        
        # Sequential
        #cmap = sns.color_palette("Reds", 10)
        # Set the first color to white
        #cmap[0] = (1,1,1)

        titleDict = {'Win': 'in Wins',
                    'Loss': 'in Losses',
                    'Diff':'Difference between Wins and Losses',
                    'All': 'All Games'}

        playDict = {'GIVEAWAY': "Giveaways", "SHOT": "Shots", "TAKEAWAY": "Takeaways"}

        returnDict = {'Win': PerGameWin,
                    'Loss': PerGameLoss,
                    'Diff': PerGameWin - PerGameLoss,
                    'All': PerGameTotal}

        title = f'Dallas Stars {playDict[playType]} Per Game {titleDict[plotType]} (thru {lastGame})'
        #title = f'Dallas Stars Per Game Difference between Wins and Losses (Play Type: {play}; thru {lastGame})'

        return returnDict[plotType], cmap,title

dataToPlot, cmap, title, vmin, vmax, annot = winLossDiff(playType,filter=True, name=player)

plotter(dataToPlot, cmap, filename,title,vmin,vmax,annot=annot)

