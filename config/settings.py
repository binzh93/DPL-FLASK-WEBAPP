import os.path as osp



UPLOAD_DIR = 'static/uploaded_images'

TEST_DIR = '' 

ALLOWED_EXTENSION = set(['png', 'jpg', 'jpeg', 'bmp'])

IMAGES_INFO_JSON = osp.join(UPLOAD_DIR, 'image_info.json')

IS_DEBUG = True