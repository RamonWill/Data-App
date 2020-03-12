import os
import unittest
import sys
from collections import namedtuple
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)

from Prescient import app, db
from Prescient.config import basedir
from Prescient.database_tools.Extracts import Portfolio_Summary, PositionSummary, PositionAccounting


# unit test
# trades_1 a single buy trade
# trades_2 user is long then sells position to go Short
# trades_3 user is short then reduces trade size
# trades_4 user is long and then increases trade size
Summary = namedtuple("Summary", ["ticker", "quantity", "price", "date"])
trades_1 = [('AMZN', 50, 1905.2, '2019-10-16')]
trades_2 = [('DIS', 20, 135.0, '2020-01-06'),
            ('DIS', 50, 140.0, '2020-01-15'),
            ('DIS', -30, 160.0, '2020-01-17'),
            ('DIS', -80, 142.0, '2020-01-21')]
trades_3 = [('KO', -85, 57.2, '2020-01-06'),
            ('KO', 53, 53.4, '2020-01-23')]
trades_4 = [('AAL', 10, 28.311, '2019-12-12'),
            ('AAL', 86, 29.88, '2020-02-06')]

class PositionSummaryTests(unittest.TestCase):

    new_trades_1 = [Summary(*trade) for trade in trades_1]
    new_trades_2 = [Summary(*trade) for trade in trades_2]
    new_trades_3 = [Summary(*trade) for trade in trades_3]
    new_trades_4 = [Summary(*trade) for trade in trades_4]

    def test_open_lots(self):
        self.assertEqual(PositionSummary(self.new_trades_1, "AMZN").total_open_lots(), 50)
        self.assertEqual(PositionSummary(self.new_trades_2, "DIS").total_open_lots(), -40)
        self.assertEqual(PositionSummary(self.new_trades_3, "KO").total_open_lots(), -32)
        self.assertEqual(PositionSummary(self.new_trades_4, "AAL").total_open_lots(), 96)

    def test_average_cost(self):
        self.assertEqual(PositionSummary(self.new_trades_1, "AMZN").avg_cost(), 1905.2)
        self.assertEqual(PositionSummary(self.new_trades_2, "DIS").avg_cost(), 142)
        self.assertEqual(PositionSummary(self.new_trades_3, "KO").avg_cost(), 57.2)
        self.assertEqual(PositionSummary(self.new_trades_4, "AAL").avg_cost(), 29.7165625)

    def test_breakdown(self):
        result = [["2020-01-06", 20, 135],
                  ["2020-01-15", 70, 138.5714],
                  ["2020-01-17", 40, 140],
                  ["2020-01-21", -40, 142]]
        self.assertEqual(PositionSummary(self.new_trades_2, "DIS").breakdown, result)


if __name__ == "__main__":
    unittest.main()
