from  flask import Flask , render_template, request , redirect , url_for , flash 
import requests
import cv2
import numpy as np
import imutils
import easyocr
import os
import xmltodict
import json
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '.\static\img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    
    path = "static\img\{}".format(filename)
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #Noise reduction
    edged = cv2.Canny(bfilter, 30, 200) #Edge detection
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0,255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)
    (x,y) = np.where(mask==255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2+1, y1:y2+1]
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)
    text = result[0][-2]
    text=text.replace(' ','')
    text=text.replace('.','')
    p= "http://www.regcheck.org.uk/api/reg.asmx/CheckIndia?RegistrationNumber={}&username=ParthPatel".format(text)
    r=requests.get(p)
    data=xmltodict.parse(r.content)
    jsonData=data['Vehicle']['vehicleJson']
    dt=json.loads(jsonData)

    return render_template('info.html' , filename=filename , desc = dt['Description'] , regyr = dt["RegistrationYear"],
            carmake = dt["CarMake"]['CurrentTextValue'],
            model =  dt["CarModel"]['CurrentTextValue'],		
            location = dt["Location"],
            registrationdate =  dt["RegistrationDate"],
            engineNumber = dt["EngineNumber"],
            IdentifyNumber =  dt["VechileIdentificationNumber"], )


if __name__ == "__main__":
    app.run(debug=True)
