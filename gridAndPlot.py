import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
from datetime import datetime
from gridder import Gridder
from glob import glob
from scipy.ndimage import gaussian_filter

# Set your grid spacing (in feet)
dx = 5
dy = 5

# Get today's date since we may need it for plot titles, etc
#now = datetime.now().strftime('%Y-%m-%d')
lastGame = pd.read_csv('./gameMetaData/gamesOverview.csv').iloc[-1,:]['Dates'][0:10]

def createGrid(dx,dy):

    # Create arrays for gridding
    x_axis = np.arange(-100,100+dx,dx)
    y_axis = np.arange(-42.5,42.5+dy,dy)

    # Create our meshgrid from our arrays
    X, Y = np.meshgrid(x_axis, y_axis)

    # Set up the grid
    G = Gridder(X,Y)

    return G

def plotter(data,cmap,filename,title=''):
    #cmap = sns.cubehelix_palette(light=1, as_cmap=True)

    fig, ax = plt.subplots(figsize=(14.12,6))
    sns.heatmap(data,ax=ax,xticklabels=False,yticklabels=False, vmin = -0.04, vmax=0.04, cmap=cmap, alpha=0.8, zorder=2)

    # Get rink image array
    map_img = mpimg.imread('./rinkDiagram_edit.png') 

    # Show the image on our created ax object, but set it beneath the heatmap (zorder = 1)
    ax.imshow(map_img,
            aspect = ax.get_aspect(),
            extent = ax.get_xlim() + ax.get_ylim(),
            zorder = 1) #put the map under the heatmap

    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename,dpi=300)

# Get the difference map (wins minus losses) for a certain play
def winLossDiff(play,filter=True):

    path = './gameplayData/'
    numFiles = len(glob(f'{path}*'))

    # Use this to subset games
    masterGameDF = pd.read_csv('./gameMetaData/gamesOverview.csv')

    G = createGrid(dx,dy)

    # Create our grids
    total_grid = np.zeros(G.tx.shape)
    totalGridLoss = np.zeros(G.tx.shape)
    totalGridWin = np.zeros(G.tx.shape)

    i = 0 

    while i < numFiles:
    
        df = pd.read_csv(f'./gameplayData/game_{i}.csv')
        justShots = df.loc[df['play'] == play,:].copy()
        
        points = G.grid_points(justShots['x'], justShots['y'])  # Run the Gridder!
        
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

playType = 'GIVEAWAY'
plotType = 'Diff' # Win, Loss, Diff, or All

dataToPlot, cmap, title = winLossDiff(playType,filter=True)

plotter(dataToPlot, cmap, f'./images/stars{playType}PGHeatMap{plotType}_test.png',title)

