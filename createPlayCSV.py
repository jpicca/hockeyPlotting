#######
## This script creates csvs to be read by the front-end javascript for plotting
## Eventually would like it to be called by front end to produce data on the fly
#######

import pandas as pd
import numpy as np
from glob import glob
from gridder import Gridder
from scipy.ndimage import gaussian_filter

game = 55
play = 'SHOT'
path = './gameplayData/'
numFiles = len(glob(f'{path}*'))

def createGrid(dx=2.5,dy=2.5):

    # Create arrays for gridding
    x_axis = np.arange(-100,100,dx)
    y_axis = np.arange(-42.5,42.5,dy)

    # Create our meshgrid from our arrays
    X, Y = np.meshgrid(x_axis, y_axis)

    # Set up the grid
    G = Gridder(X,Y)

    return G

# Use this to subset games
masterGameDF = pd.read_csv('./gameMetaData/gamesOverview.csv')

# Create grid object
G = createGrid()
totalGrid = np.zeros(G.tx.shape)
totalGridWin = np.zeros(G.tx.shape)
totalGridLoss = np.zeros(G.tx.shape)

i = 0 

while i < numFiles:

    df = pd.read_csv(f'./gameplayData/game_{i}.csv')

    # Create a fresh set of empty grids for the next game
    gameGrid = np.zeros(G.tx.shape)

    # If user inputs shot, we also need to include goals
    if (play == 'SHOT'):
        justPlay = df.loc[(df['play'] == play) | (df['play'] == 'GOAL'),:].copy()
    else:
        justPlay = df.loc[df['play'] == play,:].copy()

    points = G.grid_points(justPlay['x'], justPlay['y'])  # Run the Gridder!

    # Grid shot points for that game
    for point in points:
        gameGrid[point] += 1

    # Loop through the returned points and increment
    # that grid cell by 1.
    if (masterGameDF.loc[i,'Outcome'] == 'W'): 
        for point in points:
            totalGrid[point] += 1
            totalGridWin[point] += 1

        # Save the game grid to the win folder
        np.savetxt(f"./shotCSVs/win/game_{i}.csv", gameGrid.flatten(), newline=',', fmt='%1.2f')
    else:
        for point in points:
            totalGrid[point] += 1
            totalGridLoss[point] += 1 
        # Save the game grid to the loss folder
        np.savetxt(f"./shotCSVs/loss/game_{i}.csv", gameGrid.flatten(), newline=',', fmt='%1.2f')

    # Save the game grid to the all folder
    np.savetxt(f"./shotCSVs/all/game_{i}.csv", gameGrid.flatten(), newline=',', fmt='%1.2f')

    i += 1

# Get the win and loss count
wins = masterGameDF.groupby('Outcome').count().loc['W','Dates']
losses = masterGameDF.groupby('Outcome').count().loc['L','Dates']

pgLoss = totalGridLoss/losses
pgWin = totalGridWin/wins
pgAll = totalGrid/(wins+losses)

# Absolute totals
np.savetxt(f"./shotCSVs/all/allGames.csv", totalGrid.flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/win/allWins.csv", totalGridWin.flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/loss/allLosses.csv", totalGridLoss.flatten(), newline=',', fmt='%1.2f')

# Per Game
np.savetxt(f"./shotCSVs/all/allGamesPG.csv", pgAll.flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/win/allWinsPG.csv", pgWin.flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/loss/allLossesPG.csv", pgLoss.flatten(), newline=',', fmt='%1.2f')

### Filtered 
# ------------
# Absolute totals
np.savetxt(f"./shotCSVs/all/allGames_F.csv", gaussian_filter(totalGrid,sigma=1).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/win/allWins_F.csv", gaussian_filter(totalGridWin,sigma=1).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/loss/allLosses_F.csv", gaussian_filter(totalGridLoss,sigma=1).flatten(), newline=',', fmt='%1.2f')

# Per Game
np.savetxt(f"./shotCSVs/all/allGamesPG_F.csv", gaussian_filter(pgAll,sigma=1).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/win/allWinsPG_F.csv", gaussian_filter(pgWin,sigma=1).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/loss/allLossesPG_F.csv", gaussian_filter(pgLoss,sigma=1).flatten(), newline=',', fmt='%1.2f')

# Differences
# -------------
np.savetxt(f"./shotCSVs/diff/diff.csv", (totalGridWin-totalGridLoss).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/diff/diff_F.csv", gaussian_filter(totalGridWin-totalGridLoss, sigma=1).flatten(), newline=',', fmt='%1.2f')

np.savetxt(f"./shotCSVs/diff/diffPG.csv", (pgWin-pgLoss).flatten(), newline=',', fmt='%1.2f')
np.savetxt(f"./shotCSVs/diff/diffPG_F.csv", gaussian_filter(pgWin-pgLoss,sigma=1).flatten(), newline=',', fmt='%1.2f')