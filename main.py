
import os
import json
from flask import Flask, flash, request, redirect, render_template
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

import os.path as osp
from config.settings import UPLOAD_DIR, TEST_DIR, ALLOWED_EXTENSION
from config.settings import IMAGES_INFO_JSON, IS_DEBUG

from src.animal.animal_predict import AnimalPredict

app = Flask(__name__)
bootstrap = Bootstrap(app)

animal_predictor = AnimalPredict()
CURRENT_IMAGE_INFO = os.path.join(UPLOAD_DIR, 'current_image_info.json')

# @app.route('/generate-gallery', methods=['GET'])
# def generate_gallery():
#     img_file_list = [name for name in os.listdir(TEST_DIR) if name != ".DS_Store"]
#     for k, v in enumerate(img_file_list):
#         if k > 50: break
        
        
@app.route('/', methods=['GET', 'POST'])
def animal_predict():
# def make_prediction():
    '''
        Predict the image is cat or dog
    '''
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Please upload an image')
            return redirect(request.url)
        if file and check_file_extension(file.filename):
            filename = secure_filename(file.filename)
            file_path = save_image(file, filename)

            cls_idx, prob = animal_predictor.predict(file_path)
            print("---------current----------")
            print(cls_idx)
            print(prob)  #####
            print(type(cls_idx))
            print(type(prob))
            print("dadnsfnk0----------------da")
            save_image_info(filename, cls_idx, prob)
            current_image_info = {'prob': float(prob), 'file_name': filename}
            with open(CURRENT_IMAGE_INFO, 'w') as fw:
                json.dump(current_image_info, fw, indent=4)
            
            # get information of gallery
            images, cur_accuracy, num_stored_images = get_stat_of_recent_images()

            if cls_idx == 0:
                cat_prob = float('{:.1f}'.format(prob * 100))
                dog_prob = 100- cat_prob
            else:
                dog_prob = float('{:.1f}'.format(prob * 100))
                cat_prob = 100 - dog_prob
            print(dog_prob, cat_prob)


            return render_template(
                    'index.html',
                    # cat_prob=float('{:.1f}'.format(prob * 100)) ,
                    # dog_prob=float('{:.1f}'.format((1 - prob) * 100)),
                    cat_prob = cat_prob,
                    dog_prob = dog_prob,
                    cur_image_path=file_path,
                    images=images,
                    num_stored_images=30,
                    cur_accuracy=cur_accuracy,
                    show_feedback=True)
                

    # get information of gallery when receive GET request
    images, cur_accuracy, num_stored_images = get_stat_of_recent_images()
    return render_template(
            'index.html', images=images, cur_accuracy=cur_accuracy,
            num_stored_images=num_stored_images)
        

         
# def get_stat_of_recent_images(show_nums=30):
#     with open(IMAGES_INFO_JSON, 'r') as fr:
#         img_info = json.load(fr)
#     img_status = []
#     for k, v in img_info:
#         if k > show_nums: 
#             break
#         tmp_info = v
#         # tmp_info['path'] = 
#         img_status.append(v)

        
#     cur_accuracy = 1.0
#     num_stored_images = 30
#     return img_status, cur_accuracy, num_stored_images




@app.route('/feedback', methods=['POST'])
def save_user_feedback():
    """Save user feedback of current prediction"""

    # get most recently prediction result
    if os.path.exists(CURRENT_IMAGE_INFO):
        with open(CURRENT_IMAGE_INFO, 'r') as f:
            info = json.load(f)
            filename = info['file_name']
            prob = info['prob']

    label = request.form['label']

    print('filename: {}, prob: {}'.format(filename, prob))

    init_image_info()

    if filename:
        # save user feedback in file
        with open(IMAGE_INFO_JSON, 'r') as f:
            image_info = json.load(f)
            image_info[filename]['label'] = label
        with open(IMAGE_INFO_JSON, 'w') as f:
            json.dump(image_info, f, indent=4)

        if SAVE_INFO_ON_AWS:
            save_image_info_on_s3(image_info)


    # get information of gallery
    images, cur_accuracy, num_stored_images = get_stat_of_recent_images()


    return render_template(
            'index.html',
            prob=float('{:.1f}'.format(prob * 100)) if prob else 0,
            cur_image_path=uploaded_image_path(filename),
            images=images,
            num_stored_images=num_stored_images,
            cur_accuracy=cur_accuracy,
            show_thankyou=True)



def get_stat_of_recent_images(num_images=300):
    """Return information of recent uploaded images for galley rendering

    Parameters
    ----------
    num_images: int
        number of images to show at once
    Returns
    -------
    image_stats: list of dicts representing images in last modified order
        path: str
        label: str
        pred: str
        cat_prob: int
        dog_prob: int

    cur_accuracy: float
    num_stored_images: int
        indepenent of num_images param, the total number of images available

    """
    folder = UPLOAD_DIR

    init_image_info()


    # get list of last modified images
    # exclude .json file and files start with .
    files = ['/'.join((folder, file)) \
        for file in os.listdir(folder) if ('json' not in file) \
        and not (file.startswith('.')) ]

    # list of tuples (file_path, timestamp)
    last_modified_files = [(file, os.path.getmtime(file)) for file in files]
    last_modified_files = sorted(last_modified_files,
                            key=lambda t: t[1], reverse=True)
    num_stored_images = len(last_modified_files)



    # read in image info
    with open(IMAGES_INFO_JSON, 'r') as f:
        info = json.load(f)

    # build info for images
    image_stats = []
    for i, f in enumerate(last_modified_files):
        # set limit for rendering pictures
        if i > num_images: break

        path, filename = f[0], f[0].replace(folder, '').replace('/', '')
        cur_image_info = info.get(filename, {})

        prob = cur_image_info.get('prob', 0)

        image = {
            'path': path,
            'label': cur_image_info.get('label', 'unknown'),
            'pred': cur_image_info.get('pred', 'dog'),
            'cat_prob': int(prob * 100),
            'dog_prob': int((1 - prob) * 100),
        }
        image_stats.append(image)

    # comput current accuracy if labels available
    total, correct = 0, 0
    for image in image_stats:
        if image['label'] != 'unknown':
            total += 1
            if image['label'] == image['pred']:
                correct += 1

    try:
        cur_accuracy = float('{:.3f}'.format(correct / float(total)))
    except ZeroDivisionError:
        cur_accuracy = 0

    # print(image_stats)
    # print(cur_accuracy)

    return image_stats, cur_accuracy, num_stored_images




def init_image_info():
    """Init settings.IMAGE_INFO_JSON using file stored on S3 for
    warm start.
    """
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)


def save_image(file, filename):
    '''
    file: werkzeug.datastructures.FileStorage
    filename: str
    '''    
    if not osp.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    file_save_path = osp.join(UPLOAD_DIR, filename)
    file.save(file_save_path)

    # if save to other serveice like AWS by ak, sk
    # TODO

    return file_save_path

def save_image_info(filename, cls_idx, prob):
    with open(IMAGES_INFO_JSON, 'r') as fr:
        image_info = json.load(fr)
        image_info[filename] = {
            'prob': float(prob) if cls_idx==0 else (1-float(prob)),
            'y_pred': cls_idx,
            'pred': 'dog' if cls_idx==1 else 'cat',
            'label': 'unknown'
        }
    print("*****************")
    print(image_info[filename])
    with open(IMAGES_INFO_JSON, 'w') as fw:
        json.dump(image_info, fw, indent=4)








def check_file_extension(filename):
    return filename.split('.')[-1].lower() in ALLOWED_EXTENSION






if __name__ == "__main__":
    # IS_DEBUG = True
    
    app.run(host='192.168.0.100', port=5000, debug=IS_DEBUG)
    # PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
    # print(PROJECT_PATH)





