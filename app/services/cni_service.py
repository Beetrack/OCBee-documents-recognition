from strsimpy.normalized_levenshtein import NormalizedLevenshtein
import re


class CNIService:

    # patterns to make final clean
    P_RUN = r'\w+\s?([\dK]{8,9})'
    P_NAC_SEX = r'(\w+)\s([FM])'
    P_BTH_DOC = r'(\d{2} \w{3} \d{4}) (\d+)'
    P_GEN_DUE = r'(\d{2} \w{3} \d{4}) (\d{2} \w{3} \d{4})'

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

    def cleaner(self, text: str) -> list:
        # normalize spaces and removes non standar characters
        text = re.sub(r'\s{2,}|[^\w\\\s.-]', '\n', text).upper()

        # removes unnecessary \ or other characters excepting \n
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # split based on enter and filter of white spaces
        text_lines = map(lambda txt: txt.strip(), text.split('\n'))
        text_lines = list(filter(lambda txt: (txt != '') or (not re.match(r'\s*', txt)), text_lines))
        return text_lines

    def _valid_similarity(self, find: str, compare: str, threshold=0.75) -> bool:
        return normalized_levenshtein.similarity(find, compare) >= threshold

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

                elif re.match(self.P_RUN, text):
                    association['RUN'] = text

        return association

    def _valid_association(self, associations: dict) -> bool:
        def valid_run(associations):
            run = associations['RUN']
            return bool(run) and re.match(self.P_RUN, run)

        def valid_lastname(associations):
            return bool(associations['APELLIDOS'])

        def valid_name(associations):
            return bool(associations['NOMBRES'])

        def valid_nationality_sex(associations):
            return bool(associations['NACIONALIDAD SEXO'] or (associations['NACIONALIDAD'] and associations['SEXO']))
        
        def valid_birth_doc(associations):
            birth_doc = associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']
            return bool(birth_doc) and re.match(self.P_BTH_DOC, birth_doc)
        
        def valid_generated_due(associations):
            generated_due = associations['FECHA DE EMISION FECHA DE VENCIMIENTO']
            return bool(generated_due) and re.match(self.P_GEN_DUE, generated_due)

        return all([
            valid_run(associations) and
            valid_lastname(associations) and
            valid_name(associations) and
            valid_nationality_sex(associations) and
            valid_birth_doc(associations) and
            valid_generated_due(associations)
        ])

    def _clean_processed_text(self, associations: dict) -> dict:
        def clean_nac_sex(associations):
            if 'NACIONALIDAD' in associations.keys():
                nac, sex = re.match(self.P_NAC_SEX, associations['NACIONALIDAD']).groups()

            elif 'NACIONALIDAD SEXO' in associations.keys():
                nac, sex = re.match(self.P_NAC_SEX, associations['NACIONALIDAD SEXO']).groups()
                del associations['NACIONALIDAD SEXO']

            associations['NACIONALIDAD'] = nac
            associations['SEXO'] = sex
            return associations

        def clean_run(associations: dict) -> dict:
            associations['RUN'] = re.match(self.P_RUN, associations['RUN']).groups()[0]
            return associations

        def clean_birth_doc(associations: dict) -> dict:
            birth, doc = re.match(self.P_BTH_DOC, associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']).groups()
            associations['FECHA DE NACIMIENTO'] = birth
            associations['NUMERO DOCUMENTO'] = doc
            del associations['FECHA DE NACIMIENTO NUMERO DOCUMENTO']
            return associations

        def clean_generated_due(associations: dict) -> dict:
            generated, due = re.match(self.P_GEN_DUE, associations['FECHA DE EMISION FECHA DE VENCIMIENTO']).groups()
            associations['FECHA DE NACIMIENTO'] = generated
            associations['NUMERO DOCUMENTO'] = due
            del associations['FECHA DE EMISION FECHA DE VENCIMIENTO']
            return associations

        associations = dict(filter(lambda item: bool(item[1]), associations.items()))
        associations = clean_nac_sex(associations)
        associations = clean_run(associations)
        associations = clean_birth_doc(associations)
        associations = clean_generated_due(associations)
        return associations

