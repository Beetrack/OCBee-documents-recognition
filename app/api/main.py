import os
from pprint import pprint
from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
from werkzeug.utils import secure_filename

# own services
from app.services.ocv_service import OCVService
from app.services.documents.cni_service import CNIService

ocv_service = OCVService()
cni_service = CNIService()

UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = FlaskAPI(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/cni', methods=['GET', 'POST'])
def upload_cni():
    try:
        file = request.files['file']
        file_name = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        file.save(file_path)

        # concatenates result, passing directly what is read to the processing
        result = cni_service.process_text(ocv_service.process(file_path))

        # image cannot be analyzed
        if result is None:
            result = ({'error': 'Image is not clear enough.'}, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        else:
            result = (result, status.HTTP_200_OK)
        
            os.remove(file_path)

    except TypeError as error:
        result = ({'error': str(error)}, status.HTTP_400_BAD_REQUEST)

    except KeyError as error:
        result = ({'error': str(error)}, status.HTTP_400_BAD_REQUEST)

    finally:

        return result

if __name__ == "__main__":
    app.run(debug=True)