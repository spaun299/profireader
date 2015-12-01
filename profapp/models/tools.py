class HtmlHelper():
    @staticmethod
    def tinymce_formats(portal_layout_id=None, get_buttons=False):

        if portal_layout_id is None:
            return {'profireader_article_text_size_' + size: {'inline': 'span',
                                                              'classes': ['profireader_article_text_size_' + size],
                                                              'remove_classes_on_apply': 'profireader_article_.*'}
                    for size in ['tiny', 'little', 'small', 'normal', 'big', 'large', 'huge']}
        else:
            ret = {}

            colors = ['red', 'blue', 'green', 'gray', 'black', 'white']
            color_formats = {'foreground_color': colors, 'background_color': colors, 'border_color': colors}
            for subject in color_formats:
                ret[subject] = {}
                for color in color_formats[subject]:
                    ret[subject][color] = {'inline': 'span',
                                           'classes': ['profireader_article_%s_%s' % (subject, color)],
                                           'remove_classes_on_apply': ('profireader_article_%s_.*' % (subject))}
            for color in color_formats['border_color']:
                ret['border_color'][color]['add_classes_on_apply'] = \
                    ['profireader_article_border_placement_all', 'profireader_article_border_type_solid',
                     'profireader_article_border_width_thin']

            ret['font_family'] = {}
            for font_family in ['Arial', 'Courier', 'monospace']:
                ret['font_family'][font_family] = \
                    {'inline': 'span', 'classes': ['profireader_article_font_family_' + font_family],
                     'remove_classes_on_apply': 'profireader_article_font_family_.*'}

            ret['border_width'] = {}
            for border_width in ['medium', 'thin', 'thick', 'none']:
                ret['border_width'][border_width] = \
                    {'inline': 'span', 'classes': ['profireader_article_border_width_' + border_width],
                     'add_classes_on_apply': ['profireader_article_border_color_black',
                                              'profireader_article_border_placement_all',
                                              'profireader_article_border_type_solid'],
                     'remove_classes_on_apply': 'profireader_article_border_width_.*'}

            ret['border_placement'] = {}
            for border_placement in ['left', 'right', 'top', 'bottom', 'inside', 'all']:
                ret['border_placement'][border_placement] = \
                    {'inline': 'span', 'classes': ['profireader_article_border_placement_' + border_placement],
                     'remove_classes_on_apply': 'profireader_article_border_placement_all',
                     'add_classes_on_apply': ['profireader_article_border_color_black',
                                              'profireader_article_border_width_thin',
                                              'profireader_article_border_type_solid']}

            ret['border_placement']['all'][
                'remove_classes_on_apply'] = 'profireader_article_border_placement_(left|right|top|bottom)'

            ret['border_type'] = {}
            for border_type in ['solid', 'dashed', 'dotted', 'double']:
                ret['border_type'][border_type] = \
                    {'inline': 'span', 'classes': ['profireader_article_border_type_' + border_type],
                     'remove_classes_on_apply': 'profireader_article_border_type_.*',
                     'add_classes_on_apply': ['profireader_article_border_color_black',
                                              'profireader_article_border_width_thin'
                                              'profireader_article_border_placement_all']}

            if get_buttons:
                return {
                    format_group_name: {format_name: ("profireader_article_%s_%s" % (format_group_name, format_name))
                                        for
                                        format_name in ret[format_group_name]} for format_group_name in ret}
            else:
                return {
                    ('profireader_article_%s_%s' % (format_group_name, format_name)): ret[format_group_name][
                        format_name]
                    for format_group_name in ret for format_name in ret[format_group_name]}


                # return {'profireader_article_%s_color_%s' % (subject, color):
                #             std(subject + '_' + color) for subject in ['fg', 'bg', 'border'] for color
                #         in ['normal', 'red', 'blue', 'green', 'gray']}
