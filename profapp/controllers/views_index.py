from flask import render_template
from .blueprints import general_bp

@general_bp.route('')
def index():
    return render_template('index.html')
