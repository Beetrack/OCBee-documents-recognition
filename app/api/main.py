import os
from pprint import pprint
from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
from werkzeug.utils import secure_filename
from uuid import uuid4

# own services
from app.services.ocv_service import OCVService
from app.services.documents.cni_service import CNIService
from app.services.documents.basic_service import BasicService


UPLOAD_FOLDER = 'app/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
SERVICES = {
    'ocv': OCVService(),
    'basic': BasicService(),
    'cni': CNIService()
}

app = FlaskAPI(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SERVICES'] = SERVICES


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file) -> str:
    # we generate a unique filename to prevent the case of two pictures
    # being named the same at the same time
    file_name = secure_filename(str(uuid4()))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(file_path)
    return file_path


def app_service(name):
    # simple method to compact call
    if name not in app.config['SERVICES'].keys():
        raise KeyError('Invalid service name.')
    return app.config['SERVICES'][name]


def process_image(request, service_name, threshold=0.75):
    file_path = save_file(request.files['file'])

    # concatenates result, passing directly what is read to the processing
    service = app_service(service_name)
    result = service.process_text(app_service(
        'ocv').process(file_path), threshold=threshold)

    # clean written image
    os.remove(file_path)
    return result


def extract_threshold(request):
    threshold = request.data['threshold'] if 'threshold' in request.data.keys(
    ) else None
    if threshold and threshold.isnumeric():
        return min(1.0, max(0.1, float(threshold)))
    return 0.75


@app.route('/api/<string:service>', methods=['GET', 'POST'])
def analyze_image(service):
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
        return result


if __name__ == "__main__":
    app.run(debug=True)
