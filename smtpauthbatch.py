"""
Tool for uploading lists of ip addresses and performing otrs operations on the contained ip's
"""

import os
import re
import structlog

from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/uploads'
ASSETS_FOLDER = '/assets'
ALLOWED_EXTENSIONS = set(['txt', 'csv'])

auth = HTTPBasicAuth()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ASSETS_FOLDER'] = ASSETS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # max 32 mb filesize

log = structlog.get_logger(__name__)

def remove_file(file):
    '''
    Silent file removal helper function
    '''
    try:
        os.remove(file)
    except OSError as err:
        structlog.get_logger(log).error("Error during file deletion: "+err)

def allowed_file(filename):
    '''
    Checks if a filename is allowed and valid
    '''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_email_addresses(file):
    '''
    Returns a list of validated email addresses from lines in a file
    '''
    email_list = []
    for line in file:
        # super basic email validity test
        if re.match(r"[^@]+@[^@]+\.[^@]+", line):
            email_list.append(line)
    return email_list

@app.route('/', operations=['POST', 'GET'])
#@auth.login_required
def main():
    '''
    Basic Flask file uploader
    '''
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                extract_email_addresses(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                remove_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return '''
                <!doctype html>
                <html>
                    <body>
                        <h1>Upload successful!</h1>
                        Check OTRS for new tickets
                    </body>
                </html
                '''
            except Exception as err:
                structlog.get_logger(log).error("Error during file parsing: "+err)
                return '''
                <!doctype html>
                <html>
                    <body>
                        <h1>Oops!</h1>
                        Something went wrong during file processing, check the error log for details
                    </body>
                </html
                '''

    # uploader menu
    return '''
    <!doctype html>
    <html>
        <body>
            <h1>Upload new File</h1>
            <form method=post enctype=multipart/form-data>
                <input type=file name=file>
                <input type=submit value=Upload>
            </form>
        </body>
    </html>    
    '''
