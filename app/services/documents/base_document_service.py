# standard library imports
import re
from strsimpy.normalized_levenshtein import NormalizedLevenshtein


class BaseDocumentService:
    """
    A base class for common usage among the different supported documents with a common pipeline,
    which is cleaner, valid_text and process_text
    """

    # similarity method
    # can be changed in subclassing for specific differences
    SIM_METHOD = NormalizedLevenshtein()

    # patterns to make final clean
    PATTERNS = {}

    # keys to find and values to skip to get the corresponding
    # in the non-abstract class implementation fill with the
    # corresponding assumptions
    TO_FIND = {}

    def cleaner(self, text: str) -> list:
        """
        Cleans the recieved text from non desired characters

        Args:
            text (str): desired text to be cleaned

        Returns:
            list: list of the, apparent, separation of lines with the cleaning and reading
        """
        # normalize spaces and removes non standar characters
        text = re.sub(r'\s{2,}|[^\w\\\s.-]', '\n', text).upper()

        # removes unnecessary \ or other characters excepting \n
        text = re.sub(r'[^a-zA-Z0-9\s.-]', '', text)

        # split based on enter and filter of white spaces
        text_lines = map(lambda txt: txt.strip(), text.split('\n'))
        text_lines = list(filter(lambda txt: (txt != '') or (not re.match(r'\s*', txt)), text_lines))
        return text_lines

    def _valid_similarity(self, find: str, compare: str, threshold=0.75) -> bool:
        return self.SIM_METHOD.similarity(find, compare) >= threshold

    def _associate(self, text_list: list, threshold=0.75) -> dict:
        """Specific for each document reading implementation"""
        return dict()

    def _valid_association(self, associations: dict) -> bool:
        """Specific for each document reading implementation"""
        return False

    def _clean_processed_text(self, associations: dict) -> dict:
        """Specific for each document reading implementation"""
        return dict()

    def valid_text(self, text: str, threshold=0.75) -> bool:
        """
        Validates that a text has the specific document format and all the associations specified according
        to the specified document type (class) in use

        Args:
            text (str): text to validate
            threshold (optional)(int/float): threshold to use when validating the similarity of the search for key words

        Returns
            bool: True if text is valid accordind to specified document type, False otherwise
        """
        text_lines = self.cleaner(text)
        associations = self._associate(text_lines, threshold=threshold)
        return self._valid_association(associations)

    def process_text(self, text: str, threshold=0.75) -> dict:
        """
        Processes the desired text and formats it into a dictionary according to the specified
        document type (class) in use

        Args:
            text (str): text to validate
            threshold (optional)(int/float): threshold to use when validating the similarity of the search for key words

        Returns:
            dict: dictionary of document specified associations if valid text, None otherwise
        """
        text_lines = self.cleaner(text)
        associations = self._associate(text_lines, threshold=threshold)
        if self._valid_association(associations):
            return self._clean_processed_text(associations)
        return None
