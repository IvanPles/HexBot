import unittest
from hexbot import *

class TestTemplates(unittest.TestCase):
    def test_template_1(self):
        # construcing template
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

        vc_map, vsc_map = H_search(empty_cells, b_cells, new_vc, vc_map, vsc_map,
                                   generations_num=3, verbose_cells=verbose_cells)
        carriers = vc_map[test_cell][TopSide()]
        expected_carriers = [set()]
        for c in empty_cells:
            expected_carriers[0] = expected_carriers[0].union(c.cells)
        self.assertListEqual(carriers, expected_carriers)

       
if __name__ == "__main__":
    unittest.main()
