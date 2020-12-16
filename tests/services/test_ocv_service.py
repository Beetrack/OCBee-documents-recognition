from numpy import ndarray
import cv2
import unittest
from app.services.ocv_service import OCVService


class OCVServiceTest(unittest.TestCase):

    def setUp(self):
        # we use a small image (128 px x 128 px) to enable faster testing instead of a full one
        self.img_dir = 'tests/img/small.png'
        self.img = cv2.imread(self.img_dir)
        self.service = OCVService()

    def tearDown(self):
        del self.service
        del self.img_dir
        del self.img
