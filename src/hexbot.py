# import numpy as np
from copy import deepcopy

adjacent = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, 1), (1, -1)]
n = 6

class CellGroup:

    def __init__(self, cells):
        self.cells = set(cells)
        self.hash_val = hash(tuple(sorted(cells, key=lambda x: x[0]+x[1]*100)))

    def __eq__(self, other) -> bool:
        return self.cells==other.cells
    
    def __hash__(self):
        return self.hash_val
    
    def adjacency(self):
        res = set()
        for cell in self.cells:
            adjacent_cells = adjacency(cell)
            res.update(c for c in adjacent_cells if c not in self.cells)
        return res
    
    def __repr__(self):
        str_cells = " ;".join([f"{c[0]}, {c[1]}" for c in self.cells])
        return f"Cells: {str_cells}"

class TopSide(CellGroup):

    def __init__(self):
        cells = [(-1, i) for i in range(n)]
        super().__init__(cells)

    def adjacency(self):
        return set((0, i) for i in range(n))
    
    def __repr__(self):
        return "Top Side"

class BottomSide(CellGroup):

    def __init__(self):
        cells = [(n, i) for i in range(n)]
        super().__init__(cells)

    def adjacency(self):
        return set((n-1, i) for i in range(n))

    def __repr__(self):
        return "Bot Side"


def merge_cellgroups(cellgroups):
    new_cells = set().union(*[gr.cells for gr in cellgroups])
    return CellGroup(new_cells)

def adjacency(cell):
    x, y = cell[0:2]
    res = [(x+dx, y+dy) for dx, dy in adjacent 
            if x+dx>-1 and y+dy>-2 and x+dx<n and y+dy<n+1]
    return res

def create_vc_map_from_cells(empty_cells, black_groups):
    """
    Create vc map and vsc map from cells.
    And populate using adjacency
    """
    special_cells = [el for el in [TopSide(), BottomSide()] if el in black_groups]
    total_groups = empty_cells.union(black_groups)
    vc_map = {gr: {gr2: [] for gr2 in total_groups } for gr in total_groups}
    vsc_map ={gr: {gr2: [] for gr2 in total_groups } for gr in total_groups}
    new_vc = {}
    for cell in vc_map.keys():
        adjacent_cells = cell.adjacency()
        for adj_cell in adjacent_cells:
            adj_cell_gr = CellGroup([adj_cell])
            if adj_cell_gr in vc_map[cell]:
                vc_map[cell][adj_cell_gr].append(set())
                ##
                new_vc.setdefault(cell, dict())
                new_vc[cell].setdefault(adj_cell_gr, [])
                new_vc[cell][adj_cell_gr].append(set())
    for special_cell in special_cells:
        adjacent_cells = special_cell.adjacency()
        adjacent_cells = [CellGroup([cell]) for cell in adjacent_cells]
        for adj_cell in adjacent_cells:
            if adj_cell in vc_map:
                vc_map[adj_cell][special_cell] = [set()]
                new_vc.setdefault(adj_cell, dict())
                new_vc[adj_cell].setdefault(special_cell, [])
                new_vc[adj_cell][special_cell].append(set())
    return vc_map, vsc_map, new_vc

def create_groups_from_empty_board(n):
    """
    Create cell groups and vc map for board size n
    """
    bottom_side = BottomSide()
    top_side = TopSide()
    empty_cells = set( CellGroup([(i, j)]) for i in range(n) for j in range(n))
    black_groups = {bottom_side, top_side}
    vc_map, vsc_map, new_vc = create_vc_map_from_cells(empty_cells, black_groups)
    return empty_cells, black_groups, vc_map, vsc_map, new_vc

def create_new_group_from_cell(cell, groups):
    """
    Merge one cell of B color with other groups if necessary 
    """
    adjacent_cells = cell.adjacency()
    old_groups = []
    for adj_cell in adjacent_cells:
        for gr in groups:
            if adj_cell in gr.cells and gr not in old_groups:
                old_groups.append(gr)
    if len(old_groups)>0:
        old_groups.append(cell)
        new_group = merge_cellgroups(old_groups)
        return new_group, old_groups
    else:
        return cell, old_groups

def merge_carriers(carrier_maps):
    """
    Merge carriers when uniting several B group.
    TODO: ensure unique and ensure minimal
    """
    res_map = dict()
    for carrier_map in carrier_maps:
        for cell, carriers in carrier_map.items():
            res_map.setdefault(cell, [])
            res_map[cell].extend(carriers)
    return res_map

def update_groups_and_VC(cell, empty_cells, black_groups, vc_map, vsc_map):
    """
    Update B groups, empty cells and maps when adding cell of B color
    """
    new_cell = CellGroup([cell])
    new_gr, old_groups = create_new_group_from_cell(new_cell, black_groups)
    ###
    empty_cells.remove(new_cell)
    black_groups.add(new_gr)
    for old_gr in old_groups:
        black_groups.discard(old_gr)
    ###
    old_vc_list = [vc_map.pop(old_gr) for old_gr in old_groups]
    ## move to function
    for old_vc in old_vc_list:
        for old_gr in old_groups:
            old_vc.pop(old_gr, None)
    new_vc = merge_carriers(old_vc_list)
    if len(new_vc):
        for gr, carrier_map in vc_map.items():
            for old_gr in old_groups:
                carrier_map.pop(old_gr, None)
            carrier_map[new_gr] = new_vc[gr]
        vc_map[new_gr] = new_vc
    return empty_cells, black_groups, vc_map, vsc_map

def update_cell_map(cell_map, cell_1, cell_2, carrier):
    """
    Update map with carriers using carrier. Ensures symmetry
    """
    cell_map.setdefault(cell_1, dict())
    cell_map[cell_1].setdefault(cell_2, [])
    if carrier not in cell_map[cell_1][cell_2]:
        cell_map[cell_1][cell_2].append(carrier)
    cell_map.setdefault(cell_2, dict())
    cell_map[cell_2].setdefault(cell_1, [])
    if carrier not in cell_map[cell_2][cell_1]:
        cell_map[cell_2][cell_1].append(carrier)
    return cell_map


def and_rule_and_update(cell_1, cell_2, cell_mid, carrier1, carrier2, black_groups, vc_map, vsc_map, new_vc_curr, verbose=True):
    cell_1_in_cr2 = cell_1.cells.intersection(carrier2) == set()
    cell_2_in_cr1 = cell_2.cells.intersection(carrier1) == set()
    carrier_intersection = carrier1.intersection(carrier2) == set()
    existing_vc = len(vc_map[cell_1][cell_2])>0
    # existing_vc = set() in vc_map[cell_1][cell_2]
    if not (cell_1_in_cr2 and cell_2_in_cr1 and carrier_intersection) or existing_vc:
        return 0, set()
    new_carrier = carrier1.union(carrier2)
    if verbose:
        print(f"1st cell: {cell_1}, 2nd cell: {cell_2}, mid cell: {cell_mid}")
        print(f"Carrier1: {carrier1}")
        print(f"Carrier2: {carrier2}")
    if cell_mid in black_groups:
        new_vc_curr = update_cell_map(new_vc_curr, cell_1, cell_2, new_carrier)
        if verbose:
            print(f"updated VC {new_carrier}")
        return 1, set()

    else:
        new_carrier = new_carrier.union(cell_mid.cells)
        vsc_map[cell_1][cell_2].append(new_carrier)
        if verbose:
            print(f"updated VSC {new_carrier}")
        return 2, new_carrier

def or_rule_and_update(vsc_carriers, carrier_union, carrier_intersection, verbose=False):
    new_vcs = []
    for carrier in vsc_carriers:
        new_uninon = carrier_union.union(carrier)
        new_intersec = carrier_intersection.intersection(carrier)

        if new_intersec == set():
            new_vcs.append(new_uninon)
        else:
            vsc_carriers_new = deepcopy(vsc_carriers)
            vsc_carriers_new.remove(carrier)
            res = or_rule_and_update(vsc_carriers_new, new_uninon, new_intersec)
            new_vcs.extend(res)
    return new_vcs



def H_search(empty_cells, black_groups, new_vc_map, vc_map, vsc_map, generations_num=1, verbose_cells=None):
    """
    H search. Iteratively searches for new Virtual connections
    """
    # check duplicates in vc_map
    # treat special cells , top and bootom separatly
    verbose_cells = [] if verbose_cells is None else verbose_cells
    ##
    all_cells = empty_cells.union(black_groups)
    special_cells = [TopSide(), BottomSide()]
    for i_gen in range(generations_num):
        new_vc_curr = dict()
        for cell_1, sub_map in new_vc_map.items():
            for cell_mid, carrier_list in sub_map.items():
                for carrier1 in carrier_list:
                    for cell_2 in all_cells:
                        # verb = all(cell_curr in verbose_cells for cell_curr in [cell_1, cell_2])
                        verb = False
                        if cell_1 == cell_2 or cell_1 == cell_mid or cell_2 == cell_mid or cell_mid in special_cells:
                            if verb:
                                print(f"1st cell: {cell_1}, 2nd cell: {cell_2}, mid cell: {cell_mid}")
                                print(f"continue")
                            continue
                        for carrier2 in vc_map[cell_2][cell_mid]:
                            
                            res, new_carrier = and_rule_and_update(cell_1, cell_2, cell_mid, carrier1, carrier2, black_groups, vc_map, vsc_map, new_vc_curr, verbose=verb)
         
                            if res == 2:
                                carriers_to_iterate = deepcopy(vsc_map[cell_1][cell_2])
                                carriers_to_iterate.remove(new_carrier)
                                new_vcs_or = or_rule_and_update(carriers_to_iterate, new_carrier, new_carrier)
                                if verb:
                                    print("Updated VC after or")
                                    print(new_vcs_or)
                                for new_vc_or in new_vcs_or:
                                    new_vc_curr = update_cell_map(new_vc_curr, cell_1, cell_2, new_vc_or)
        ###
        print("############ non symmetric")
        print(len(new_vc_curr))
        for c1, sub_map in new_vc_curr.items():
            for c2, carrier_list in sub_map.items():
                for carrier in carrier_list:
                    vc_map = update_cell_map(vc_map, c1, c2, carrier)
            # search
        new_vc_map = deepcopy(new_vc_curr)
    return vc_map, vsc_map







""" Move is made
0. by default have no or only basic vc.
Also create list with all cells (empty and ours + creating groups)
Do we need to store opponents cells?
1a. opponents move -> just remove from cells and remove from vc and vsc
end
1b. our move
1. update connected groups. update in vc_maps and vsc_maps
2. update all vc and vsc with current cell (with some depth)

Updating groups. first remove old groups and collect their carriers with other cells.
Rmove them in this dictionary.
Merge carriers. How to do? Save all them, todo: remove redundant
Insert new group with carriers
in other groups in dicts remove old, update new group

"""

"""
building vc
loop over all cells cell
loop over pair of cells (cell1, cell2)
try to apply and rule for cells

Q:how do we distinguish VC between empty cells and our cells?
"""


