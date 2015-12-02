function getTinymceSettings() {
var general_formats =   {
				valigntop: [
					{selector: 'td,th', styles: {'verticalAlign': 'top'}}
				],

				valignmiddle: [
					{selector: 'td,th', styles: {'verticalAlign': 'middle'}}
				],

				valignbottom: [
					{selector: 'td,th', styles: {'verticalAlign': 'bottom'}}
				],

				alignleft: [
					{selector: 'figure,p,h1,h2,h3,h4,h5,h6,td,th,tr,div,ul,ol,li', styles: {textAlign: 'left'}, defaultBlock: 'div'},
					{selector: 'img,table', collapsed: false, styles: {'float': 'left'}}
				],

				aligncenter: [
					{selector: 'figure,p,h1,h2,h3,h4,h5,h6,td,th,tr,div,ul,ol,li', styles: {textAlign: 'center'}, defaultBlock: 'div'},
					{selector: 'img', collapsed: false, styles: {display: 'block', marginLeft: 'auto', marginRight: 'auto'}},
					{selector: 'table', collapsed: false, styles: {marginLeft: 'auto', marginRight: 'auto'}}
				],

				alignright: [
					{selector: 'figure,p,h1,h2,h3,h4,h5,h6,td,th,tr,div,ul,ol,li', styles: {textAlign: 'right'}, defaultBlock: 'div'},
					{selector: 'img,table', collapsed: false, styles: {'float': 'right'}}
				],

				alignjustify: [
					{selector: 'figure,p,h1,h2,h3,h4,h5,h6,td,th,tr,div,ul,ol,li', styles: {textAlign: 'justify'}, defaultBlock: 'div'}
				],

				bold: [
					{inline: 'strong', remove: 'all'},
					{inline: 'span', styles: {fontWeight: 'bold'}},
					{inline: 'b', remove: 'all'}
				],

				italic: [
					{inline: 'em', remove: 'all'},
					{inline: 'span', styles: {fontStyle: 'italic'}},
					{inline: 'i', remove: 'all'}
				],

				underline: [
					{inline: 'span', styles: {textDecoration: 'underline'}, exact: true},
					{inline: 'u', remove: 'all'}
				],

				strikethrough: [
					{inline: 'span', styles: {textDecoration: 'line-through'}, exact: true},
					{inline: 'strike', remove: 'all'}
				],

				blockquote: {block: 'blockquote', wrapper: 1, remove: 'all'},
				subscript: {inline: 'sub'},
				superscript: {inline: 'sup'},

                code: {inline: 'code'},

				link: {inline: 'a', selector: 'a', remove: 'all', split: true, deep: true,
					onmatch: function() {
						return true;
					},

					onformat: function(dom, elm, fmt, vars) {
						each(vars, function(value, key) {
							dom.setAttrib(elm, key, value);
						});
					}
				},

				removeformat: [
					{
						selector: 'b,strong,em,i,font,u,strike,sub,sup,dfn,code,samp,kbd,var,cite,mark,q,del,ins',
						remove: 'all',
						split: true,
						expand: false,
						block_expand: true,
						deep: true
					},
					{selector: 'span', attributes: ['style', 'class'], remove: 'empty', split: true, expand: false, deep: true},
					{selector: '*', attributes: ['style', 'class'], split: false, expand: false, deep: true}
				]
			};

			// Register default block formats
			each('p h1 h2 h3 h4 h5 h6 div address pre div dt dd samp'.split(/\s/), function(name) {
                general_formats[name] = {block: name, remove: 'all'};
			});


var portal_formats =   {

			};


var valid_classes = {};
var valid_attributes = {};
var valid_attributes = {};

}