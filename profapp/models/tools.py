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

            def remove_none_or_all(x, group_name):
                replace_something(x, [fn(group_name, '(left|right|top|bottom|none)')], fn(group_name, 'all'),
                                  'remove_classes_on_apply')
                replace_something(x, [fn(group_name, '(left|right|top|bottom|all)')], fn(group_name, 'none'),
                                  'remove_classes_on_apply')
                return x

            groups = {
                'font_family': {'values': ['Arial', 'Courier', 'monospace']},
                'foreground_color': {'values': colors},
                'background_color': {'values': colors},

                'border_color': {'values': colors, 'add_classes': rm(border_default_classes, 'border_color_black')},

                'border_width': {'values': ['medium', 'thin', 'thick'],
                                 'add_classes': rm(border_default_classes, 'border_width_thin')},

                'border_type': {'values': ['solid', 'dotted', 'dashed', 'double'],
                                'add_classes': rm(border_default_classes, 'border_type_solid')},

                'border_placement': {'values': ['none', 'left', 'right', 'top', 'bottom', 'all'],
                                     # TODO: OZ by OZ: add inside border placement to place in each cell 'inside'
                                     'add_classes': rm(border_default_classes, 'border_placement_all'),
                                     'remove_classes': [fn('border_placement', 'all'), fn('border_placement', 'none')],
                                     'post_process': lambda x: remove_none_or_all(x, 'border_placement')
                                     },

                'margin_size': {'values': ['medium', 'thin', 'thick'], 'add_classes': ['margin_placement_all']},

                'margin_placement': {'values': ['none', 'left', 'right', 'top', 'bottom', 'all'],
                                     'add_classes': ['margin_size_thin'],
                                     'remove_classes': [fn('margin_placement', 'all'), fn('margin_placement', 'none')],
                                     'post_process': lambda x: remove_none_or_all(x, 'margin_placement')
                                     },

                'padding_size': {'values': ['medium', 'thin', 'thick'], 'add_classes': ['margin_placement_all']},

                'padding_placement': {'values': ['none', 'left', 'right', 'top', 'bottom', 'all'],
                                     # TODO: OZ by OZ: add inside border placement to place in each cell 'inside'
                                     'add_classes': ['padding_size_thin'],
                                     'remove_classes': [fn('padding_placement', 'all'), fn('padding_placement', 'none')],
                                     'post_process': lambda x: remove_none_or_all(x, 'padding_placement')
                                     }

            }

            return {group_label: get_group_formats(group_label, **merge(defaultFormatGroupOptions, group_properties))
                    for group_label, group_properties in
                    groups.items()}
