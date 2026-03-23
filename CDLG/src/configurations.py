import os

# Default directories
DEFAULT_OUTPUT_DIR = os.path.join('output')
DEFAULT_PARAMETER_DIR = os.path.join('CDLG/src/input_parameters/')
PARAMETER_NAME = 'Simple_2'
# First time stamp of each event log
FIRST_TIMESTAMP = '2024/01/01 08:00:00'
# Incremental evolution parameters for incremental drifts
INCREMENTAL_EVOLUTION_SCOPE = [0.05, 0.10]
# Use multiprocessing with specified number of CPUs (if N_CORES = None, then cpu_count()-2 is used
MULTIPROCESSING = False
N_CORES = None