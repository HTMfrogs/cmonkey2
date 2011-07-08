"""unit test module for cmonkey"""
import unittest
from datatypes import DataMatrix, DataMatrixCollection
from cmonkey import CMonkey, Membership, quantile, make_matrix

# setting up some simple dummy test input
# approximately 1 bicluster per 10 genes
NUM_GENES = 10
NUM_COLS = 2
GENE_NAMES = ['gene' + str(i) for i in range(NUM_GENES)]
COL_NAMES = ['cond' + str(i) for i in range(NUM_COLS)]
RATIOS = DataMatrix(NUM_GENES, NUM_COLS, GENE_NAMES, COL_NAMES)
RATIO_MATRICES = DataMatrixCollection([RATIOS])


class CMonkeyTest(unittest.TestCase):  # pylint: disable-msg=R0904
    """Test class for CMonkey"""

    def test_create_cmonkey(self):
        """create a CMonkey object"""
        cmonkey = CMonkey(RATIO_MATRICES)
        self.assertFalse(cmonkey.run_finished)
        self.assertEquals('hpy', cmonkey.configuration['organism'])

    def test_create_cmonkey_with_config(self):
        """create CMonkey object, specifying an organism"""
        config = {'organism': 'homo sapiens'}
        cmonkey = CMonkey(RATIO_MATRICES, config)
        self.assertFalse(cmonkey.run_finished)
        self.assertEquals('homo sapiens', cmonkey.configuration['organism'])

    def test_run_cmonkey_simple(self):
        """run CMonkey in the simplest way"""
        cmonkey = CMonkey(RATIO_MATRICES)
        cmonkey.run()
        self.assertTrue(cmonkey.run_finished)

    def test_make_matrix(self):
        """tests the make_matrix function"""
        matrix = make_matrix(["row1", "row2"], 3)
        self.assertEquals(2, len(matrix))
        self.assertEquals(3, len(matrix['row1']))
        self.assertEquals(0, matrix['row1'][0])

    def test_quantile(self):
        """tests the quantile function"""
        data = [1, 2, 3, 4, 5]
        self.assertEquals(1, quantile(data, 0))
        self.assertEquals(1.8, quantile(data, 0.2))
        self.assertEquals(2, quantile(data, 0.25))
        self.assertEquals(3, quantile(data, 0.5))
        self.assertEquals(4, quantile(data, 0.75))
        self.assertEquals(5, quantile(data, 1))


class MembershipTest(unittest.TestCase):  # pylint: disable-msg=R0904
    """Test class for Membership"""

    def test_map_to_is_member_matrix(self):
        """tests the map_to_is_member_matrix function"""
        in_matrix = [[1, 2], [2, 3]]
        out = Membership.map_to_is_member_matrix(in_matrix, 3)
        self.assertEquals([[True, False], [True, True], [False, True]], out)

if __name__ == '__main__':
    unittest.main()
