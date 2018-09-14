# DINDIN Meryll
# June 04, 2018
# Dreem Headband Sleep Phases Classification Challenge

import argparse, warnings

from package.database import *

if __name__ == '__main__':

    warnings.simplefilter('ignore')

    # Initialize the arguments
    prs = argparse.ArgumentParser()
    # Mandatory arguments
    prs.add_argument('-f', '--folds', help='Number of folds for cross-validation', type=int, default=10)
    prs.add_argument('-t', '--threads', help='Number of concurrent threads', type=int, default=multiprocessing.cpu_count())
    # Parse the arguments
    prs = prs.parse_args()

    # Launch the datasets construction
    dtb = Database(threads=prs.threads)
    dtb.load_labels()
    dtb.unshift()
    dtb.add_norm_acc()
    dtb.add_norm_eeg()
    dtb.add_features()
    # dtb.add_betti_curves()
    # dtb.add_landscapes()
    dtb.build_series()
    dtb.rescale(size=500)
    dtb.build_cv(prs.folds)
