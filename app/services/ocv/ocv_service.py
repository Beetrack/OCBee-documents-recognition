"""
Service to provide a wrapper around OCV that returns the read strings from an image
"""
# pylint: disable=no-member
import cv2
import pytesseract
import numpy as np


class OCVServiceWrappers:
    """
    Class to wrap and raise errors of OCVService and make it mor rebust
    """

    @staticmethod
    def value_error_wrapper(error_keys: list):
        """Raises exception for value if the item does not have the min value expected

        Args:
             error_keys (list): tuple list (i.e.: [('gamma', 0)])
        """
        def _wrapper(func):
            def __wrapper(*args, **kwargs):
                for key in error_keys:
                    if key[0] in kwargs.keys() and kwargs[key[0]] <= key[1]:
                        raise ValueError(f'{key[0]} must be greater than {key[1]}.')
                return func(*args, **kwargs)
            return __wrapper
        return _wrapper

    @staticmethod
    def type_error_wrapper(error_keys: list):
        """Raises exception for value if the item is not of the specified type

        Args:
             error_keys (list): tuple list (i.e.: [('gamma', 0)])
        """
        def _wrapper(func):
            def __wrapper(*args, **kwargs):
                for key in error_keys:
                    if key[0] in kwargs.keys() and not isinstance(kwargs[key[0]], key[1]):
                        raise TypeError(f'{key[0]} must be of type {key[1]}.')
                return func(*args, **kwargs)
            return __wrapper
        return _wrapper


class OCVService:
    """
    A class service to wrap a Open Computer Vision with Tesseract to analyze the text of images

    Original form: https://stackoverflow.com/a/57103789

    Public methods:
        adjust_gamma(image, gamma=1): Builds a lookup table mapping the pixel values [0, 255] to their adjusted gamma
        process_image(img, block_size=80, delta=50): Pipeline of segmenting into regions
        combine_process(img, mask): Executes whole pipeline and returns a mask for the original image
        process(img_name, gamma=1, block_size=80, delta=50): Processes the image with an 'adaptive binarization'
    """

    @staticmethod
    @OCVServiceWrappers.type_error_wrapper([
        ('image', type(np.ndarray)), ('gamma', (int, float))
    ])
    @OCVServiceWrappers.value_error_wrapper([
        ('gamma', 0)
    ])
    def adjust_gamma(image, gamma=1):
        """Builds a lookup table mapping the pixel values [0, 255] to their adjusted gamma values. Returns cv2 image"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    @staticmethod
    def _preprocess(image):
        """Noise cancelling"""
        image = cv2.medianBlur(image, 3)
        return 255 - image

    @staticmethod
    def _postprocess(image):
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return image

    @staticmethod
    def _get_block_index(image_shape, _yx, block_size):
        """Helper function to generate 'box' coordinates"""
        __y = np.arange(max(0, _yx[0]-block_size), min(image_shape[0], _yx[0]+block_size))
        __x = np.arange(max(0, _yx[1]-block_size), min(image_shape[1], _yx[1]+block_size))
        return np.meshgrid(__y, __x)

    @staticmethod
    def _adaptive_median_threshold(img_in, delta):
        med = np.median(img_in)
        img_out = np.zeros_like(img_in)
        img_out[img_in - med < delta] = 255
        kernel = np.ones((3, 3), np.uint8)
        img_out = 255 - cv2.dilate(255 - img_out, kernel, iterations=2)
        return img_out

    @staticmethod
    def _block_image_process(image, block_size, delta):
        """
        Divides the image into local regions regions (blocks), and perform the `adaptive_mean_threshold(...)`
        function to each of the regions.
        """
        out_image = np.zeros_like(image)
        for row in range(0, image.shape[0], block_size):
            for col in range(0, image.shape[1], block_size):
                idx = (row, col)
                block_idx = OCVService._get_block_index(image.shape, idx, block_size)
                out_image[tuple(block_idx)] = OCVService._adaptive_median_threshold(image[tuple(block_idx)], delta)
        return out_image

    @staticmethod
    @OCVServiceWrappers.type_error_wrapper([
        ('image', type(np.ndarray)), ('block_size', int), ('delta', (int, float))
    ])
    @OCVServiceWrappers.value_error_wrapper([
        ('block_size', 0), ('delta', 0)
    ])
    def process_image(img, block_size=80, delta=50):
        """Pipeline of segmenting into regions. Returns a cv2 image"""
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_in = OCVService._preprocess(image_in)
        image_out = OCVService._block_image_process(image_in, block_size, delta)
        image_out = OCVService._postprocess(image_out)
        return image_out

    @staticmethod
    def _sigmoid(__x, orig, rad):
        """Composing function to separate background"""
        __k = np.exp((__x - orig) * 5 / rad)
        return __k / (__k + 1.)

    @staticmethod
    def _combine_block(img_in, mask):
        """Combines all the local blocks into one image."""
        # First, we pre-fill the masked region of img_out to white
        # (i.e. background). The mask is retrieved from previous section.
        img_out = np.zeros_like(img_in)
        img_out[mask == 255] = 255
        fimg_in = img_in.astype(np.float32)

        # Then, we store the foreground (letters written with ink)
        # in the `idx` array. If there are none (i.e. just background),
        # we move on to the next block.
        idx = np.where(mask == 0)
        if idx[0].shape[0] == 0:
            img_out[idx] = img_in[idx]
            return img_out

        # We find the intensity range of our pixels in this local part
        # and clip the image block to that range, locally.
        _lo = fimg_in[idx].min()
        _hi = fimg_in[idx].max()
        __v = fimg_in[idx] - _lo
        __r = _hi - _lo

        # Now we use good old OTSU binarization to get a rough estimation
        # of foreground and background regions.
        img_in_idx = img_in[idx]
        _, th3 = cv2.threshold(img_in[idx], 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # Then we normalize the stuffs and apply sigmoid to gradually
        # combine the stuffs.
        bound_value = np.min(img_in_idx[th3[:, 0] == 255])
        bound_value = (bound_value - _lo) / (__r + 1e-5)
        __f = (__v / (__r + 1e-5))
        __f = OCVService._sigmoid(__f, bound_value + 0.05, 0.2)

        # Finally, we re-normalize the result to the range [0..255]
        img_out[idx] = (255. * __f).astype(np.uint8)
        return img_out

    @staticmethod
    def _combine_block_image_process(image, mask, block_size):
        """
        Combination routine on local blocks, so that the scaling parameters
        of Sigmoid function can be adjusted to local setting
        """
        out_image = np.zeros_like(image)
        for row in range(0, image.shape[0], block_size):
            for col in range(0, image.shape[1], block_size):
                idx = (row, col)
                block_idx = OCVService._get_block_index(image.shape, idx, block_size)
                out_image[tuple(block_idx)] = OCVService._combine_block(image[tuple(block_idx)], mask[tuple(block_idx)])
        return out_image

    @staticmethod
    def _combine_postprocess(image):
        return image

    @staticmethod
    @OCVServiceWrappers.type_error_wrapper([
        ('image', type(np.ndarray)), ('mask', type(np.ndarray))
    ])
    def combine_process(image, mask):
        """Executes whole pipeline and returns a mask for the original image. Returns cv2 image"""
        image_in = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_out = OCVService._combine_block_image_process(image_in, mask, 20)
        image_out = OCVService._combine_postprocess(image_out)
        return image_out

    @staticmethod
    @OCVServiceWrappers.type_error_wrapper([
        ('img_name', str), ('gamma', (int, float)), ('block_size', int), ('delta', (int, float))
    ])
    @OCVServiceWrappers.value_error_wrapper([
        ('gamma', 0), ('block_size', 0), ('delta', 0)
    ])
    def process(img_name, gamma=1, block_size=80, delta=50) -> str:
        """Processes the image with an 'adaptive binarization' to extract the text in it

        Args:
            img_name (str): The name of the image containing the file
            gamma (float):  Gamma correction to be applied to the image
            block_size (int): Size of blocks to divide the image with. The trick is to choose its size
                              large enough so that you still get a large chunk of text and background
                              (i.e. larger than any symbols that you have), but small enough to not suffer
                              from any lightening condition variations (i.e. 'large, but still local')
            delta (int): Threshold of 'how far away from median we will still consider it as background?'

        Returns:
            string: a string of the processed text and what it is being identified in the image
        """

        img = cv2.imread(img_name)
        mask = OCVService.adjust_gamma(img, gamma=gamma)
        mask = OCVService.process_image(mask, block_size=block_size, delta=delta)
        new_img = OCVService.combine_process(img, mask)

        return pytesseract.image_to_string(new_img)
