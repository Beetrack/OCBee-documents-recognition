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

    def test_process_image_return_type(self):
        # must return correctly with all of this cases
        self.assertTrue(type(self.service.process_image(self.img)) is ndarray)
        self.assertTrue(type(self.service.process_image(self.img, block_size=10)) is ndarray)
        self.assertTrue(type(self.service.process_image(self.img, delta=1)) is ndarray)
        self.assertTrue(type(self.service.process_image(self.img, delta=1.1)) is ndarray)
        self.assertTrue(type(self.service.process_image(self.img, block_size=15, delta=1.1)) is ndarray)

    def test_process_image_args(self):
        # img type must be ndarray
        self.assertRaises(TypeError, self.service.process_image, '')

        # block_size must be greater than zero
        self.assertRaises(ValueError, self.service.process_image, self.img, block_size=0)
        self.assertRaises(ValueError, self.service.process_image, self.img, block_size=-1)

        # block_size must be an integer
        self.assertRaises(TypeError, self.service.process_image, self.img, block_size=1.1)
        self.assertRaises(TypeError, self.service.process_image, self.img, block_size='')

        # delta amust be greater than zero
        self.assertRaises(ValueError, self.service.process_image, self.img, delta=0)
        self.assertRaises(ValueError, self.service.process_image, self.img, delta=-1)

        # delta must be float or integer
        self.assertRaises(TypeError, self.service.process_image, self.img, delta='')

    def test_combine_process_return_type(self):
        mask = self.service.adjust_gamma(self.img)
        mask = self.service.process_image(mask)

        # must return correct type
        self.assertTrue(type(self.service.combine_process(self.img, mask)) is ndarray)

    def test_combine_process_args(self):
        # img type must be ndarray
        self.assertRaises(TypeError, self.service.combine_process, '', self.img)

        # mask type must be ndarray
        self.assertRaises(TypeError, self.service.combine_process, self.img, '')

    def test_process_return_type(self):
        # must return correct type
        self.assertTrue(type(self.service.process(self.img_dir)) is str)
        self.assertTrue(type(self.service.process(self.img_dir, block_size=15)) is str)
        self.assertTrue(type(self.service.process(self.img_dir, delta=10)) is str)
        self.assertTrue(type(self.service.process(self.img_dir, gamma=15.1)) is str)
        self.assertTrue(type(self.service.process(self.img_dir, block_size=15, delta=10, gamma=200)) is str)

    def test_process_args(self):
        # img_name must be string
        self.assertRaises(SystemError, self.service.process, self.img)

        # img must be a valid directory
        self.assertRaises(cv2.error, self.service.process, '')

        # block_size must be greater than zero
        self.assertRaises(ValueError, self.service.process, self.img_dir, block_size=0)
        self.assertRaises(ValueError, self.service.process, self.img_dir, block_size=-1)

        # block_size must be an integer
        self.assertRaises(TypeError, self.service.process, self.img_dir, block_size=1.1)
        self.assertRaises(TypeError, self.service.process, self.img_dir, block_size='')

        # delta amust be greater than zero
        self.assertRaises(ValueError, self.service.process, self.img_dir, delta=0)
        self.assertRaises(ValueError, self.service.process, self.img_dir, delta=-1)

        # delta must be float or integer
        self.assertRaises(TypeError, self.service.process, self.img_dir, delta='')

        # gamma must be greater that zero
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=0)
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=-1)
        self.assertRaises(ValueError, self.service.adjust_gamma, self.img, gamma=-2.1)

        # gamma can be float or int and nothing else
        self.assertRaises(TypeError, self.service.adjust_gamma, self.img, gamma='1')