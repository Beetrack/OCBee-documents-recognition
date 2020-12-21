"""
CNI Service which it is used to read CNI
"""
# standard library imports
import re

# own dependencies
from app.services.documents.base_document_service import BaseDocumentService


class CNIService(BaseDocumentService):
    """
    CNI: Cedula Nacional de Identidad parsing service.

    Patterns that are required (re format) (`PATTERNS`):
        - RUN
        - Nacionality and Sex
        - Birthdate and Document number
        - Generated date of document and Due date of document

    Patterns that are normally obtained by OCV and are required to parse document correctly (`TO_FIND`):
        - 'RUN'
        - 'APELLIDOS'
        - 'NOMBRES'
        - 'NACIONALIDAD SEXO' (we apply also 'NACIONALIDAD' and 'SEXO' separately as OCV
                               can sometimes interpret them as separte items)
        - 'FECHA DE NACIMIENTO NUMERO DOCUMENTO'
        - 'FECHA DE EMISION FECHA DE VENCIMIENTO'
    """

    # patterns to make final clean
    PATTERNS = {
        'run': r'\w+\s?([\dK.-]{10,12})',
        'nac_sex': r'(\w+)\s([FM])',
        'bth_doc': r'(\d{2} \w{3} \d{4}) (\d.+)',
        'gen_due': r'(\d{2} \w{3} \d{4}) (\d{2} \w{3} \d{4})'
    }

    # keys to find and values to skip to get the corresponding
    # asumes format:
    # ...
    # APELLIDOS, APELLIDO 1, APELLIDO 2
    # ...
    # NOMBRES, JUAN DE LA ROSA
    # ...
    # NACIONALIDAD SEXO, CHILENO M,
    # ...
    # FECHA DE NACIMIENTO NUMERO DOCUMENTO, 31 DIC 1997 511.408.104
    # ...
    # FECHA DE EMISION FECHA DE VENCIMIENTO, 13 MAR 2017 31 DIC 2020
    TO_FIND = {
        'RUN': 0,
        'APELLIDOS': 1,
        'NOMBRES': 1,
        'NACIONALIDAD SEXO': 1,
        'NACIONALIDAD': 2,
        'SEXO': 1,
        'FECHA DE NACIMIENTO NUMERO DOCUMENTO': 1,
        'FECHA DE EMISION FECHA DE VENCIMIENTO': 1
    }

    def _associate(self, text_list: list, threshold=0.75) -> dict:
        """
        Initial association of cleaned text into the corresponding dictionary; this is fields that are
        searched for filled with the corresponding information
        
        Args:
            text_list (list): cleaned list of strings that will be searched upon to associate
                              to the desired document elements
            threshold (optional)(int/float): threshold to use when validating the similarity of the search for key words

        Returns:
            dict: dictionary of generated associations of fields (i.e.: {field: information})
        """
        association = {txt: None for txt in self.TO_FIND}
        try:

            for finding in self.TO_FIND.keys():
                for j, text in enumerate(text_list):
                    if self._valid_similarity(finding, text, threshold=threshold):
                        # APELLIDOS are generally in two separate lines so we have to
                        # concatenate them into a single string by looking into the next
                        # element in the list
                        if finding == 'APELLIDOS':
                            association['APELLIDOS'] = text_list[j+1] + ' ' + text_list[j+2]
                        else:
                            association[finding] = text_list[j + self.TO_FIND[finding]]
                    # RUN is normally in the same string instead of a different one, so we
                    # have to apply regex to know if the text has the pattern of a RUN
                    elif re.match(self.PATTERNS['run'], text):
                        association['RUN'] = text

        except IndexError:
            # we ignore the error and return inmediatly, which
            # will force the next steps into invalidation as there is no
            # match between the necessary findings
            pass
        finally:
            return association

    def _valid_association(self, associations: dict) -> bool:
        """
        Validates that the initial association is correct and correctly fills all the required
        fields of the document

        Args:
            associations (dict): dictionary of previously generated associations

        Returns:
            bool: True if all required fields are correctly fielled, False otherwise
        """
        def valid_run(associations):
            run = associations['RUN']
            return bool(run) and re.match(self.PATTERNS['run'], run)

        def valid_lastname(associations):
            # we cannot check with regex for names as they are unique in form and style
            return bool(associations['APELLIDOS'])

        def valid_name(associations):
            # we cannot check with regex for names as they are unique in form and style
            return bool(associations['NOMBRES'])

        def valid_nationality_sex(associations):
            # we have to validate a combination as they may be separated, but both have to be present
            return bool(associations['NACIONALIDAD SEXO'] or (associations['NACIONALIDAD'] and associations['SEXO']))

        def valid_birth_doc(associations):
            birth_doc = associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']
            return bool(birth_doc) and re.match(self.PATTERNS['bth_doc'], birth_doc)

        def valid_generated_due(associations):
            generated_due = associations['FECHA DE EMISION FECHA DE VENCIMIENTO']
            return bool(generated_due) and re.match(self.PATTERNS['gen_due'], generated_due)

        return all((
            valid_run(associations),
            valid_lastname(associations),
            valid_name(associations),
            valid_nationality_sex(associations),
            valid_birth_doc(associations),
            valid_generated_due(associations)
        ))

    def _clean_processed_text(self, associations: dict) -> dict:
        """
        Cleans the processed text and splits and extracts the desired information from the association
        to have the final information with the correct association

        i.e.: before -> {'NAC SEX': 'CHILE M'} -> after {'NAC': 'CHILE', 'SEX': 'M'}

        Args:
            associations (dict): dictionary of previously generated and cleaned associations

        Returns:
            dict: correctly formatted associations and information
        """
        def clean_nac_sex(associations):
            if 'NACIONALIDAD' in associations.keys():
                nac, sex = re.match(self.PATTERNS['nac_sex'], associations['NACIONALIDAD']).groups()

            elif 'NACIONALIDAD SEXO' in associations.keys():
                nac, sex = re.match(self.PATTERNS['nac_sex'], associations['NACIONALIDAD SEXO']).groups()
                del associations['NACIONALIDAD SEXO']

            associations['NACIONALIDAD'] = nac
            associations['SEXO'] = sex
            return associations

        def clean_run(associations: dict) -> dict:
            associations['RUN'] = re.match(self.PATTERNS['run'], associations['RUN']).groups()[0]
            return associations

        def clean_birth_doc(associations: dict) -> dict:
            birth, doc = re.match(self.PATTERNS['bth_doc'],
                                  associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']).groups()
            associations['FECHA DE NACIMIENTO'] = birth
            associations['NUMERO DOCUMENTO'] = doc
            del associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']
            return associations

        def clean_generated_due(associations: dict) -> dict:
            generated, due = re.match(self.PATTERNS['gen_due'],
                                      associations['FECHA DE EMISION FECHA DE VENCIMIENTO']).groups()
            associations['FECHA DE EMISION'] = generated
            associations['FECHA DE VENCIMIENTO'] = due
            del associations['FECHA DE EMISION FECHA DE VENCIMIENTO']
            return associations

        associations = dict(filter(lambda item: bool(item[1]), associations.items()))
        associations = clean_nac_sex(associations)
        associations = clean_run(associations)
        associations = clean_birth_doc(associations)
        associations = clean_generated_due(associations)
        return associations
