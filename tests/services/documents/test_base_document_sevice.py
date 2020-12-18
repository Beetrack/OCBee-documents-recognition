import pytest

from app.services.documents.base_document_service import BaseDocumentService

base_doc_service = BaseDocumentService()

def test_cleaner_return_type():
    assert type(base_doc_service.cleaner('')) == list

def test__valid_similarity_type():
    assert type(base_doc_service._valid_similarity('a', 'b')) == bool

def test__associate_return_type():
    assert type(base_doc_service._associate([])) == dict

def test__valid_association_return_type():
    assert type(base_doc_service._valid_association({})) == bool

def test__clean_processed_text_return_type():
    assert type(base_doc_service._clean_processed_text({})) == dict

def test_valid_text_return_type():
    assert type(base_doc_service.valid_text('')) == bool
