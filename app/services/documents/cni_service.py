# standard library imports
import re

# own dependencies
from base_document_service import BaseDocumentService


class CNIService(BaseDocumentService):

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
    # FECHA DE NACIMIENTO NUMERO DOCUMENTO, 31 DIC 1997 511408104
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
        association = {txt: None for txt in self.TO_FIND}

        for finding in self.TO_FIND.keys():
            for j, text in enumerate(text_list):
                # RUN is read in different way
                if self._valid_similarity(finding, text):
                    if finding == 'APELLIDOS':
                        association['APELLIDOS'] = text_list[j+1] + ' ' + text_list[j+2]
                    else:
                        association[finding] = text_list[j + self.TO_FIND[finding]]

                elif re.match(self.PATTERNS['run'], text):
                    association['RUN'] = text

        return association

    def _valid_association(self, associations: dict) -> bool:
        def valid_run(associations):
            run = associations['RUN']
            return bool(run) and re.match(self.PATTERNS['run'], run)

        def valid_lastname(associations):
            return bool(associations['APELLIDOS'])

        def valid_name(associations):
            return bool(associations['NOMBRES'])

        def valid_nationality_sex(associations):
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

