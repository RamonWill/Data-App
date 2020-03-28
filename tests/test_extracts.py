import os
import unittest
import sys
from collections import namedtuple
import pandas as pd

topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)

from Prescient.database_tools.Extracts import PositionSummary, PositionAccounting


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
        self.assertEqual(PositionSummary(self.new_trades_1).total_open_lots(), 50)
        self.assertEqual(PositionSummary(self.new_trades_2).total_open_lots(), -40)
        self.assertEqual(PositionSummary(self.new_trades_3).total_open_lots(), -32)
        self.assertEqual(PositionSummary(self.new_trades_4).total_open_lots(), 96)

    def test_average_cost(self):
        self.assertEqual(PositionSummary(self.new_trades_1).avg_cost(), 1905.2)
        self.assertEqual(PositionSummary(self.new_trades_2).avg_cost(), 142)
        self.assertEqual(PositionSummary(self.new_trades_3).avg_cost(), 57.2)
        self.assertEqual(PositionSummary(self.new_trades_4).avg_cost(), 29.7165625)

    def test_breakdown(self):
        result = [["2020-01-06", 20, 135],
                  ["2020-01-15", 70, 138.5714],
                  ["2020-01-17", 40, 140],
                  ["2020-01-21", -40, 142]]
        self.assertEqual(PositionSummary(self.new_trades_2).breakdown, result)


class PositionAccountingTests(unittest.TestCase):

    new_trades_2 = [Summary(*trade) for trade in trades_2]
    maxDiff = None
    # helper method
    def price_table(self):
        dates = ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09",
                 "2020-01-10", "2020-01-13", "2020-01-14", "2020-01-15",
                 "2020-01-16", "2020-01-17", "2020-01-20", "2020-01-21"]
        daily_prices = [145.65, 145.70, 145.40, 144.83,
                        144.62, 143.88, 145.20, 144.32,
                        145.12, 144.33, 143.56, 144.01]
        data = tuple(zip(dates, daily_prices))
        return data

        # DIS
    def test_position_performance(self):
        P = namedtuple("Pandas", ["date", "quantity", "avg_cost", "price", "pct_change"])
        perf = [["2020-01-06", 20.0, 135.0, 145.65, 7.889],
                ["2020-01-07", 20.0, 135.0, 145.70, 7.926],
                ["2020-01-08", 20.0, 135.0, 145.40, 7.704],
                ["2020-01-09", 20.0, 135.0, 144.83, 7.281],
                ["2020-01-10", 20.0, 135.0, 144.62, 7.126],
                ["2020-01-13", 20.0, 135.0, 143.88, 6.578],
                ["2020-01-14", 20.0, 135.0, 145.20, 7.556],
                ["2020-01-15", 70.0, 138.5714, 144.32, 4.148],
                ["2020-01-16", 70.0, 138.5714, 145.12, 4.726],
                ["2020-01-17", 40.0, 140.0, 144.33, 3.093],
                ["2020-01-20", 40.0, 140.0, 143.56, 2.543],
                ["2020-01-21", -40.0, 142.0, 144.01, -1.415]]
        data = [P(*day) for day in perf]
        prices = self.price_table()
        Performance = PositionAccounting(prices, self.new_trades_2)

        self.assertEqual(Performance.performance_table(), data)

    # using DIS
    def test_daily_valuation(self):
        mv = [["2020-01-06", 2913],
              ["2020-01-07", 2914],
              ["2020-01-08", 2908],
              ["2020-01-09", 2896.6],
              ["2020-01-10", 2892.4],
              ["2020-01-13", 2877.6],
              ["2020-01-14", 2904],
              ["2020-01-15", 10102.4],
              ["2020-01-16", 10158.4],
              ["2020-01-17", 5773.20],
              ["2020-01-20", 5742.4],
              ["2020-01-21", -5760.4]]
        mv = pd.DataFrame.from_records(mv, columns=["date", "market_val_DIS"])
        mv = mv.set_index("date")

        prices = self.price_table()
        Performance = PositionAccounting(prices, self.new_trades_2)
        pd.testing.assert_frame_equal(Performance.daily_valuations(), mv)


if __name__ == "__main__":
    unittest.main()
