import unittest

import guesser


class TestPreReqs(unittest.TestCase):
    pass


def create_test(case, func):
    def do_test_expected(self):
        self.assertLess(func(case), 8)

    return do_test_expected


def manipulations(cases, func):
    for case in cases:
        test_method = create_test(case, func)
        test_method.__name__ = f"test_{case}"
        setattr(TestPreReqs, test_method.__name__, test_method)


if __name__ == "__main__":
    all_cases = guesser.generate_variants()

    manipulations(list(all_cases)[:10], guesser.main)
    # log_file = "test_log_file.txt"
    # with open(log_file, "w") as f:
    #     runner = unittest.TextTestRunner(f, verbosity=2)
    #     unittest.main(testRunner=runner)
    unittest.main()
