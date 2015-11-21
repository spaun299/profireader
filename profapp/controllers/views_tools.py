


@tools_bp.route('/translate/', methods=['POST'])
@ok
def translate(json):
    translation = TranslateTemplate.getTranslate(request.json['template'], request.json['phrase'])
    return {'phrase': translation}


@tools_bp.route('/save_translate/', methods=['POST'])
@ok
def save_translate(json):
    return TranslateTemplate.getTranslate(request.json['template'], request.json['phrase'], request.json['url'])

@tools_bp.route('/update_last_accessed/', methods=['POST'])
@ok
def update_last_accessed(json):
    return TranslateTemplate.update_last_accessed(request.json['template'], request.json['phrase'])

@tools_bp.route('/list/', methods=['GET'])
def show_mine():
    return render_template(
        'article/list.html',
        angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js')
