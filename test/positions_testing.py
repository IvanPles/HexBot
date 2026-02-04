from src.hexbot import BoardStateGroups, CellGroup
from src.board import BoardState
import time
import numpy as np
from copy import deepcopy
from typing import Dict, List, Set, Tuple

def make_moves(n: int, moves: List, moves_opponent: List):
    board_state = BoardState(np.zeros((n,n), dtype=int))
    for m in moves:
        board_state.make_move(m, player=True)
    for m in moves_opponent:
        board_state.make_move(m, player=False)
    bsg = BoardStateGroups(n=n)
    bsg.load_from_board(board_state.state)
    return bsg

def find_vc(board_state: BoardStateGroups, test_cells: List[CellGroup], max_generations: int):
    """"""
    """"""
    new_vc = deepcopy(board_state.vc_map)
    assert len(test_cells)==2, 'Need exactly 2 cells for test'
    cell_1, cell_2 = test_cells[0], test_cells[1]
    found_carriers = []
    start_time = time.time()
    for i_gen in range(max_generations):
        new_vc_curr = board_state.H_search(new_vc, generations_num=1)
        if len(board_state.vc_map[cell_1][cell_2]):
            elapsed_time = time.time()-start_time
            print(f'Found VC for {cell_1}, {cell_2} on generation {i_gen}')
            print(f'Carriers: {board_state.vc_map[cell_1][cell_2]}')
            found_carriers = board_state.vc_map[cell_1][cell_2]
            break
        new_vc = new_vc_curr
    if not len(found_carriers):
        elapsed_time = time.time()-start_time
        print(f'No VC is found for {cell_1}, {cell_2} after {max_generations} generations')
    return found_carriers, elapsed_time
    
