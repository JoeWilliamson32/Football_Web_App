import pandas as pd
import numpy as np
import io

# ML
from sklearn import preprocessing
from sklearn.decomposition import PCA

# Dashboard
import streamlit as st


def data_prep_posMins(df, position):
    
    df_pos = df[(df['Position'] == position)].reset_index(drop=True)

    col_90s = df_pos['Mins']/90
    for col in df_pos.iloc[:, 4:]:
        if col == 'Pass Completion Rate':
            continue 

        df_pos[col] = df_pos[col]/col_90s
        
    return df_pos


def data_prep_allMins(df, player, position):
    df1 = df[(df['Position'] == position) & 
             (df['playerName'] != player)].reset_index(drop=True)

    df2 = df[df['playerName'] == player].reset_index(drop=True)
    
    cols = ['Mins', 'Passes Completed', 'Passes Attempted', 'Forward Passes', 'Long Passes', 
            'xT via Pass', 'npxG', 'xA', 'Shots', 'Tackles', 'Interceptions', 'Fouls', 'Aerials', 'Recoveries', 
            'Ball Wins', 'Touches', 'Box Touches', 'Final 1/3 Touches', 'Progressive Passes', 
            'Progressive Carries', 'Box Passes', 'Box Carries', 'Successful Take Ons', 'xT Carry', 'xT Received']
    
    d1 = dict.fromkeys(cols, 'sum')
    df2 = df2.groupby(['playerName', 'PlayerID']) \
             .agg(d1) \
             .reset_index()

    df2['Pass Completion Rate'] = df2['Passes Completed'] / df2['Passes Attempted']
    df2['Position'] = position
    order = list(df2.columns[:2]) + [df2.columns[28]] + list(df2.columns[2:6]) + [df2.columns[27]] + list(df2.columns[6:27])

    df2 = df2[order]
    
    df_pos = pd.concat([df1, df2], axis=0).reset_index(drop=True)
    
    col_90s = df_pos['Mins']/90
    for col in df_pos.iloc[:, 4:]:
        if col == 'Pass Completion Rate':
            continue 

        df_pos[col] = df_pos[col]/col_90s

        
    return df_pos


def playerSimilaritySearch(df, name):
    df_info, df_metrics = df.iloc[:, :4], df.iloc[:, 4:]
    cols = df_metrics.columns.tolist()

    vals = df_metrics.values
    scaler = preprocessing.MinMaxScaler()
    vals_scaled = scaler.fit_transform(vals)
    vals_norm = pd.DataFrame(vals_scaled, columns=cols)
    
    pca_2d = PCA(n_components = 2)
    df_reduced = pd.DataFrame(pca_2d.fit_transform(vals_norm), columns=['x', 'y'])
    df = pd.concat([df_info, df_reduced], axis=1)

    x,y = df[df['playerName'] == name]['x'].tolist()[0], df[df['playerName'] == name]['y'].tolist()[0]

    df['Difference Score'] = round(np.sqrt((x - df['x'])**2 + (y - df['y'])**2), 3)
    df = df.sort_values(by='Difference Score').reset_index(drop=True)[['playerName', 'Mins', 'Difference Score']]
    df.columns = ['Player', 'Minutes', 'Difference Score']

    return df.head(11)


st.title('Player Profiles')

st.divider()

st.markdown(
"""
- Only includes PL Teams for the 23/24 season as of the minute.
- Data as of Gameweek 27.
- Only includes players who have played more than 100 minutes in the respective position. 
- Goalkeepers not included. 
"""
)


df = pd.read_csv('player_db.csv').iloc[:,1:]
df = df[(df['Mins'] >= 100) & 
        (df['Position'] != 'Goalkeeper')].reset_index(drop=True)

players = sorted(list(set(df['playerName'])))

player = st.selectbox(
    'Player Name', 
    players
)

positions = list(df[df['playerName'] == player]['Position'])

position = st.selectbox(
    'Position', 
    positions
)

all_mins = st.checkbox('To include all minutes at above positions')

if all_mins:
    df = data_prep_posMins(df, position)

else:
    df = data_prep_allMins(df, player, position)

df_similar = playerSimilaritySearch(df)

generate = st.button('Create Plot')

if generate:
    st.dataframe(df_similar)