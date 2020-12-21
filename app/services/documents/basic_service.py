"""
Basic Service module that returns all the read information in a clean format
"""
from app.services.documents.base_document_service import BaseDocumentService


class BasicService(BaseDocumentService):
    """
    Basic: general image analysis for non implemented documents
    """

    TO_FIND = {
        'interpreted': 0
    }

    def _associate(self, text_list: list, threshold=0.75) -> dict:
        """
        Returns: dict: all information associated with the interpretation
        """
        return {txt: text_list for txt in self.TO_FIND}

    def _valid_association(self, associations: dict) -> bool:
        """Returns: True: as no association is really made"""
        return True

    def _clean_processed_text(self, associations: dict) -> dict:
        """
        Returns: dict: made association with simple interpretation and cleaning
        """
        return associations
