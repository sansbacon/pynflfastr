# dkscraper.py

import datetime
import logging
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).parent / 'data'
OFFENSE_PLAY_TYPES = ('pass', 'run', 'qb_spike', 'qb_kneel')
OFFENSE_IMPORTANT_PLAYS = ('pass', 'run')


def convert_top(t):
    """Converts time of possession string to seconds
    
    Args:
        t (str): e.g. '1:30'

    Returns:
        int: e.g. 90
    """
    try:
        m, s = [int(c) for c in t.split(':')]
        return m * 60 + s
    except (AttributeError, ValueError):
        return 0


def current_season():
    """Gets current season year

    Returns:
        int: e.g. 2020
    """
    td = datetime.datetime.today()
    if td.month > 8:
        return td.year
    return td.year - 1


def current_season_week(sched=None):
    """Gets current week of current season
    
    Args:
        sched (DataFrame): default None

    Returns:
        int: 1 - 17
    """
    if sched is None or sched.empty:
        sched = schedule()
    td = datetime.datetime.today()
    seas = current_season()
    week_starts = sched.loc[sched.season == seas, :].groupby('week')['gameday'].min()
    this_week = week_starts.loc[week_starts < td].max()
    return week_starts.loc[week_starts == this_week].index.values[0]


def dst(df):
    """Gets core dst stats from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns

    """
    pass


def gamesmeta(sched=None):
    """Converts schedule to one row per team, two per game"""
    if sched is None or sched.empty:
        sched = schedule()
    h = sched.copy()
    a = sched.copy()
    h = h.rename(columns={'home_team': 'team', 'away_team': 'opp'})
    a = a.rename(columns={'away_team': 'team', 'home_team': 'opp'})
    return pd.concat([a, h]).sort_values('game_id')


def passing(df):
    """Gets core passing stats from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns

    """
    pass


def plays(df):
    """Gets core pace/plays from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns

    """
    tp = (
         df.query('play_type in @OFFENSE_PLAY_TYPES')
        .pivot_table(index=['game_id', 'posteam'], 
                    columns=['play_type'], 
                    values=['play_id'], 
                    aggfunc='count',
                    fill_value=0)
        .pipe(lambda x: x.set_axis([f'{b}_plays' for a, b in x.columns], axis=1, inplace=False))
        .reset_index()
    )   
    tp['tot_plays'] = tp.loc[:, [c for c in tp.columns if '_plays' in c]].sum(axis=1)
    tp['run_pct'] = tp['run_plays'] / (tp['run_plays'] + tp['pass_plays'])
    tp['pass_pct'] = tp['pass_plays'] / (tp['run_plays'] + tp['pass_plays'])
    return tp.join(time_of_possession(df), on=['game_id', 'posteam'], how='left')
    

def receiving(df):
    """Gets core receiving stats from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns
        targets, receptions, rec_yards, rec_tds, 
        total_air_yards, inc_air_yards, yac
    """
    cols = ['player', 'targets', 'receptions', 'rec_yards', 'rec_tds',
            'total_air_yards', 'inc_air_yards', 'yac']
    return (
        df
        .query('play_type == "pass"')
        .groupby(['game_id', 'receiver_player_id'])
        .agg(targets=('play_type', 'count'),
            receptions=('complete_pass', 'sum'),
            rec_yards=('yards_gained', 'sum'),
            rec_tds=('pass_touchdown', 'sum'),
            total_air_yards=('air_yards', 'sum'), 
            yac=('yards_after_catch', 'sum'))
        .assign(inc_air_yards=lambda x: x['total_air_yards'] + x['yac'] - x['rec_yards'])
        .reset_index(level=0, drop=True)
        .join(df.groupby('receiver_player_id').first()['receiver_player_name'], how='left')
        .reset_index(drop=True)
        .rename(columns={'receiver_player_name': 'player'})
        .loc[:, cols]
        .set_index('player')
        .fillna(0)
        .astype(int)
    )


def rushing(df, add_success=False):
    """Gets core rushing stats from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe
        add_success (bool): add success data, default False

    Returns:
        DataFrame with columns
        'rush_att', 'rush_yards', 'rush_tds'
    """
    tmp = (
        df
        .query('play_type == "run"')
        .rename(columns={'rusher_player_id': 'player_id', 'rusher_player_name': 'player'})
        .groupby(['game_id', 'player_id', 'player'])
        .agg(rush_att=('rush_attempt', 'sum'),
            rush_yards=('yards_gained', 'sum'),
            rush_tds=('rush_touchdown', 'sum'))
        .droplevel(0)
        .fillna(0)
        .astype(int)
    )
    if add_success:
        s = rushing_success_rate(df)
        tmp = tmp.join(s.drop('rushes', axis=1), how='left')
    return tmp


def rushing_success(row):
    """Determines whether rushing play was success
    Based on Chase Stuart / Football perspectives
    Returns:
        int: 1 if success, 0 otherwise
    """
    success = 0
    if row.down == 1:
        if row.yards_gained >= 6:
            success = 1
        elif row.yards_gained >= row.ydstogo * .4:
            success = 1
    elif row.down == 2:
        if row.yards_gained >= 6:
            success = 1
        elif row.yards_gained >= row.ydstogo * .5:
            success = 1
    elif row.down > 3:
        if row.yards_gained >= row.ydstogo:
            success = 1
    return success


def rushing_success_rate(df):
    """Calculates rushing success rate"""
    df['success'] =  df.apply(rushing_success, axis=1)
    criteria = (df.down > 2) & (df.ydstogo > 5)
    return (
        df
        .loc[~criteria, :]
        .rename(columns={'rusher_player_id': 'player_id', 'rusher_player_name': 'player'})
        .groupby(['game_id', 'player_id', 'player'])
        .agg(successes=('success', 'sum'),
             rushes=('rush_attempt', 'sum'))
        .assign(success_rate=lambda df_: df_.successes / df_.rushes)
        .droplevel(0)
    )


def schedule(fn=None):
    """Gets schedule"""
    if not fn:
        fn = DATA_DIR / 'schedule.parquet'
    return pd.read_parquet(fn)


def situation(df):
    """Gets situational rates"""
    tmp1 = plays(df.loc[df.score_differential.abs() <= 6, :])
    tmp1['situation_type'] = 'Neutral'
    tmp2 = plays(df.loc[df.score_differential > 6, :])
    tmp2['situation_type'] = 'Ahead'
    tmp3 = plays(df.loc[df.score_differential < -6, :])
    tmp3['situation_type'] = 'Behind'
    return (
        pd.concat([tmp1, tmp2, tmp3], axis=0, ignore_index=True)
        .set_index(['game_id', 'posteam'])
        .fillna(0)
    )


def time_of_possession(df):
    """Gets time of possession from play-by-play

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns

    """
    drives = (
        df.groupby(['game_id', 'posteam', 'fixed_drive'])
        .first()
        .loc[:, 'drive_time_of_possession']
        .reset_index()
    )

    drives['top'] = drives.drive_time_of_possession.apply(convert_top)
    return drives.groupby(['game_id', 'posteam'])['top'].sum() / 60


def touchdowns(df):
    """Gets data on touchdown plays

    Args:
        df (DataFrame): play-by-play dataframe

    Returns:
        DataFrame with columns

    """
    return (
        df
        .loc[df.play_type.isin(['run', 'pass']), :]
        .assign(player=lambda x: np.where(pd.isna(x['receiver_player_name']), x['rusher_player_name'], x['receiver_player_name']))
        .loc[:, ['play_id', 'player', 'play_type', 'yards_gained']]
        .sort_values('yards_gained', ascending=False)
    )


if __name__ == '__main__':
    pass