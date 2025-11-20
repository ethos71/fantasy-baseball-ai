#!/usr/bin/env python3
"""
Create Roster File

Simple script to create a roster CSV file with your actual players.
This will be used by the sit/start analysis.

Usage:
    python src/scripts/create_roster.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def create_roster_file():
    """Create a roster CSV file"""
    
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    Create Your Fantasy Roster                             ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("Enter your roster players (one per line).")
    print("Press Enter twice when done.")
    print()
    
    players = []
    while True:
        player = input(f"Player {len(players)+1} (or press Enter to finish): ").strip()
        if not player:
            if len(players) > 0:
                break
            else:
                continue
        players.append(player)
    
    if not players:
        print("❌ No players entered!")
        return
    
    # Create DataFrame
    df = pd.DataFrame({
        'player_name': players,
        'team': [''] * len(players),  # Can be filled in later
        'position': [''] * len(players),  # Can be filled in later
    })
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path('data') / f'yahoo_roster_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    
    print()
    print(f"✅ Roster saved: {output_file.name}")
    print(f"📊 Players: {len(players)}")
    print()
    print("Your roster:")
    for i, player in enumerate(players, 1):
        print(f"  {i:2d}. {player}")
    print()
    print("Now run: ./fb-ai --date 2025-09-28")
    print()


if __name__ == '__main__':
    create_roster_file()
