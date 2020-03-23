
from string import Template
class HtmlGenerator:
    html_base_template = Template('''<!DOCTYPE html><html><head>$header</head><body>$body</body></html>''')
    container_template = Template('''<div class="container"><h4>$container_title</h4>$container_content</div>''')
    container_style_string = "<style>.container {width: fit-content; border: 2px solid;}</style>"
    script_template = Template('''\n<script>$js_content</script>''')
    html_base = Template(html_base_template.safe_substitute(header=container_style_string))

    def __init__(self):
        self.html_base = Template(self.html_base_template.safe_substitute(header=self.container_style_string))
        self.html_body = ''
        self.html_script = ''
        self.number_ui_elements = 0

    def get_and_reset_count(self):
        tmp = self.number_ui_elements
        self.number_ui_elements = 0
        return tmp

    def add_fixed_range_ordered_domain(self, id_, designator, min_, max_, current, trigger_infos = []):
        # TODO: add support to trigger action after user interaction
        print("adding fixed range ordered domain input {}".format(id_))
        self.__add_html_for_slider(id_, designator, min_, max_, current, trigger_infos)

    def add_trigger_button(self, id, name, trigger_infos):
        # TODO: add support to trigger action after user interaction
        trigger_description = ', '.join([a.describe_http_event() for a in trigger_infos])
        self.__add_stateless_trigger_button(name, name, trigger_description)

    def add_general_input(self, id, name):
        self.__add_html_for_general_input(id, name)

    def generate_ui_for_thing(self, name):
        self.html_body = self.container_template.substitute(container_title=name, container_content=self.html_body)
        self.html_body += self.script_template.substitute(js_content=self.html_script)
        return self.html_base.substitute(body=self.html_body)

    def __add_html_for_general_input(self, id, name):
        text_input_template = Template('''<label for="$id">$designator</label> <input type="number" id="$id" name="$id">''')
        self.html_body += text_input_template.substitute(id=id, designator=name)

    def __add_html_for_slider(self, id, title, min, max, current, trigger_infos):
        slider_template = Template('''<div><h5>$slider_title<h5><input id="$slider_id" type="range" min="$min" max="$max" value="$current" class="slider" /><p>Value: <span id="$output_id" /></p></div>''')
        slider_script_template = Template('''var $slider_id = document.getElementById("$slider_id");
                                var $output_id = document.getElementById("$output_id");
                                $output_id.innerHTML = $slider_id.value;
                                $slider_id.oninput = function() { $output_id.innerHTML = this.value;}
                                $slider_id.onchange = function() { alert('$trigger_descr');}

                                ''')
        trigger_description = ', '.join([a.describe_http_event() for a in trigger_infos])
        self.html_body += slider_template.substitute(slider_title= title, slider_id=id, min=min, max=max, current=current, output_id=id+'_output')
        self.html_script += slider_script_template.substitute(slider_id=id, output_id=id+'_output', trigger_descr=trigger_description)

    def __add_stateless_trigger_button(self, id, text, trigger_descr):
        button_template = Template('''<button id=$id type="button" onclick="alert('$trigger_descr')">$text</button>''')
        self.html_body += button_template.substitute(id=id, trigger_descr=trigger_descr, text=text)


