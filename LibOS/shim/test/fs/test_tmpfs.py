#!/usr/bin/env python3

import os
import shutil

from regression import (
    HAS_SGX,
    RegressionTestCase,
    expectedFailureIf,
)

# Do tmpfs tests.
# pylint: disable=too-many-public-methods
class TC_10_Tmpfs(RegressionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.FILE_SIZES = [0, 1, 2, 15, 16, 17, 255, 256, 257, 1023, 1024, 1025, 65535, 65536, 65537,
                          1048575, 1048576, 1048577]
        cls.TEST_DIR = 'tmp'
        cls.INDEXES = range(len(cls.FILE_SIZES))
        cls.INPUT_DIR = os.path.join(cls.TEST_DIR, 'input')
        cls.INPUT_FILES = [os.path.join(cls.INPUT_DIR, str(x)) for x in cls.FILE_SIZES]
        cls.OUTPUT_DIR = os.path.abspath('/mnt-tmpfs')
        cls.OUTPUT_FILES = [os.path.join(cls.OUTPUT_DIR, str(x)) for x in cls.FILE_SIZES]

        # create directory structure and test files
        os.mkdir(cls.TEST_DIR)
        os.mkdir(cls.INPUT_DIR)
        for i in cls.INDEXES:
            with open(cls.INPUT_FILES[i], 'wb') as file:
                file.write(os.urandom(cls.FILE_SIZES[i]))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEST_DIR)

    def setUp(self):
        # clean output for each test
        shutil.rmtree(self.OUTPUT_DIR, ignore_errors=True)

    # copy input file to output dir (for tests that alter the file so input remains untouched)
    # pylint: disable=no-self-use
    def copy_input(self, input_path, output_path):
        shutil.copy(input_path, output_path)

    def verify_open_close(self, stdout, stderr, path, mode):
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('open(' + path + ') ' + mode + ' OK', stdout)
        self.assertIn('close(' + path + ') ' + mode + ' OK', stdout)
        self.assertIn('open(' + path + ') ' + mode + ' 1 OK', stdout)
        self.assertIn('open(' + path + ') ' + mode + ' 2 OK', stdout)
        self.assertIn('close(' + path + ') ' + mode + ' 1 OK', stdout)
        self.assertIn('close(' + path + ') ' + mode + ' 2 OK', stdout)
        self.assertIn('fopen(' + path + ') ' + mode + ' OK', stdout)
        self.assertIn('fclose(' + path + ') ' + mode + ' OK', stdout)
        self.assertIn('fopen(' + path + ') ' + mode + ' 1 OK', stdout)
        self.assertIn('fopen(' + path + ') ' + mode + ' 2 OK', stdout)
        self.assertIn('fclose(' + path + ') ' + mode + ' 1 OK', stdout)
        self.assertIn('fclose(' + path + ') ' + mode + ' 2 OK', stdout)

    def test_100_open_close(self):
        output_path = os.path.join(self.OUTPUT_DIR, 'test_100') # new file to be created
        stdout, stderr = self.run_binary(['open_close', 'W', output_path])
        self.verify_open_close(stdout, stderr, output_path, 'output')

    def verify_open_flags(self, stdout, stderr):
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('open(O_CREAT | O_EXCL | O_RDWR) [doesn\'t exist] succeeded as expected',
                      stdout)
        self.assertIn('open(O_CREAT | O_EXCL | O_RDWR) [exists] failed as expected', stdout)
        self.assertIn('open(O_CREAT | O_RDWR) [exists] succeeded as expected', stdout)
        self.assertIn('open(O_CREAT | O_RDWR) [doesn\'t exist] succeeded as expected', stdout)
        self.assertIn('open(O_CREAT | O_TRUNC | O_RDWR) [doesn\'t exist] succeeded as expected',
                      stdout)
        self.assertIn('open(O_CREAT | O_TRUNC | O_RDWR) [exists] succeeded as expected', stdout)

    def test_101_open_flags(self):
        file_path = os.path.join(self.OUTPUT_DIR, 'test_101') # new file to be created
        stdout, stderr = self.run_binary(['open_flags', file_path])
        self.verify_open_flags(stdout, stderr)

    def test_110_read_write(self):
        file_path = os.path.join(self.OUTPUT_DIR, 'test_110') # new file to be created
        stdout, stderr = self.run_binary(['read_write', file_path])
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('open(' + file_path + ') RW OK', stdout)
        self.assertIn('write(' + file_path + ') RW OK', stdout)
        self.assertIn('seek(' + file_path + ') RW OK', stdout)
        self.assertIn('read(' + file_path + ') RW OK', stdout)
        self.assertIn('compare(' + file_path + ') RW OK', stdout)
        self.assertIn('close(' + file_path + ') RW OK', stdout)

    def verify_seek_tell(self, stdout, stderr, input_path, output_path_1, output_path_2, size):
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('open(' + input_path + ') input OK', stdout)
        self.assertIn('seek(' + input_path + ') input start OK', stdout)
        self.assertIn('seek(' + input_path + ') input end OK', stdout)
        self.assertIn('tell(' + input_path + ') input end OK: ' + str(size), stdout)
        self.assertIn('seek(' + input_path + ') input rewind OK', stdout)
        self.assertIn('tell(' + input_path + ') input start OK: 0', stdout)
        self.assertIn('close(' + input_path + ') input OK', stdout)
        self.assertIn('fopen(' + input_path + ') input OK', stdout)
        self.assertIn('fseek(' + input_path + ') input start OK', stdout)
        self.assertIn('fseek(' + input_path + ') input end OK', stdout)
        self.assertIn('ftell(' + input_path + ') input end OK: ' + str(size), stdout)
        self.assertIn('fseek(' + input_path + ') input rewind OK', stdout)
        self.assertIn('ftell(' + input_path + ') input start OK: 0', stdout)
        self.assertIn('fclose(' + input_path + ') input OK', stdout)

        self.assertIn('open(' + output_path_1 + ') output OK', stdout)
        self.assertIn('seek(' + output_path_1 + ') output start OK', stdout)
        self.assertIn('seek(' + output_path_1 + ') output end OK', stdout)
        self.assertIn('tell(' + output_path_1 + ') output end OK: ' + str(size), stdout)
        self.assertIn('seek(' + output_path_1 + ') output end 2 OK', stdout)
        self.assertIn('seek(' + output_path_1 + ') output end 3 OK', stdout)
        self.assertIn('tell(' + output_path_1 + ') output end 2 OK: ' + str(size + 4098), stdout)
        self.assertIn('close(' + output_path_1 + ') output OK', stdout)
        self.assertIn('fopen(' + output_path_2 + ') output OK', stdout)
        self.assertIn('fseek(' + output_path_2 + ') output start OK', stdout)
        self.assertIn('fseek(' + output_path_2 + ') output end OK', stdout)
        self.assertIn('ftell(' + output_path_2 + ') output end OK: ' + str(size), stdout)
        self.assertIn('fseek(' + output_path_2 + ') output end 2 OK', stdout)
        self.assertIn('fseek(' + output_path_2 + ') output end 3 OK', stdout)
        self.assertIn('ftell(' + output_path_2 + ') output end 2 OK: ' + str(size + 4098), stdout)
        self.assertIn('fclose(' + output_path_2 + ') output OK', stdout)

    def test_115_seek_tell(self):
        input_path = self.INPUT_FILES[-1] # existing file
        output_path_1 = os.path.join(self.OUTPUT_DIR, 'test_115a') # writable files
        output_path_2 = os.path.join(self.OUTPUT_DIR, 'test_115b')
        stdout, stderr = self.run_binary(['seek_tell_tmpfs', input_path, output_path_1, output_path_2])
        self.verify_seek_tell(stdout, stderr, input_path, output_path_1, output_path_2,
                              self.FILE_SIZES[-1])        

    def test_120_file_delete(self):
        file_path = 'test_120'
        file_in = self.INPUT_FILES[-1] # existing file to be copied
        file_out_1 = os.path.join(self.OUTPUT_DIR, file_path + 'a')
        file_out_2 = os.path.join(self.OUTPUT_DIR, file_path + 'b')
        file_out_3 = os.path.join(self.OUTPUT_DIR, file_path + 'c')
        file_out_4 = os.path.join(self.OUTPUT_DIR, file_path + 'd')
        file_out_5 = os.path.join(self.OUTPUT_DIR, file_path + 'e')
        stdout, stderr = self.run_binary(['delete_tmpfs', file_in, file_out_1, file_out_2, file_out_3, file_out_4,
                                         file_out_5])
        # verify
        self.assertNotIn('ERROR: ', stderr)
        self.assertFalse(os.path.isfile(file_out_1))
        self.assertFalse(os.path.isfile(file_out_2))
        self.assertFalse(os.path.isfile(file_out_3))
        self.assertFalse(os.path.isfile(file_out_4))
        self.assertFalse(os.path.isfile(file_out_5))
        self.assertIn('unlink(' + file_out_1 + ') OK', stdout)
        self.assertIn('open(' + file_out_2 + ') input 1 OK', stdout)
        self.assertIn('close(' + file_out_2 + ') input 1 OK', stdout)
        self.assertIn('unlink(' + file_out_2 + ') input 1 OK', stdout)
        self.assertIn('open(' + file_out_3 + ') input 2 OK', stdout)
        self.assertIn('unlink(' + file_out_3 + ') input 2 OK', stdout)
        self.assertIn('close(' + file_out_3 + ') input 2 OK', stdout)
        self.assertIn('open(' + file_out_4 + ') output 1 OK', stdout)
        self.assertIn('close(' + file_out_4 + ') output 1 OK', stdout)
        self.assertIn('unlink(' + file_out_4 + ') output 1 OK', stdout)
        self.assertIn('open(' + file_out_5 + ') output 2 OK', stdout)
        self.assertIn('unlink(' + file_out_5 + ') output 2 OK', stdout)
        self.assertIn('close(' + file_out_5 + ') output 2 OK', stdout)

    # pylint: disable=too-many-arguments
    def verify_stat(self, stdout, stderr, input_path, output_path, size):
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('stat(' + input_path + ') input 1 OK', stdout)
        self.assertIn('open(' + input_path + ') input 2 OK', stdout)
        self.assertIn('stat(' + input_path + ') input 2 OK: ' + size, stdout)
        self.assertIn('fstat(' + input_path + ') input 2 OK: ' + size, stdout)
        self.assertIn('close(' + input_path + ') input 2 OK', stdout)

        self.assertIn('stat(' + output_path + ') output 1 OK', stdout)
        self.assertIn('open(' + output_path + ') output 2 OK', stdout)
        self.assertIn('stat(' + output_path + ') output 2 OK: ' + size, stdout)
        self.assertIn('fstat(' + output_path + ') output 2 OK: ' + size, stdout)
        self.assertIn('close(' + output_path + ') output 2 OK', stdout)

    def test_130_file_stat(self):
        # running for every file separately so the process doesn't need to enumerate directory
        # (different code path, enumeration also performs stat)
        for i in self.INDEXES:
            input_path = self.INPUT_FILES[i] # existing file
            output_path = self.OUTPUT_FILES[i] # file that will be opened in write mode
            size = str(self.FILE_SIZES[i])
            stdout, stderr = self.run_binary(['stat_tmpfs', input_path, output_path])
            self.verify_stat(stdout, stderr, input_path, output_path, size)

    def do_truncate_test(self, size_in, size_out):
        # prepare paths/files
        i = self.FILE_SIZES.index(size_in)
        input_path = self.INPUT_FILES[i] # source file to be truncated
        out_1_path = self.OUTPUT_FILES[i] + 'a'
        out_2_path = self.OUTPUT_FILES[i] + 'b'
        # run test
        stdout, stderr = self.run_binary(['truncate_tmpfs', input_path, out_1_path, out_2_path, str(size_out)])
        self.assertNotIn('ERROR: ', stderr)
        self.assertIn('truncate(' + out_1_path + ') to ' + str(size_out) + ' OK', stdout)
        self.assertIn('open(' + out_2_path + ') output OK', stdout)
        self.assertIn('ftruncate(' + out_2_path + ') to ' + str(size_out) + ' OK', stdout)
        self.assertIn('close(' + out_2_path + ') output OK', stdout)

    def test_140_file_truncate(self):
        self.do_truncate_test(0, 1)
        self.do_truncate_test(0, 16)
        self.do_truncate_test(0, 65537)
        self.do_truncate_test(1, 0)
        self.do_truncate_test(1, 17)
        self.do_truncate_test(16, 0)
        self.do_truncate_test(16, 1048576)
        self.do_truncate_test(255, 15)
        self.do_truncate_test(255, 256)
        self.do_truncate_test(65537, 65535)
        self.do_truncate_test(65537, 65536)

    def do_copy_test(self, executable, timeout):
        stdout, stderr = self.run_binary([executable, self.INPUT_DIR, self.OUTPUT_DIR],
                                         timeout=timeout)

    def test_200_copy_dir_whole(self):
        self.do_copy_test('copy_whole', 30)

    def test_201_copy_dir_seq(self):
        self.do_copy_test('copy_seq', 60)

    def test_202_copy_dir_rev(self):
        self.do_copy_test('copy_rev', 60)

    def test_203_copy_dir_sendfile(self):
        self.do_copy_test('copy_sendfile', 60)

    def test_210_copy_dir_mounted(self):
        executable = 'copy_whole'
        stdout, stderr = self.run_binary([executable, '/mounted/input', '/mnt-tmpfs'],
                                         timeout=30)
