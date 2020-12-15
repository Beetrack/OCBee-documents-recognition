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
