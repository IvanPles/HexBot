import numpy as np


adjacency = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, 1), (1, -1)]

class BoardState:

    def __init__(self, board_state, move=True):
        self.state = board_state
        self.move = move # move order True - black, False - white
    
    def make_move(self, coords: tuple[int, int]):

        new_state = self.state.copy()
        if self.move:
            new_state[coords[0], coords[1]] = 1
        else:
            new_state[coords[0], coords[1]] = -1

        return BoardState(new_state, move = not self.move)

    def canonical_view(self):
        """
        Returns canonical view of board as if first player
        """
        if self.move:
            return self.state
        else:
            return -1*self.state.T
    





