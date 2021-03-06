import academictorrents as at
import unittest
import os
import shutil
import time
import sys


class AcademicTorrentsTestSuite(unittest.TestCase):
    """Test cases on the academictorrents.py file."""

    def test_absolute_truth_and_meaning(self):
        assert True

    def test_get_file_http(self):
        filename = at.get('55a8925a8d546b9ca47d309ab438b91f7959e77f')
        self.assertTrue(os.path.isfile(filename))

    def test_get_multiple_files(self):
        path = at.get('b79869ca12787166de88311ca1f28e3ebec12dec')
        files = os.listdir(path)
        self.assertTrue(len(files) == 174)

    def test_redownload_only_one_file(self):
        path = at.get('b79869ca12787166de88311ca1f28e3ebec12dec')  # test torrent
        files = os.listdir(path)
        self.assertTrue(len(files) == 174)
        datastore = os.getcwd() + "/datastore/"
        os.remove(datastore + "/BreastCancerCell_dataset/ytma55_030603_benign2.TIF")
        files = os.listdir(path)
        self.assertTrue(len(files) == 173)
        path = at.get('b79869ca12787166de88311ca1f28e3ebec12dec')  # test torrent
        files = os.listdir(path)
        self.assertTrue(len(files) == 174)

    def test_get_single_file(self):
        filename = at.get('323a0048d87ca79b68f12a6350a57776b6a3b7fb')
        self.assertTrue(os.path.isfile(filename))

    def test_find_downloaded_torrent(self):
        filename = at.get('323a0048d87ca79b68f12a6350a57776b6a3b7fb')
        self.assertTrue(os.path.isfile(filename))

    # Test with different datastore
    def test_different_datastore(self):
        filename = at.get('323a0048d87ca79b68f12a6350a57776b6a3b7fb', datastore=os.getcwd() + '/datastore/alt/')
        assert filename == os.getcwd() + '/datastore/alt/mnist.pkl.gz'
        self.assertTrue(os.path.isfile(filename))


if __name__ == '__main__':
    unittest.main()
