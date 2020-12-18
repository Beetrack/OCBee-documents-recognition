from app.services.documents.base_document_service import BaseDocumentService


class BasicService(BaseDocumentService):

    TO_FIND = {
        'interpreted': 0
    }

    def _associate(self, text_list: list, threshold=0.75) -> dict:
        return {txt: text_list for txt in self.TO_FIND}

    def _valid_association(self, associations: dict) -> bool:
        return True

    def _clean_processed_text(self, associations: dict) -> dict:
        return associations
