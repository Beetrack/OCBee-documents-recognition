import cv2
import pytesseract
import numpy as np


class OCVServiceWrapper:

    @staticmethod
    def value_error_wrapper(error_keys: list):
        """Raises exception for value if the item does not have the min value expected

        Args:
             error_keys (list): tuple list (i.e.: [('gamma', 0)])
        """
        def _wrapper(func):
            def __wrapper(self, *args, **kwargs):
                for key in error_keys:
                    if key[0] in kwargs.keys() and kwargs[key[0]] <= key[1]:
                        raise ValueError(f'{key[0]} must be greater than {key[1]}.')
                return func(self, *args, **kwargs)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def adjust_gamma(self, image, gamma=1):
        """Builds a lookup table mapping the pixel values [0, 255] to their adjusted gamma values. Returns cv2 image"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    def _preprocess(self, image):
        """Noise cancelling"""
        image = cv2.medianBlur(image, 3)
        return 255 - image

    def _postprocess(self, image):
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return image

    def _get_block_index(self, image_shape, yx, block_size):
        """Helper function to generate 'box' coordinates"""
        y = np.arange(max(0, yx[0]-block_size), min(image_shape[0], yx[0]+block_size))
        x = np.arange(max(0, yx[1]-block_size), min(image_shape[1], yx[1]+block_size))
        return np.meshgrid(y, x)

    def _adaptive_median_threshold(self, img_in, delta):
        med = np.median(img_in)
        img_out = np.zeros_like(img_in)
        img_out[img_in - med < delta] = 255
        kernel = np.ones((3, 3), np.uint8)
        img_out = 255 - cv2.dilate(255 - img_out, kernel, iterations=2)
        return img_out

    def _block_image_process(self, image, block_size, delta):
        """
        Divides the image into local regions regions (blocks), and perform the `adaptive_mean_threshold(...)`
        function to each of the regions.
        """
        out_image = np.zeros_like(image)
        for row in range(0, image.shape[0], block_size):
            for col in range(0, image.shape[1], block_size):
                idx = (row, col)
                block_idx = self._get_block_index(image.shape, idx, block_size)
                out_image[tuple(block_idx)] = self._adaptive_median_threshold(image[tuple(block_idx)], delta)
        return out_image

    def process_image(self, img, block_size=80, delta=50):
        """Pipeline of segmenting into regions. Returns a cv2 image"""
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_in = self._preprocess(image_in)
        image_out = self._block_image_process(image_in, block_size, delta)
        image_out = self._postprocess(image_out)
        return image_out

    def _sigmoid(self, x, orig, rad):
        """Composing function to separate background"""
        k = np.exp((x - orig) * 5 / rad)
        return k / (k + 1.)

    def _combine_block(self, img_in, mask):
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
        lo = fimg_in[idx].min()
        hi = fimg_in[idx].max()
        v = fimg_in[idx] - lo
        r = hi - lo

        # Now we use good old OTSU binarization to get a rough estimation
        # of foreground and background regions.
        img_in_idx = img_in[idx]
        ret3, th3 = cv2.threshold(img_in[idx], 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # Then we normalize the stuffs and apply sigmoid to gradually
        # combine the stuffs.
        bound_value = np.min(img_in_idx[th3[:, 0] == 255])
        bound_value = (bound_value - lo) / (r + 1e-5)
        f = (v / (r + 1e-5))
        f = self._sigmoid(f, bound_value + 0.05, 0.2)

        # Finally, we re-normalize the result to the range [0..255]
        img_out[idx] = (255. * f).astype(np.uint8)
        return img_out

    def _combine_block_image_process(self, image, mask, block_size):
        """
        Combination routine on local blocks, so that the scaling parameters
        of Sigmoid function can be adjusted to local setting
        """
        out_image = np.zeros_like(image)
        for row in range(0, image.shape[0], block_size):
            for col in range(0, image.shape[1], block_size):
                idx = (row, col)
                block_idx = self._get_block_index(image.shape, idx, block_size)
                out_image[tuple(block_idx)] = self._combine_block(image[tuple(block_idx)], mask[tuple(block_idx)])
        return out_image

    def _combine_postprocess(self, image):
        return image

    def combine_process(self, img, mask):
        """Executes whole pipeline and returns a mask for the original image. Returns cv2 image"""
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_out = self._combine_block_image_process(image_in, mask, 20)
        image_out = self._combine_postprocess(image_out)
        return image_out

    def process(self, img_name, gamma=1, block_size=80, delta=50) -> str:
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
        mask = self.adjust_gamma(img, gamma=gamma)
        mask = self.process_image(mask, block_size=block_size, delta=delta)
        new_img = self.combine_process(img, mask)

        return pytesseract.image_to_string(new_img)
