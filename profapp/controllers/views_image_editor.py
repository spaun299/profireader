from .blueprints import image_editor_bp
from flask import render_template, request
from config import Config

@image_editor_bp.route('/')
def image_editor():

    ratio = Config.IMAGE_EDITOR_RATIO
    return render_template('image_editor.html',
                           ratio=ratio
                           )

@image_editor_bp.route('/editor', methods=['GET', 'POST'])
def editor():

    return render_template('image_editor.html')