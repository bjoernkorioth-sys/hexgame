# turn_manager.py
class TurnManager:
    def __init__(self, num_players, units_per_player):
        self.num_players = num_players
        self.units_per_player = units_per_player
        self.current_player = 0
        self.phase = "setup"  # can be "setup" or "play"
        self.units_placed = [0] * num_players

    def next_turn(self):
        """Advance to the next player's turn, switching phase if setup is complete."""
        self.current_player = (self.current_player + 1) % self.num_players

        # Check if setup phase is complete
        if self.phase == "setup":
            if all(u == self.units_per_player for u in self.units_placed):
                self.phase = "play"

    def can_place_unit(self, player_id):
        """Return True if the player can still place units during setup."""
        return (
            self.phase == "setup"
            and self.units_placed[player_id] < self.units_per_player
        )

    def record_placement(self, player_id):
        """Count one placed unit for the player."""
        if self.phase == "setup":
            self.units_placed[player_id] += 1
