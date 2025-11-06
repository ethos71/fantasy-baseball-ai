#!/usr/bin/env python3
"""
Weight Configuration Manager

Manages factor analysis weights for both global defaults and player-specific overrides.
Integrates with all factor analysis modules to apply appropriate weights during analysis.
"""

import json
from pathlib import Path
from typing import Dict, Optional
import sys


class WeightConfig:
    """Configuration manager for factor analysis weights"""
    
    # Default weights for all factors
    DEFAULT_WEIGHTS = {
        'wind': 0.10,
        'matchup': 0.15,
        'home_away': 0.12,
        'platoon': 0.10,
        'park_factors': 0.08,
        'rest_day': 0.08,
        'injury': 0.12,
        'umpire': 0.05,
        'temperature': 0.05,
        'pitch_mix': 0.05,
        'lineup_position': 0.05,
        'time_of_day': 0.03,
        'defensive_positions': 0.02
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Auto-detect project root
            current_file = Path(__file__).resolve()
            if 'src' in current_file.parts:
                # Navigate up to project root
                project_root = current_file
                while project_root.name != 'fantasy-baseball-ai' and project_root.parent != project_root:
                    project_root = project_root.parent
            else:
                project_root = Path.cwd()
        
        self.project_root = project_root
        self.config_dir = project_root / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.global_weights_file = self.config_dir / "factor_weights.json"
        self.player_weights_file = self.config_dir / "player_weights.json"
        
        # Load weights
        self.global_weights = self.load_global_weights()
        self.player_weights = self.load_player_weights()
    
    def load_global_weights(self) -> Dict:
        """Load global factor weights"""
        if self.global_weights_file.exists():
            try:
                with open(self.global_weights_file, 'r') as f:
                    weights = json.load(f)
                    # Merge with defaults to ensure all factors are present
                    return {**self.DEFAULT_WEIGHTS, **weights}
            except Exception as e:
                print(f"⚠️  Error loading global weights: {e}, using defaults")
        
        return self.DEFAULT_WEIGHTS.copy()
    
    def load_player_weights(self) -> Dict[str, Dict]:
        """Load player-specific weight overrides"""
        if self.player_weights_file.exists():
            try:
                with open(self.player_weights_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading player weights: {e}")
        
        return {}
    
    def get_weights(self, player: Optional[str] = None) -> Dict:
        """Get weights for a specific player or global defaults"""
        if player and player in self.player_weights:
            # Merge player-specific with global defaults
            return {**self.global_weights, **self.player_weights[player]}
        
        return self.global_weights.copy()
    
    def set_global_weight(self, factor: str, weight: float):
        """Set a global weight for a factor"""
        if factor not in self.DEFAULT_WEIGHTS:
            raise ValueError(f"Unknown factor: {factor}")
        
        self.global_weights[factor] = weight
    
    def set_player_weight(self, player: str, factor: str, weight: float):
        """Set a player-specific weight override"""
        if factor not in self.DEFAULT_WEIGHTS:
            raise ValueError(f"Unknown factor: {factor}")
        
        if player not in self.player_weights:
            self.player_weights[player] = {}
        
        self.player_weights[player][factor] = weight
    
    def set_player_weights(self, player: str, weights: Dict):
        """Set all weights for a specific player"""
        for factor in weights:
            if factor not in self.DEFAULT_WEIGHTS:
                raise ValueError(f"Unknown factor: {factor}")
        
        self.player_weights[player] = weights.copy()
    
    def save_global_weights(self):
        """Save global weights to file"""
        try:
            with open(self.global_weights_file, 'w') as f:
                json.dump(self.global_weights, f, indent=2)
            print(f"✓ Saved global weights to {self.global_weights_file}")
        except Exception as e:
            print(f"✗ Error saving global weights: {e}")
    
    def save_player_weights(self):
        """Save player-specific weights to file"""
        try:
            with open(self.player_weights_file, 'w') as f:
                json.dump(self.player_weights, f, indent=2)
            print(f"✓ Saved player weights to {self.player_weights_file}")
        except Exception as e:
            print(f"✗ Error saving player weights: {e}")
    
    def save_all(self):
        """Save both global and player weights"""
        self.save_global_weights()
        self.save_player_weights()
    
    def display_weights(self, player: Optional[str] = None):
        """Display weights for console output"""
        print("\n" + "="*60)
        if player:
            print(f"WEIGHTS FOR: {player}".center(60))
        else:
            print("GLOBAL WEIGHTS".center(60))
        print("="*60)
        
        weights = self.get_weights(player)
        
        # Sort by weight value (descending)
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        for factor, weight in sorted_weights:
            bar_length = int(weight * 50)  # Visual bar
            bar = "█" * bar_length
            print(f"{factor:25s} {weight:.4f} {bar}")
        
        total = sum(weights.values())
        print(f"\n{'Total':<25s} {total:.4f}")
        
        if abs(total - 1.0) > 0.01:
            print(f"⚠️  Warning: Weights don't sum to 1.0")
    
    def normalize_weights(self, weights: Dict) -> Dict:
        """Normalize weights to sum to 1.0"""
        total = sum(weights.values())
        if total == 0:
            return self.DEFAULT_WEIGHTS.copy()
        
        return {k: v / total for k, v in weights.items()}
    
    def reset_player_weights(self, player: str):
        """Remove player-specific overrides"""
        if player in self.player_weights:
            del self.player_weights[player]
            print(f"✓ Reset weights for {player} to global defaults")
        else:
            print(f"ℹ️  {player} already using global defaults")
    
    def reset_all_player_weights(self):
        """Remove all player-specific overrides"""
        count = len(self.player_weights)
        self.player_weights = {}
        print(f"✓ Reset weights for {count} players to global defaults")
    
    def list_players_with_custom_weights(self):
        """List all players with custom weight configurations"""
        if not self.player_weights:
            print("ℹ️  No players with custom weights")
            return []
        
        print(f"\n👥 Players with custom weights ({len(self.player_weights)}):")
        for player in sorted(self.player_weights.keys()):
            print(f"  • {player}")
        
        return list(self.player_weights.keys())


# Singleton instance for easy access
_config_instance = None

def get_weight_config(project_root: Optional[Path] = None) -> WeightConfig:
    """Get or create the singleton WeightConfig instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = WeightConfig(project_root)
    return _config_instance


# Command-line interface
def main():
    """Command-line interface for weight management"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Manage factor analysis weights',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scripts/weight_config.py --show                    # Show global weights
  python src/scripts/weight_config.py --show --player "Ohtani"  # Show player weights
  python src/scripts/weight_config.py --list                    # List custom weights
  python src/scripts/weight_config.py --reset --player "Ohtani" # Reset player weights
        """
    )
    
    parser.add_argument('--show', action='store_true', help='Show weights')
    parser.add_argument('--list', action='store_true', help='List players with custom weights')
    parser.add_argument('--reset', action='store_true', help='Reset weights to defaults')
    parser.add_argument('--player', type=str, help='Specific player name')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    config = WeightConfig(project_root)
    
    if args.list:
        config.list_players_with_custom_weights()
    
    elif args.show:
        config.display_weights(args.player)
    
    elif args.reset:
        if args.player:
            config.reset_player_weights(args.player)
            config.save_player_weights()
        else:
            response = input("Reset ALL player weights? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                config.reset_all_player_weights()
                config.save_player_weights()
            else:
                print("Cancelled")
    
    else:
        # Default: show global weights
        config.display_weights()
        print("\n💡 Use --help for more options")


if __name__ == "__main__":
    main()
