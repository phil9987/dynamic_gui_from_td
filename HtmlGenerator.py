
from string import Template
class HtmlGenerator:
    html_base_template = Template('''<!DOCTYPE html><html><head>$header</head><body>$body</body></html>''')
    container_template = Template('''<div class="container"><h4>$container_title</h4>$container_content</div>''')
    container_style_string = "<style>.container {width: fit-content; border: 2px solid;}</style>"
    script_template = Template('''\n<script>$js_content</script>''')

    def __init__(self):
        self.html_base = Template(self.html_base_template.safe_substitute(header=self.container_style_string))
        self.html_body = ''
        self.html_script = ''
        self.number_ui_elements = 0

    def get_and_reset_count(self):
        tmp = self.number_ui_elements
        self.number_ui_elements = 0
        return tmp

    def add_fixed_range_ordered_domain(self, id_, min_, max_, current):
        self.__add_html_for_slider(id_, min_, max_, current)

    def add_trigger_button(self, name, uri, arguments):
        self.__generate_html_for_button(name, name, uri, "arguments: {}".format(arguments))

    def generate_ui_for_thing(self, name):
        self.html_body = self.container_template.substitute(container_title=name, container_content=self.html_body)
        self.html_body += self.script_template.substitute(js_content=self.html_script)
        return self.html_base.substitute(body=self.html_body)

    def __add_html_for_slider(self, id, min, max, current):
        slider_template = Template('''<div><h5>$slider_title<h5><input id="$slider_id" type="range" min="$min" max="$max" value="$current" class="slider" /><p>Value: <span id="$output_id" /></p></div>''')
        slider_script_template = Template('''var $slider_id = document.getElementById("$slider_id");
                                var $output_id = document.getElementById("$output_id");
                                $output_id.innerHTML = $slider_id.value;
                                $slider_id.oninput = function() { $output_id.innerHTML = this.value;}
                                ''')
        self.html_body += slider_template.substitute(slider_title= id, slider_id=id, min=min, max=max, current=current, output_id=id+'_output')
        self.html_script += slider_script_template.substitute(slider_id=id, output_id=id+'_output')

    def __generate_html_for_general_input(self, designator, id):
        text_input_template = Template('''<label for="$id">$designator</label> <input type="text" id="$id" name="$id">''')
        return text_input_template.substitute(id=id, designator=designator), ""

    def __generate_html_for_button(self, id, text, trigger_api, trigger_payload):
        button_template = Template('''<button id=$id type="button" onclick="alert('sending request to $trigger_api with $trigger_payload')">$text</button>''')
        return button_template.substitute(id=id, trigger_api=trigger_api, trigger_payload=trigger_payload, text=text), ""


    html_base = Template(html_base_template.safe_substitute(header=container_style_string))