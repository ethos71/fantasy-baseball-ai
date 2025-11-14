"""Helper utilities for Streamlit dashboard"""
import streamlit as st

def abbreviate_position(pos, player_name='', yahoo_position=''):
    """Convert position to Yahoo-style abbreviation"""
    # If we have Yahoo position data with SP/RP, use it
    if yahoo_position:
        if 'SP' in yahoo_position and 'RP' in yahoo_position:
            return 'SP,RP'
        elif 'SP' in yahoo_position:
            return 'SP'
        elif 'RP' in yahoo_position:
            return 'RP'
    
    # Fallback to MLB data position mapping
    abbrev_map = {
        'Catcher': 'C',
        'First Base': '1B',
        'Second Base': '2B',
        'Third Base': '3B',
        'Shortstop': 'SS',
        'Outfielder': 'OF',
        'Designated Hitter': 'DH',
        'Pitcher': 'P',
        'Infielder': 'IF',
        'Unknown': '?'
    }
    return abbrev_map.get(pos, pos)

def create_yahoo_link(player_name, player_key=''):
    """Create Yahoo Fantasy player page link"""
    if player_key:
        player_id = player_key.split('.')[-1] if '.' in player_key else ''
        if player_id:
            url = f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{player_id}"
            return f'<a href="{url}" target="_blank">{player_name}</a>'
    return player_name

def get_recommendation_emoji(recommendation):
    """Get emoji for recommendation type"""
    if 'STRONG START' in recommendation:
        return '🌟'
    elif 'FAVORABLE' in recommendation or 'START' in recommendation:
        return '✅'
    elif 'UNFAVORABLE' in recommendation:
        return '⚠️'
    elif 'BENCH' in recommendation or 'SIT' in recommendation:
        return '🚫'
    else:
        return '⚖️'
