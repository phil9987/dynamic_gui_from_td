import json
from string import Template

from HttpForm import HttpForm
'''
ui_outputs = {'general_data_output',
               'ordered_domain_output',
               'fixed_range_ordered_domain_output'
             }
ui_inputs = {'stateless_trigger_button',
               'stateless_forward_backward_buttons',
               'general_data_input',
               'ordered_domain_input',
               'ordered_domain_with_neutral_value_input',
               'operating_mode_input',
               'ordered_domain_fixed_range_input',
               'boolean_switch_input',
               'set_position_input',
               'move_input'
            }
'''
class UserInterfaceGenerator:
    def __init__(self):
        print("UI generator successfully initialized")

    def generate_html_ui_from_file(self, path):
        with open(path, 'r') as f:
            jsonld_input = json.load(f)
            return self.generate_html_ui(jsonld_input)

    def generate_html_ui(self, jsonld_td):
        self.actions = self.__extract_actions(jsonld_td)
        self.events = self.__extract_events(jsonld_td)
        self.properties = self.__extract_properties(jsonld_td)
        self.http_forms = self.__extract_http_methods()
        action_parse_res = self.__parse_actions(self.actions, self.http_forms)
        html_base = Template(self.html_base_template.safe_substitute(header=self.container_style_string))

        html_body = ''
        html_script = ''
        for action_name, html_ui_elements in action_parse_res:
            print("adding html elements for action {}".format(action_name))
            for html_part, js_part in html_ui_elements:
                html_body += html_part
                html_script += js_part
        # TODO: should different actions be put into separate <div> containers?

        html_body = self.container_template.substitute(container_title=jsonld_td.get("title"), container_content=html_body)

        html_body += self.script_template.substitute(js_content=html_script)

        full_html = html_base.substitute(body=html_body)
        print(full_html)
        return full_html

    def __extract_http_methods(self):
        http_forms = []
        for action_name, a in self.actions.items():
            for form in a.get('forms'):
                http_forms.append(('action', HttpForm(action_name, form, isAction=True)))

        for property_name, p in self.properties.items():
            for form in p.get('forms'):
                http_forms.append(('property', HttpForm(property_name, form)))

        for event_name, e in self.events.items():
            for form in e.get('forms'):
                http_forms.append(('event', HttpForm(event_name, form)))
        for name, f in http_forms:
            print(name + " " + str(f))
        self.http_forms = http_forms
        return http_forms

    # TODO: parse data types and together with Http_Form data, determine corresponding UI element
    # property: type; if type==object, then it's nested!
    # action: (input & output)->type; if type==object, then it's nested!
    # event: data->type (this is the type that is being received)
    def __extract_actions(self, jsonld_input):
        return jsonld_input.get('actions', {})

    def __extract_events(self, jsonld_input):
        return jsonld_input.get('events', {})

    def __extract_properties(self, jsonld_input):
        return jsonld_input.get('properties', {})

    def __parse_uri_variables(self, jsonld):
        '''
            part of InteractionAffordance, same level as forms and connected to forms (no uriVariables without forms)

            e.g.

            "uriVariables": {
                    "p" : { "type": "integer", "minimum": 0, "maximum": 16, "@type": "eg:SomeKindOfAngle" },
                    "d" : { "type": "integer", "minimum": 0, "maximum": 1, "@type": "eg:Direction" }
            },
            "forms": [{
            "href" : "http://192.168.1.25/left{?p,d}",
            "htv:methodName": "GET"
            }]
        '''
        # not essential for now. TODO: implement later
        return None

    def __extract_data_description(self, jsonld):
        type_ = jsonld.get("type")
        min_ = jsonld.get("minimum")
        max_ = jsonld.get("maximum")
        ordered = False
        if type_ in {"integer", "number"}:
            # TODO: is boolean also ordered?
            ordered = True
        return {"type": type_, "ordered": ordered, "min": min_, "max": max_}

    def __map_array_type_input(self, jsonld):
        '''
        In general, arrays can be displayed and entered in a general data field by comma separated values.
        If the number of items is fixed and the types are known, a separate input field for each element could be displayed.
        The downside is, that the designators for each element is unknown, i.e. for RGB value in the example below it is clear
        if there is a single input field with description RGB value, 3 items, comma-separated. But it might be less clear
        if there are 3 input fields with only one title saying RGB values. Hence I would rather create a descriptive title
        and a single input field.

            "type": "array",
            "items" : {
                "type" : "number",
                "minimum": 0,
                "maximum": 255
            },
            "minItems": 3,
            "maxItems": 3
        '''
        data_description = self.__extract_data_description(jsonld.get("items"))
        minItems = jsonld.get("minItems")
        maxItems = jsonld.get("maxItems")
        if minItems and maxItems and minItems == maxItems:
            # a fixed number of elements
            data_description["num_elements"] = minItems
        elif minItems and maxItems:
            data_description["num_elements"] = "min{}_max{}".format(minItems, maxItems)
        # TODO: complete implementation, array type is omitted for the PoC

    def __map_number_type_input(self, json_key, jsonld):
        # for both integer and number
        '''
            "type": "number",
            "minimum": 0.0,
            "maximum": 100.0
        '''
        min_ = jsonld.get('minimum')
        max_ = jsonld.get('maximum')
        # TODO: handle case when it's not a range or only bounded to one side
        return self.__generate_html_for_slider(json_key, min_, max_, min_)

    def __map_object_type_input(self, jsonld):
        # recursively parse types
        '''
                "type": "object",
                "properties": {
                    "from": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "to": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "duration": {"type": "number"}
                },
                "required": ["to","duration"],
        '''
        props = jsonld.get('properties')
        ui_elements = []
        for p in props:
            ui_elements.append(self.__map_to_input_ui_elements(p, props.get(p)))
        return ui_elements

    def __map_to_input_ui_elements(self, json_key, jsonld):
        t = jsonld.get('type')
        # TODO: also check for enum
        if t == 'object':
            return self.__map_object_type_input(jsonld)
        elif t == 'integer' or  t == 'number':
            return self.__map_number_type_input(json_key, jsonld)
        else:
            print("type not yet supported: {}".format(t))
            return None

    def __parse_actions(self, actions, http_forms):
        '''
                Heuristics for actions:
                - no input -> simple trigger
                - input -> - single input -> single UI_input_element (no trigger button, interaction with UI_input_element automatically triggers action, except for general (string) input)
                        - multiple inputs -> for each input UI_input_element and trigger button to trigger action
                - output -> sensor outputs; or could it also render back into a stateful actuator?
                                            RE: might make sense for stateful actuators, i.e. request to change state
                                            to 10 and actuator does not change. Then input trigger-wheel will turn
                                            back to actual value. In the general case the output seems to be more something
                                            like a feedback. i.e. "success" or "error"
            "input": {
                "type": "object",
                "properties": {
                    "from": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "to": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "duration": {"type": "number"}
                },
                "required": ["to","duration"],
            },
            "output": {"type": "string"},


            "actions": {
            "dim" : {
                "@type": "saref:levelcontrolfunction",
                "input": {
                    "type": "object",
                    "properties": {
                        "from": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "to": {
                            "@type": "example:dimTarget",
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100
                        }                },
                    "required": ["to"]
                },
                "forms": [{
                    "href": "https://mylamp.example.com/dim"
                }]
            }
        }
        '''
        overall_res = []
        for action_name, a in actions.items():
            print(action_name)
            print(a)
            input = a.get("input")
            output = a.get("output")
            # TODO: handle output
            res = self.__map_to_input_ui_elements(action_name, input)
            if type(res) != list:
                res = [res]
            if len(res) > 1:
                # trigger button needed
                print("DEBUG: " + str(res))
                res.append(self.__generate_html_for_button(action_name, action_name, a.get("forms")[0].get('href'), "{} arguments".format(len(res))))
            overall_res.append((action_name, res))
        return overall_res

    html_base_template = Template('''
                                <!DOCTYPE html>
                                <html>
                                    <head>
                                        $header
                                    </head>
                                    <body>
                                        $body
                                    </body>
                                </html>''')

    container_template = Template('''<div class="container"><h4>$container_title</h4>$container_content</div>''')
    container_style_string = '''<style>
                            .container {
                                width: fit-content;
                                border: 2px solid;
                            }
                        </style>'''

    script_template = Template('''\n<script>$js_content</script>''')

    def __generate_html_for_slider(self, id, min, max, current):
        slider_template = Template('''<div><h5>$slider_title<h5><input id="$slider_id" type="range" min="$min" max="$max" value="$current" class="slider" /><p>Value: <span id="$output_id" /></p></div>''')
        slider_script_template = Template('''var $slider_id = document.getElementById("$slider_id");
                                var $output_id = document.getElementById("$output_id");
                                $output_id.innerHTML = $slider_id.value;
                                $slider_id.oninput = function() { $output_id.innerHTML = this.value;}
                                ''')
        html_body = slider_template.substitute(slider_title= id, slider_id=id, min=min, max=max, current=current, output_id=id+'_output')
        html_script = slider_script_template.substitute(slider_id=id, output_id=id+'_output')
        return html_body, html_script

    def __generate_html_for_general_input(self, designator, id):
        text_input_template = Template('''<label for="$id">$designator</label> <input type="text" id="$id" name="$id">''')
        return text_input_template.substitute(id=id, designator=designator), ""

    def __generate_html_for_button(self, id, text, trigger_api, trigger_payload):
        button_template = Template('''<button id=$id type="button" onclick="alert('sending request to $trigger_api with $trigger_payload')">$text</button>''')
        return button_template.substitute(id=id, trigger_api=trigger_api, trigger_payload=trigger_payload, text=text), ""


    html_base = Template(html_base_template.safe_substitute(header=container_style_string))


    def __parse_properties(self, http_forms):
        '''
            According to w3c standard: "Property instances are also instances of the class DataSchema.
            Therefore, it can contain the type, unit, readOnly and writeOnly members, among others."
        '''
        for property_name, p in self.properties.items():
            for form in p.get('forms'):
                http_forms.append(('property', Http_Form(property_name, form)))
            property_type = p.get('type')
            if property_type in {'array', 'string', 'number', 'integer', 'boolean'}:
                # TODO: simple type, infer UI element for each form?
                print("property of simple type")
            elif property_type ==  'object':
                # TODO: recursive type checking
                print("property of type object, recursively parsing...")
            elif property_type == 'null':
                # TODO: define what happens here
                print("property of type null...")

    def __parse_events(self, http_forms):
        '''
            subscription (optional): Defines data that needs to be passed upon subscription.
            data (optional): Defines the data schema of the Event instance messages pushed by the Thing.
            cancellation (optional): Defines any data that needs to be passed to cancel a subscription

            e.g.

            "subscription": {
                "type": "object",
                "properties": {
                    "callbackURL": {
                        "type": "string",
                        "format": "uri",
                        "description": "Callback URL provided by subscriber for Webhook notifications.",
                        "writeOnly": true
                    },
                    "subscriptionID": {
                        "type": "string",
                        "description": "Unique subscription ID for cancellation provided by WebhookThing.",
                        "readOnly": true
                    }
                }
            },
            "data": {
                "type": "number",
                "description": "Latest temperature value that is sent to the callback URL."
            },
            "cancellation": {
                "type": "object",
                "properties": {
                    "subscriptionID": {
                        "type": "integer",
                        "description": "Required subscription ID to cancel subscription.",
                        "writeOnly": true
                    }
                }
            },
        '''
        for event_name, e in self.events.items():
            for form in e.get('forms'):
                http_forms.append(('event', Http_Form(event_name, form)))
            event_output_type = e.get('data').get('type')
            if event_output_type in {'array', 'string', 'number', 'integer', 'boolean'}:
                # TODO: simple type, infer UI element for each form?
                print("simple type")
                pass
            elif event_output_type ==  'object':
                # TODO: recursive type checking
                print("object type")
            elif event_output_type == 'null':
                # TODO: define what happens here
                print("null type")


def main():
    ui_generator = UserInterfaceGenerator()
    ui_generator.generate_html_ui_from_file('./tds/lampThingSampleTD.json')
    ui_generator.generate_html_ui_from_file('./tds/poppyErgoJr_RobotArm_TD.json')

if __name__== "__main__":
    main()