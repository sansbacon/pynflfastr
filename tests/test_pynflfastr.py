from pathlib import Path
import random
import sys

import pandas as pd
import pytest

sys.path.append(str(Path.home() / 'workspace' / 'pynflfastr'))
from pynflfastr import *


@pytest.fixture
def df(test_directory):
    return pd.read_parquet(test_directory / 'pbp.parquet')


def test_convert_top():
    """Tests convert_top"""
    vals = {
        '1:30': 90,
        None: 0,
        '11:12': 672
    }

    for t, v in vals.items():
        assert convert_top(t) == v


def test_plays(df):
    """Tests plays"""
    tp = plays(df)

    teamplays = {
        'ARI': 78,
        'BUF': 81,
        'PHI': 67,
        'CAR': 65,
        'JAX': 47,
        'MIN': 49
    }
    
    for t, v in teamplays.items():
        assert tp.loc[tp.posteam == t, 'tot_plays'].values[0] == v


def test_receiving(df):
    """Tests receiving"""
    r = receiving(df)
    assert r.loc['J.Jones', 'rec_yards'] == 157
    assert r.loc['D.Adams', 'rec_tds'] == 2
    cols = {'targets', 'receptions', 'rec_yards', 'rec_tds', 
            'total_air_yards', 'inc_air_yards', 'yac'}
    assert set(r.columns) == cols


def test_rushing(df, tprint):
    """Tests rushing"""
    r = rushing(df)
    assert r.xs('J.Jacobs', level=1)['rush_tds'].values[0] == 3
    assert r.xs('J.Mixon', level=1)['rush_yards'].values[0] == 69
    cols = {'rush_att', 'rush_yards', 'rush_tds'}
    assert set(r.columns) == cols
    assert list(r.index.names) == ['player_id', 'player']


def test_rushing_add_success(df, tprint):
    """Tests rushing with add rushing success parameter"""
    r = rushing(df, True)
    assert r.xs('H.Ruggs', level=1)['success_rate'].values[0] == 1
    cols = {'rush_att', 'rush_yards', 'rush_tds', 'successes', 'success_rate'}
    assert set(r.columns) == cols
    assert list(r.index.names) == ['player_id', 'player']
    

def test_rushing_success_rate(df, tprint):
    s = rushing_success_rate(df)
    assert s.xs('H.Ruggs', level=1)['success_rate'].values[0] == 1
    cols = {'rushes', 'successes', 'success_rate'}
    assert set(s.columns) == cols
    assert set(s.index.names) == {'player_id', 'player'}
    

def test_dst(df):
    """Tests dst"""
    pass


def test_time_of_possession(df):
    """Tests time of possession"""
    pass


def test_touchdowns(df):
    """Tests touchdowns"""
    pass


def test_situation(df, tprint):
    """Tests situation"""
    s = situation(df)
    tprint(s)
    assert situation(df) is not None