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
