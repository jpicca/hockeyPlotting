# Aggregating, Gridding, and Plotting Dallas Stars Shots 

### Description
This repo contains various files that aggregate shots on net via the NHL's API, grid those shots, and then produce a front-end, dynamic visualization.

### Back End

There are four primary back-end Python scripts:
- **apiDataGrab.py**: This script is a sort of "initialization" of our data files. If directly called by the user, it will grab all game endpoints for the specified teamID through the current date. It will then build a dataframe and subsequent csv (gamesOverview.csv) with "metadata" for all the games. Additionally, it will build individual game dataframes/csvs that contain all specified (ie desired) plays for each game.

- **addNewGames.py**: This script calls specific functions from apiDataGrab to collect any new games that might have occurred since the initialization from apiDataGrab. It's essentially a streamlined way to just get data from new games, append them to the gamesOverview.csv, and add corresponding individual game csvs.

- **createPlayCSV.py**: This script creates a specified grid (using gridder.py -- see below) and grids desired plays ('SHOT','GIVEAWAY',etc.) for each game type ('win','loss','all') during the current season. Additionally, it applies Gaussian smoothers to produce "filtered" grids for each type. These are all saved to csvs, which are used for plotting.

- **gridder.py**: This script is the backbone of our gridding process. It sets up a new class Gridder, which creates our desired grid and uses a [KDTree](https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.spatial.KDTree.html) for efficient nearest-neighbor lookup and gridding. This Gridder class is imported to createPlayCSV to process our data.

### Front End
Version 5 of d3js is utilized to visualize our gridded shot data. A menu on the left can be used to display data by game type, as well as filtered/smoothed and per-game data.

![Example](https://github.com/jpicca/hockeyPlotting/blob/master/Screenshot%202020-02-19%2017.13.29.png)

### Future Work
The next steps are to develop a logistic regression model that utilizes features associated with shot data to predict goal probability for each shot. These data could then be plotted and utilized to determine is a goalie is performing as expected, above, or below NHL average.

