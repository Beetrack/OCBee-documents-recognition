import pytest

from app.services.documents.cni_service import CNIService


cni_service = CNIService()

cases = [
    'CEDULA DE\nIDENTIDAD\n\n \n\nRUN 9.932.656-5\n\n \n\nREPUBLICA DE CHILE\n\nSERVIC OPE REGISTRO Civil & DER TT\n\nAPELEIDOS\n\nRODRIGUEZ\nZEPEDA\n\nNOMBRES\n\nCLAUDIO ANTONIO\n\nNACIONALIDAD SEXO\n\nCHILENA M\n\nFECHA DE NACIMIENTO NUMERO DOCUMENTO\n\n143 OCT 1965 102.814.050\n\nFECHA DE EMISION FECHA DE VENCIMIENTO\n\n05 AGO 2014 13 OCT 2019\n\nFIRMA DEL TITULAR\n\ndio\n\x0c',
    '  \n\nCEDULA DE\nIDENTIDAD\n\nEXTRANJERO\n\n \n\nin REPUBLICA DE CHILE\n\nRODRIGUEZ\nAPONTE\n\nNOMBRES\n\nMARIA TERESA\nNACIONALIDAT SEXO\nVEN F\nFECHA DE NACIMIENTO NUMERO DOCUMENTO\n“5 MAR 1991\nADEFMISION FECHA DE VENCIMIENTO.\n\n96 SEPT 2018 31 AGO 2019\n\nAMAL. TITUAR\n\n‘ Pc drupal ,\ni WwW ie 7\n\n \n\nWw\n\nom\n\x0c',
    '    \n\nCEDULA DE\nIDENTIDAD dems\n\n \n\nREPUBLICA DE CHILE\n\nSERVICIO DE REGISTRO CIVIL E IDENTIFICACION\nAPELLIDOS\n\nSANHUEZA\nHARRIS\n\nNOMBRES\n\nOLGA ESTER\n\nNACIONALIDAD SEXO\n\nCHILENA FE\n\nFECHA DE NACIMIENT’ a a “7 6\n25 SEPT 1964 a ~~ vv\n\n \n\nFECHA DE EMISION\n\n23 JUL 2014\n\nFIRMA DEL TITULAR\n\n/\n\n \n\x0c',
    'CEDULA DE REPUBLICA DE CHILE\n\nIDENTIDAD.\n\n \n\nRUN 12.749.625-K\n\nSEIVIC © DE REGISTRO C VIL EIDENTINCACION.\n\nAPELUDOS\nFREDEZ\n\nVIDAL\n\nNonnres.\n\nMARCELA CAROLINA\nMACIONALIDAD ‘sexo\nCHILENA F\n\nFECHA DENACIMENTO NUMERO OCUMENTO\n21 FEB 1982 100000001\nPECHADEEMIEION FECHA DE-VENCIMIENTO.\n1 SEP 2013 10 AGO 2023\n\nc-cleMeda=\n\n \n\x0c',
    " \n\n \n\n \n\nCEDULA DE\nIDENTIDAD\n\n_— =\n_ _ &\n“Be co \\\n\ndsc is\n\nRUN 5.632.605-7\n\nREPUBLICA DE CHILE\n\nSERVICIO DE REGIS™RO C'VIL F IDENTIFICAC ON\n\nAPELLIDOS\nMALDONADO\nJEREZ\n\nNOMBRES\n\nJUAN DANIEL\n\nNACIONALIDAD\n SEXO\n\nCHILENA M\n\nFECHA DE NACIMIENTO NUMERO DOCUMENTO\n\n15 MAR 1948 102.773.350\n\nFECHA DE EMISION FECHA DE VENCIMIENTO\n\n31 JUL 2014 15 MAR 2020\n\nFIRMA DEL TITULAR\n\npie\n\n \n\n4 oN\n/\n\n \n\n5 @§2.505-7\n\x0c",
    'CEDULA DE\nIDENTIDAD lee\n\n \n\nRUN 19.711.416-9\n\nREPUBLICA DE CHILE\n\nSERVICIO DE REGISTRO CIVIL E IDENTHF © At ‘On! ™\n\nuy *\nAPELLIDOS\n\nLEIVA\nSEREY\n\nNOMBRES\n\nRONY ORLANDO\n\nNAC IONALIDAD SEXO\n\nCHILENA M .\n\nFECHA DE NACIMIENTO NUMERO DOCUMENTO\n\n31 DIC 1997 511.408.104\n\nFECHA DE EMISION FECHA DE VENCIMIENTO\n\n13 MAR 2017 31 DIC 2020\n\nFIRMA DEL TITULAR\n\n)\n| pew\n\n!\n\x0c'
]

invalid_run = cases[0:4]
valid_run = cases[4:]


@pytest.mark.parametrize(
    "test_input,expected",
    [
        # unpacks into the expected with input
        *zip(valid_run, [True] * len(valid_run)),
        *zip(invalid_run, [False] * len(invalid_run))
    ]
)
def test_valid_text_valid_return(test_input, expected):
    assert cni_service.valid_text(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        # unpacks into the expected with input
        *zip(valid_run, [dict] * len(valid_run)),
        *zip(invalid_run, [type(None)] * len(invalid_run))
    ]
)
def test_process_text_valid_return_type(test_input, expected):
    assert type(cni_service.process_text(test_input)) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        *zip(valid_run, [['RUN',
                          'APELLIDOS',
                          'NOMBRES',
                          'NACIONALIDAD',
                          'SEXO',
                          'FECHA DE NACIMIENTO',
                          'NUMERO DOCUMENTO',
                          'FECHA DE EMISION',
                          'FECHA DE VENCIMIENTO']] * len(valid_run))
    ]
)
def test_process_text_field_names(test_input, expected):
    # we sort to make it comparable
    assert sorted(list(cni_service.process_text(test_input).keys())) == sorted(expected)


def test_cleaner_return_type():
    assert type(cni_service.cleaner('')) == list


def test__valid_similarity_type():
    assert type(cni_service._valid_similarity('a', 'b')) == bool


def test__associate_return_type():
    assert type(cni_service._associate([])) == dict


def test__valid_association_return_type():
    assert type(cni_service._valid_association({key: None for key in cni_service.TO_FIND.keys()})) == bool


def test__clean_processed_text_return_type():
    assert type(cni_service._clean_processed_text({
        'NACIONALIDAD SEXO': 'CHILENO M',
        'RUN': 'RUN 12.345.678-9',
        'NOMBRES': 'JUAN PEREZ',
        'APELLIDOS': 'SOTO DE LA PERA',
        'FECHA DE NACIMIENTO NUMERO DOCUMENTO': '01 ENE 1750 111.111.111',
        'FECHA DE EMISION FECHA DE VENCIMIENTO': '01 ENE 1750 02 ENE 1752'
    })) == dict


def test_valid_text_return_type():
    assert type(cni_service.valid_text('')) == bool
