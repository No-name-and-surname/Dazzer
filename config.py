import copy
import os

global FUZZ, file_name, args, output_file, dict_name

FUZZ = "qW3r7y_A5d_4sD_1234567890" 
FUZZING_TYPE = "White" # Black/White/Gray

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "Test_examples")
OUT_DIR = os.path.join(BASE_DIR, "out")

#Path to target file
file_name = os.path.join(TEST_DIR, 'cov_test')

#Fuzzing arguments
args = ['1', '1']

#White Box
source_file = os.path.join(TEST_DIR, "cov_test.c")

#Black Box
TARGET_HOST = "localhost"
TARGET_PORT = 1337
TIMEOUT = 5

#Results saving
output_file = 'output.txt'
dict_name = 'dict.txt'
Corpus_dir = OUT_DIR

# Create directories if they don't exist
os.makedirs(TEST_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# Multithreading settings
NUM_THREADS = 3

