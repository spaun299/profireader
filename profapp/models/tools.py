import re


class HtmlHelper():
    REMOVE_CLASSES_FROM_SAME_GROUP = 1

    @staticmethod
    def tinymce_format_groups(layout=None):

        def merge(a, b):
            return dict(list(a.items()) + list(b.items()))

        def rm(list, el):
            ret = list[:]
            ret.remove(el)
            return ret

        def fn(*args):
            return ("profireader_article_" + '_'.join(['%s'] * len(args))) % args

        def get_class_based_formats(group_label, format_labels, remove_classes_on_apply=False,
                                    add_classes_on_apply=False):
            return {fn(group_label, format_label): {'inline': 'span',
                                                    'classes': [fn(group_label, format_label)],
                                                    'remove_classes_on_apply': remove_classes_on_apply,
                                                    'add_classes_on_apply': add_classes_on_apply
                                                    }
                    for format_label in format_labels}

        def get_group_formats(group_label, values=None, remove_classes=[],
                              add_classes=[], post_process=lambda x: x):
            if remove_classes == HtmlHelper.REMOVE_CLASSES_FROM_SAME_GROUP:
                remove_classes = [fn(group_label, '.*')]
            add_also_classes_if_not_exists = {
                fn(group_label_format_label): fn(re.sub('_([^_]+)$', '_.*', group_label_format_label))
                for group_label_format_label in add_classes}
            return post_process(
                get_class_based_formats(group_label, values, remove_classes, add_also_classes_if_not_exists))

        defaultFormatGroupOptions = {'add_classes': [], 'remove_classes': HtmlHelper.REMOVE_CLASSES_FROM_SAME_GROUP,
                                     'post_process': lambda x: x}

        if layout is None:
            return {'text_size': get_group_formats('text_size',
                                                   **merge(defaultFormatGroupOptions, {
                                                       'values': ['tiny', 'little', 'small', 'normal', 'big', 'large',
                                                                  'huge']}))}
        else:

            colors = ['red', 'blue', 'green', 'gray', 'black', 'white']

            border_default_classes = ['border_color_black', 'border_placement_all', 'border_type_solid',
                                      'border_width_thin']

            def replace_something(where, newval, *indexes):
                deep = where
                for i in indexes[0:-1]:
                    deep = deep[i]
                deep[indexes[-1]] = newval
                return where

            groups = {
                'font_family': {'values': ['Arial', 'Courier', 'monospace']},
                'foreground_color': {'values': colors},
                'background_color': {'values': colors},
                'border_color': {'values': colors, 'add_classes': rm(border_default_classes, 'border_color_black')},
                'border_width': {'values': ['medium', 'thin', 'thick', 'none'],
                                 'add_classes': rm(border_default_classes, 'border_width_thin')},
                'border_type': {'values': ['solid', 'dotted', 'dashed', 'double'],
                                'add_classes': rm(border_default_classes, 'border_width_thin')},
                'border_placement': {'values': ['left', 'right', 'top', 'bottom', 'all'],
                                     # TODO: OZ by OZ: add inside border placement to place in each cell 'inside'
                                     'add_classes': rm(border_default_classes, 'border_placement_all'),
                                     'remove_classes': fn('border_placement', 'all'),
                                     'post_process': lambda x: replace_something(x, fn('border_placement_(left|right|top|bottom)'),
                                                                                 fn('border_placement', 'all'),
                                                                                 'remove_classes_on_apply')
                                     }
            }

            return {group_label: get_group_formats(group_label, **merge(defaultFormatGroupOptions, group_properties))
                    for group_label, group_properties in
                    groups.items()}
