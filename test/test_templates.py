import sys
sys.path.append('..')
from positions_testing import make_moves, find_vc
from src.hexbot import BoardStateGroups
from src.hexbot import CellGroup



cases = ((10, [], [], ('Top side', (2, 0)), 8),)


if __name__ == '__main__':
    for case in cases:
        print(case)
        n, moves, op_moves, cells, max_gen = case
        board_state = make_moves(n, moves, op_moves)
        mapping_name = {'Top side': board_state.special_cells[0],
                        'Bot side': board_state.special_cells[1]}
        cells = [mapping_name[c] if c in mapping_name else CellGroup([c], n)
                 for c in cells]
        res = find_vc(board_state, cells, max_generations=max_gen)
        print(f'Elapsed time: {res[1]}')
    
