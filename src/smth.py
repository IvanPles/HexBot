import numpy as np
from hexbot import *

n = 6
board = np.zeros((n,n))

empty_cells, b_cells, vc_map, vsc_map, new_vc = create_groups_from_empty_board(n)
# print("EMPTY")
# print(b_cells)
# print(empty_cells)

i, j = 2,3
board[i, j] = 1
i2, j2 = 3, 3
board[i2, j2] = 1

# vc_map, vsc_map = H_search(empty_cells, b_cells, new_vc, vc_map, vsc_map, generations_num=2)
# test_cell = CellGroup([(1,3)])
# test_cell2 = CellGroup([(2,1)])

#print(f"For cell {test_cell}")
#print("VC map")
#print(vc_map[test_cell])
#print("VSC")
#print(vsc_map[test_cell])
#print("additional")
#print(vc_map[test_cell2][test_cell])
#print(vc_map[test_cell][test_cell2])
#print("!!!")

#empty_cells, b_cells, vc_map, vsc_map = update_groups_and_VC((i, j), empty_cells, b_cells, vc_map, vsc_map)
#print("ADD one")
#print(b_cells)
#test_cell = CellGroup([(1,3)])
#print(vc_map[test_cell])
#
###
#empty_cells, b_cells, vc_map, vsc_map = update_groups_and_VC((i2, j2),empty_cells, b_cells, vc_map, vsc_map)
#print("ADD second")
#print(b_cells)
#print(vc_map[test_cell])

empty_cells = set( CellGroup([(0, i)]) for i in range(4))
for i in range(3):
    empty_cells.add(CellGroup([(1,i)]))
empty_cells.add(CellGroup([(2, 0)]))

test_cell = CellGroup([(2, 1)])
# empty_cells.add(test_cell)
# b_cells = set([TopSide()])
b_cells = set([test_cell] )
b_cells.add(TopSide())

vc_map, vsc_map, new_vc = create_vc_map_from_cells(empty_cells, b_cells)
# new_vc = [el for el in new_vc if el[0]==test_cell or el[1]==test_cell]

###
verbose_cells = [TopSide(), test_cell]

vc_map, vsc_map = H_search(empty_cells, b_cells, new_vc, vc_map, vsc_map, generations_num=3, verbose_cells=verbose_cells)
other_cell = CellGroup([(2,0)])

carriers = vc_map[other_cell][TopSide()]
for ix, s1 in enumerate(carriers):
    for jx, s2 in enumerate(carriers):
        if ix != jx:
            print(s1)
            print(s2)
            print(s1.intersection(s2) == s1)

for cell in vc_map:
    print(cell)
    print(vc_map[cell])

