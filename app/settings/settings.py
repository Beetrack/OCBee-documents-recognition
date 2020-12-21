import os
from dotenv import load_dotenv

# own services
from app.services.ocv.ocv_service import OCVService
from app.services.documents.cni_service import CNIService
from app.services.documents.basic_service import BasicService

load_dotenv(dotenv_path='.env')

# config file
DEBUG = (os.getenv('DEBUG').title() == 'True')

config = {
    'UPLOAD_FOLDER': 'app/uploads',
    'ALLOWED_EXTENSIONS': {
        'png',
        'jpg',
        'jpeg'
    },
    # !!!IMPORTANT!!!
    #####################################################
    # DO NOT REMOVE OCV, AS IT IS NECESSARY FOR THE REST
    # OF THE SERVICES TO WORK
    'OCV': OCVService(),
    #####################################################

    # add here the services that are supported
    # the pairs are in form:
    # url: service
    # url being the url route that will be used
    # (i.e. 'basic' will be 'localhost:5000/api/basic')
    'SERVICES': {
        'basic': BasicService(),
        'cni': CNIService()
    }
}
