import numpy as np
from typing import Dict, List, Set, Tuple
from copy import deepcopy
import logging
import time

###
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

adjacent = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, 1), (1, -1)]
COL_INX = 100


class CellGroup:

    def __init__(self, cells: List[Tuple[int, int]], n):
        self.cells = set(cells)
        sorted_cells = sorted(cells, key=lambda x: x[0]+x[1]*COL_INX)
        self.hash_val = hash(tuple(sorted_cells))
        self.index = sorted_cells[0][0]+sorted_cells[0][1]*COL_INX
        self.n = n

    def __eq__(self, other) -> bool:
        return self.cells==other.cells
    
    def __hash__(self):
        return self.hash_val
    
    def adjacency(self):
        res = set()
        for cell in self.cells:
            adjacent_cells = adjacency(cell, self.n)
            res.update(c for c in adjacent_cells if c not in self.cells)
        return res
    
    def __repr__(self):
        str_cells = " ;".join([f"{c[0]}, {c[1]}" for c in self.cells])
        return f"Cells: {str_cells}"

class TopSide(CellGroup):

    def __init__(self, n: int):
        cells = [(-1, i) for i in range(n)]
        super().__init__(cells, n)

    def adjacency(self):
        return set((0, i) for i in range(self.n))
    
    def __repr__(self):
        return "Top Side"

class BottomSide(CellGroup):

    def __init__(self, n: int):
        cells = [(n, i) for i in range(n)]
        super().__init__(cells, n)

    def adjacency(self):
        return set((self.n-1, i) for i in range(self.n))

    def __repr__(self):
        return "Bot Side"

def update_cell_map(cell_map: Dict, cell_1: CellGroup, cell_2: CellGroup, carrier: Set):
    """
    Update map with carriers using carrier. Ensures symmetry
    """
    cell_map.setdefault(cell_1, dict())
    cell_map[cell_1].setdefault(cell_2, [])
    if not any(c.issubset(carrier) for c in cell_map[cell_1][cell_2]):
        cell_map[cell_1][cell_2].append(carrier)
    # second cell
    cell_map.setdefault(cell_2, dict())
    cell_map[cell_2].setdefault(cell_1, [])
    if not any(c.issubset(carrier) for c in cell_map[cell_2][cell_1]):
        cell_map[cell_2][cell_1].append(carrier)
    return cell_map

def check_and_update_subsets(old_sets: List, new_set: Set):
    new_sets = []
    keep_new = True
    for s in old_sets:
        if s==new_set:
            return old_sets
        if s.issubset(new_set):
            keep_new = False
        if not new_set.issubset(s):
            new_sets.append(s)
    if keep_new:
        new_sets.append(new_set)
    return new_sets

def merge_cellgroups(cellgroups: List[CellGroup]):
    new_cells = set().union(*[gr.cells for gr in cellgroups])
    return CellGroup(new_cells, n=cellgroups[0].n)

def adjacency(cell: Tuple[int, int], n):
    x, y = cell[0:2]
    res = [(x+dx, y+dy) for dx, dy in adjacent 
            if x+dx>-2 and y+dy>-1 and x+dx<n+1 and y+dy<n]
    return res


class BoardStateGroups:

    def __init__(self, n: int, **kwargs):
        self.n = n
        self.player_groups = set()
        self.empty_cells = set()
        self.opponent_groups = set()
        self.vc_map = dict() 
        self.vsc_map = dict()
        self.special_cells = list()
        self.resist_def = kwargs.get('resist_def', 1.2)
        self.max_depth_or = kwargs.get('max_depth_or', 5)
        self.max_carriers = kwargs.get('max_carriers', 100)
        self.presort = kwargs.get('presort', True)
        self.old_or = True
        
    def load_from_board(self, board_state: np.ndarray):
        assert len(board_state.shape) == 2
        assert board_state.shape[0] == board_state.shape[1]
        self.create_groups_form_board(board_state)
        self.create_vc_map_from_cells()

    def create_groups_form_board(self, board: np.ndarray):
        bottom_side = BottomSide(self.n)
        top_side = TopSide(self.n)
        self.player_groups = {bottom_side, top_side}
        for i in range(self.n):
            for j in range(self.n):
                if board[i][j] == 0:
                    self.empty_cells.add(CellGroup([(i,j)], self.n))
                elif board[i][j] == -1:
                    self.opponent_groups.add(CellGroup([(i,j)], self.n))
                elif board[i][j] == 1:
                    self.player_groups.add(CellGroup([(i,j)], self.n))
                else:
                    continue
        ### merge groups
        self.player_groups = self.merge_groups(self.player_groups)
        self.opponent_groups = self.merge_groups(self.opponent_groups)
        self.collect_special_cells()
        return 

    def collect_special_cells(self):
        cells = [c for c in self.player_groups if c.index<=self.n]
        self.special_cells = [min(cells, key=lambda x: x.index), max(cells, key=lambda x: x.index)]

    @staticmethod
    def merge_cell_and_group(cell: CellGroup, groups: Set[CellGroup]):
        """
        Merge one cell if necessary 
        """
        adjacent_cells = cell.adjacency()
        merged_groups = []
        for adj_cell in adjacent_cells:
            for gr in groups:
                if adj_cell in gr.cells and gr not in merged_groups:
                    merged_groups.append(gr)
        new_group = merge_cellgroups(merged_groups+[cell])
        return new_group, merged_groups

    @staticmethod
    def merge_groups(cell_groups: Set[CellGroup]):
        new_groups = set()
        for cell_gr in cell_groups:
            new_gr, merged_groups = BoardStateGroups.merge_cell_and_group(cell_gr, new_groups)
            new_groups.add(new_gr)
            for m_gr in merged_groups:
                new_groups.discard(m_gr)
        return new_groups

    def create_vc_for_adjacent(self, cell_gr: CellGroup):
        vcs = dict()
        adjacent_cells = cell_gr.adjacency()
        for adj_cell in adjacent_cells:
            adj_cell_gr = CellGroup([adj_cell], self.n)
            if adj_cell_gr in self.empty_cells and set() not in self.vc_map[cell_gr][adj_cell_gr]:
                self.vc_map[cell_gr][adj_cell_gr].append(set()) 
                self.vc_map[adj_cell_gr][cell_gr].append(set()) 
                vcs = update_cell_map(vcs, cell_gr, adj_cell_gr, set())
        return vcs
    
    def create_vc_map_from_cells(self):
        total_groups = self.empty_cells.union(self.player_groups)
        self.vc_map = {gr: {gr2: [] for gr2 in total_groups } for gr in total_groups}
        self.vsc_map = {gr: {gr2: [] for gr2 in total_groups } for gr in total_groups}
        for cell_gr in total_groups:
            _ = self.create_vc_for_adjacent(cell_gr)
        ##
        return None
    
    def remove_cell_from_maps(self, cell: CellGroup):
        self.vc_map.pop(cell)
        self.vsc_map.pop(cell)
        for sub_map in self.vc_map.values():
            sub_map.pop(cell)
        ##
        for sub_map in self.vsc_map.values():
            sub_map.pop(cell)
    
    def copy_state(self):
        """
        Method to copy everything from this state to other state
        """
        new_state = BoardStateGroups(self.n)
        new_state.empty_cells = deepcopy(self.empty_cells)
        new_state.player_groups = deepcopy(self.player_groups)
        new_state.opponent_groups = deepcopy(self.opponent_groups)
        new_state.vc_map = deepcopy(self.vc_map)
        new_state.vsc_map = deepcopy(self.vsc_map)
        return new_state
    
    def make_move(self, cell: Tuple[int, int], player: bool = True):
        cell_gr = CellGroup([cell], self.n)
        new_state = self.copy_state()
        ### remove cell from everywhere (check do we need to remove what it is our move?)
        new_state.empty_cells.discard(cell_gr)
        new_state.remove_cell_from_maps(cell_gr)
        ##
        if player:
            ### merge groups if needed
            new_group, merged_groups = BoardStateGroups.merge_cell_and_group(cell_gr, self.player_groups)
            new_state.collect_special_cells()
            # remove merged groups from all maps
            for m_gr in merged_groups:
                new_state.remove_cell_from_maps(m_gr)
            # add new group
            new_state.player_groups.add(new_group)
            new_state_total_groups = new_state.player_groups.union(new_state.empty_cells)
            new_state.vc_map[new_group] = {gr2: [] for gr2 in new_state_total_groups}
            new_state.vsc_map[new_group] = {gr2: [] for gr2 in new_state_total_groups}
            for c in new_state_total_groups:
                new_state.vc_map[c][new_group] = []
                new_state.vsc_map[c][new_group] = []
            new_vcs = new_state.create_vc_for_adjacent(new_group)
            
        else:
            new_group, merged_groups = BoardStateGroups.merge_cell_and_group(cell_gr, self.opponent_groups)
            for m_gr in merged_groups:
                new_state.opponent_groups.discard(m_gr)
            new_state.opponent_groups.add(new_group)
            new_vcs = dict()
       
        new_state.update_vc_map_carriers(cell, player)
        return new_state, new_vcs

    def update_vc_map_carriers(self, cell: Tuple[int, int], player: bool = True):
        cell_set = set()
        cell_set.add(cell)
        for c, sub_map in self.vsc_map.items():
            for c2, carriers_list in sub_map.items():
                self.vsc_map[c][c2] = [carrier for carrier in carriers_list if cell not in carrier]

        for c, sub_map in self.vc_map.items():
            for c2, carriers_list in sub_map.items():
                self.vc_map[c][c2] = [carrier for carrier in carriers_list if cell not in carrier]
                if not player:
                    self.vsc_map[c][c2].extend([carrier-cell_set for carrier in carriers_list if cell in carrier])
        return None

    def and_rule(self, cell_1: CellGroup, cell_2: CellGroup, cell_mid: CellGroup, 
                 carrier1: Set, carrier2: Set, new_vcs: Dict):
        cell_1_in_cr2 = cell_1.cells.intersection(carrier2) == set()
        cell_2_in_cr1 = cell_2.cells.intersection(carrier1) == set()
        carrier_intersection = carrier1.intersection(carrier2) == set()
        new_carrier = carrier1.union(carrier2)
        add_carriers = new_vcs.get(cell_1, dict()).get(cell_2, [])
        existing_vc = any(c.issubset(new_carrier) for c in self.vc_map[cell_1][cell_2]+add_carriers)
        if not (cell_1_in_cr2 and cell_2_in_cr1 and carrier_intersection) or existing_vc:
            return 0, set()
        if cell_mid in self.player_groups:
            return 1, new_carrier
        else:
            new_carrier = new_carrier.union(cell_mid.cells)
            existing_vsc = any(c.issubset(new_carrier) for c in self.vsc_map[cell_1][cell_2])
            if not existing_vsc:
                return 2, new_carrier
            else:
                return 0, set()

    def or_rule(self, vsc_carriers: List, carrier_union: Set, carrier_intersection: Set, current_depth: int):
        new_vcs = []
        if current_depth == 0:
            return []
        for carrier in vsc_carriers:
            new_union = carrier_union.union(carrier)
            new_intersec = carrier_intersection.intersection(carrier)
            if new_intersec == set():
                new_vcs = check_and_update_subsets(new_vcs, new_union)
            else:
                vsc_carriers_new = deepcopy(vsc_carriers)
                vsc_carriers_new.remove(carrier)
                res = self.or_rule(vsc_carriers_new, new_union, new_intersec, current_depth-1)
                for val in res:
                    new_vcs = check_and_update_subsets(new_vcs, val)
        return new_vcs

    def or_rule_v2(self, vsc_carriers: List, carrier_union: Set, carrier_intersection: Set, current_depth: int):
        ###  
        vsc_carriers = vsc_carriers[:self.max_carriers]
        new_vcs = []
        if current_depth == 0:
            return []
        candidates = [(carrier_union.union(c[0]), carrier_intersection.intersection(c[1])) for c in vsc_carriers]
        new_vcs = [cand[0] for cand in candidates if cand[1] == set()]
        candidates = [cand for cand in candidates if cand[1] != set()]
        for ix, cand in enumerate(candidates):
            cand_u, cand_intersec = cand
            res = self.or_rule_v2([c for c in candidates[ix+1:]], cand_u, cand_intersec, current_depth=current_depth-1)
            for val in res:
                new_vcs = check_and_update_subsets(new_vcs, val)

        return new_vcs

    def or_rule_v4(self, vsc_carriers: List, new_carrier: Set, max_depth: int, presort = False):
        if presort:
            intersections = [(c, len(c.intersection(new_carrier))) for c in vsc_carriers]
            intersections = sorted(intersections, key=lambda x: x[1])
            vsc_carriers = [c[0] for c in intersections]
        vsc_carriers = vsc_carriers[:self.max_carriers]
        ### iterative version
        new_vcs = []
        stack = [(new_carrier, new_carrier, 0, 0)]
        num_evals = 0
        while stack:
            carrier_union, carrier_intersec, depth, inx = stack.pop()
            if depth>=max_depth or inx>=len(vsc_carriers):
                continue
            num_evals+=1
            new_intersec = vsc_carriers[inx].intersection(carrier_intersec)
            new_union = vsc_carriers[inx].union(carrier_union)
            if new_intersec == set():
                new_vcs = check_and_update_subsets(new_vcs, new_union)
            else:
                stack.append((new_union, new_intersec, depth+1, inx+1))
            stack.append((carrier_union, carrier_intersec, depth, inx+1))
        return new_vcs


    def H_search(self, new_vc_map: Dict, generations_num: int = 1, verbose_cells=None):
        """
        H search. Iteratively searches for new Virtual connections
        """
        verbose_cells = [] if verbose_cells is None else verbose_cells
        ##
        all_cells = self.empty_cells.union(self.player_groups)
        for i_gen in range(generations_num):
            new_vc_curr = dict()
            logger.info(f'Generation {i_gen}')
            time_gen = time.time()
            max_time_or = (None, None, 0)
            for cell_1, sub_map in new_vc_map.items():
                for cell_mid, carrier_list in sub_map.items():
                    for carrier1 in carrier_list:
                        for cell_2 in all_cells:
                            verbose = all(cell_curr in verbose_cells for cell_curr in [cell_1, cell_2])
                            # verb = True
                            if cell_1 == cell_2 or cell_1 == cell_mid or cell_2 == cell_mid or cell_mid in self.special_cells:
                                continue
                            for carrier2 in self.vc_map[cell_2][cell_mid]:
                                res, new_carrier = self.and_rule(cell_1, cell_2, cell_mid, carrier1, carrier2, new_vc_curr)
                                if res == 1:
                                    if verbose:
                                        logger.debug(f"Found VC after and rule with {cell_1}, {cell_2} and carrier {new_carrier}")
                                        _ = input()
                                    new_vc_curr = update_cell_map(new_vc_curr, cell_1, cell_2, new_carrier)
                                if res == 2:
                                    if verbose:
                                        logger.debug(f"Found VSC after and rule with {cell_1}, {cell_2} and carrier {new_carrier}")
                                        _ = input()
                                    self.vsc_map = update_cell_map(self.vsc_map, cell_1, cell_2, new_carrier)
                                    carriers_to_iterate = deepcopy(self.vsc_map[cell_1][cell_2])
                                    carriers_to_iterate.remove(new_carrier)
                                    if self.old_or:
                                        carriers_to_iterate = [(c, c) for c in carriers_to_iterate]
                                        t_or_rule = time.time()
                                        new_vcs_or = self.or_rule_v2(carriers_to_iterate, new_carrier, new_carrier, self.max_depth_or)
                                        t_elapsed_or = time.time() - t_or_rule
                                    else:
                                        t_or_rule = time.time()
                                        new_vcs_or = self.or_rule_v4(carriers_to_iterate, new_carrier, self.max_depth_or, presort=self.presort)
                                        t_elapsed_or = time.time() - t_or_rule
   
                                    if t_elapsed_or >max_time_or[2]:
                                        max_time_or = (cell_1, cell_2, t_elapsed_or)
                                    if verbose:
                                        logger.debug("Updated VC after or with carriers:")
                                        logger.debug(new_vcs_or)
                                        logger.debug(f'Time elapsed: {t_elapsed_or}')
                                        _ = input()
                                    for new_vc_or in new_vcs_or:
                                        new_vc_curr = update_cell_map(new_vc_curr, cell_1, cell_2, new_vc_or)
            ###
            logger.info(f'{time.time() - time_gen} spent on generation {i_gen}')
            c1, c2, t11 = max_time_or
            logger.info(f'Max time or is {t11} for cells: {c1, c2}')
            if c1 is not None:
                logger.info(f'number of vsc: {len(self.vsc_map[c1][c2])}, combinations: {np.math.comb(min(len(self.vsc_map[c1][c2]), self.max_carriers), self.max_depth_or)}')
                logger.info(f"Number of new VCs: {len(new_vc_curr)}")
            for c1, sub_map in new_vc_curr.items():
                for c2, carrier_list in sub_map.items():
                    for carrier in carrier_list:
                        self.vc_map = update_cell_map(self.vc_map, c1, c2, carrier)
                # search
            new_vc_map = deepcopy(new_vc_curr)
        return new_vc_map

    def resistance_from_carriers(self, carriers: List):
        if set() in carriers:
            return 1.0
        else:
            return self.resist_def
    
    def create_adjacency_matrix(self):
        all_cells = self.empty_cells.union(self.player_groups)
        all_cells_l = sorted(list(all_cells), key=lambda x: x.index)
        all_cells_inx = {cell: ix for ix, cell in enumerate(all_cells_l)}
        adjacency_matrix = np.zeros((len(all_cells_l), len(all_cells_l)), dtype=float)
        for cell in all_cells_l:
            for cell_2, carriers in self.vc_map[cell].items():
                ix, jx = all_cells_inx[cell], all_cells_inx[cell_2]
                is_players_stone = any(c in self.player_groups for c in [cell, cell_2])
                coef = 0.5 if is_players_stone else 1.0
                if len(carriers) and not (adjacency_matrix[ix, jx]>0):
                    resist = self.resistance_from_carriers(carriers)
                    adjacency_matrix[ix, jx] = resist*coef
                    adjacency_matrix[jx, ix] = resist*coef

        return adjacency_matrix

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


"""
boardState

Bot:
algo, cache

make_move(state):
canonial_view = state.canonical_view()
inner_repr = repr(canonical_view)
new_move = algo(inner_repr, cache?)
"""




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


