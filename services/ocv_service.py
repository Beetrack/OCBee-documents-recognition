import cv2
import pytesseract
import nunmpy as np


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
                out_image[block_idx] = self._adaptive_median_threshold(image[block_idx], delta)
        return out_image

    def process_image(self, img, block_size=80, delta=50):
        """Pipeline of segmenting into regions. Returns a cv2 image"""
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_in = self._preprocess(image_in)
        image_out = self._block_image_process(image_in, block_size, delta)
        image_out = self._postprocess(image_out)
        return image_out
