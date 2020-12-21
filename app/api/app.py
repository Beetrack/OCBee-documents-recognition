"""
Main module to run Flask API
"""
# pylint: disable=import-error
import os
from uuid import uuid4
from flask import request
from flask_api import FlaskAPI, status
from werkzeug.utils import secure_filename
# pylint: enable=import-error


app = FlaskAPI(__name__)


def allowed_file(filename):
    """Determines if the filetype is allowed or not accordingly to its name"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_file(file) -> str:
    """Saves the uploaded file temporarily into 'app/uploads'"""
    # we generate a unique filename to prevent the case of two pictures
    # being named the same at the same time
    file_name = secure_filename(str(uuid4()))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(file_path)
    return file_path


def app_service(name):
    """Method to compact call from other functions and return the corresponding association"""
    if name not in app.config['SERVICES'].keys():
        raise KeyError('Invalid service name.')
    return app.config['SERVICES'][name]

# we disable redefinition of outer name as pylint thinks `request` is
# being redefined but it is really not happening
# pylint: disable=redefined-outer-name
def process_image(request, service_name: str, threshold=0.75):
    """Processes the uploaded image and returns the service result

    Args:
        request (flask): flask request
        service_name (str): name of the requested service as indicated by settings
        threshold (int/float): threshold to tolerate the sesarched terms

    Returns:
        dict/None: aaccording to processs
    """
    file_path = save_file(request.files['file'])

    # concatenates result, passing directly what is read to the processing
    service = app_service(service_name)
    result = service.process_text(app.config['OCV'].process(file_path), threshold=threshold)

    # clean written image
    os.remove(file_path)
    return result


def extract_threshold(request):
    """Simplifies the extraction from request and handles errors"""
    threshold = request.data['threshold'] if 'threshold' in request.data.keys() else None
    if threshold and threshold.isnumeric():
        return min(1.0, max(0.1, float(threshold)))
    return 0.75
# pylint: enable=redefined-outer-name

@app.route('/api/<string:service>', methods=['GET', 'POST'])
def analyze_image(service):
    """
    API endpoint for all services of image analysis
    """
    # allow access through any string format
    service = service.lower()
    try:
        # we extract (if existing) the threshold and apply a 'roof' to cap it at 1
        threshold = extract_threshold(request)
        result = process_image(request, service, threshold=threshold)
        # image cannot be analyzed
        if result is None:
            result = ({'error': 'Image is not clear enough with threshold {}.'.format(threshold)},
                      status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        else:
            result = ({'data': result}, status.HTTP_200_OK)

    except TypeError as error:
        result = ({'error': str(error)}, status.HTTP_400_BAD_REQUEST)
    except KeyError as error:
        result = ({'error': str(error)}, status.HTTP_400_BAD_REQUEST)
    finally:
        # disabling of lost exception as it is being handled
        return result # pylint: disable=lost-exception
