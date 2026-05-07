import copy
import os

global FUZZ, file_name, args, output_file, dict_name
FUZZ = "qW3r7y_A5d_4sD_1234567890" 
FUZZING_TYPE = "White"
TARGET_LANGUAGE = "c"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "Test_examples")
OUT_DIR = os.path.join(BASE_DIR, "out")

file_name = os.path.join(TEST_DIR, 'divzero')

args = ['10', '0']

source_file = os.path.join(TEST_DIR, "divzero.c")

TARGET_HOST = "localhost"
TARGET_PORT = 1337
TIMEOUT = 5

output_file = os.path.join(BASE_DIR, 'output.txt')
dict_name = os.path.join(BASE_DIR, 'dict.txt')
Corpus_dir = OUT_DIR
Coverage_dir = OUT_DIR

os.makedirs(TEST_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
if TARGET_LANGUAGE == "go":
    os.makedirs(Coverage_dir, exist_ok=True)

NUM_THREADS = 8

ENABLE_COVERAGE_CACHING = True
COVERAGE_CACHE_SIZE = 10000
MUTATION_CACHE_SIZE = 10000
TESTING_CACHE_SIZE = 5000
BATCH_SIZE = 1
ADAPTIVE_MUTATION = True
COVERAGE_TIMEOUT = 1.0
TESTING_TIMEOUT = 1.0
FAST_MODE = True
SUPER_SPEED = True
SAFE_MODE = True
CACHE_AGGRESSIVELY = True
