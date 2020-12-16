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

    def test_gamma_return_type(self):
        # must return correctly with all of this cases
        self.assertTrue(type(self.service.adjust_gamma(self.img)) is ndarray)
        self.assertTrue(type(self.service.adjust_gamma(self.img, gamma=1)) is ndarray)
        self.assertTrue(type(self.service.adjust_gamma(self.img, gamma=1.1)) is ndarray)

    def test_gamma_args(self):
        # img type must be ndarray
        self.assertRaises(TypeError, self.service.adjust_gamma, '')

        # gamma must be greater that zero
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=0)
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=-1)
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=-2.1)

        # gamma can be float or int and nothing else
        self.assertRaises(TypeError, self.service.adjust_gamma, self.img, gamma='1')

