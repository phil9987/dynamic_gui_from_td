import json
from string import Template

from HttpForm import HttpForm
from HtmlGenerator import HtmlGenerator
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
    def __init__(self, mapping_file_path = ''):
        self.semantic_type_mapping = {}
        self.mapping = {}
        if mapping_file_path:
            with open(mapping_file_path, 'r') as f:
                json_mapping = json.load(f).get("mapping")
                self.mapping_id = 0
                for m in json_mapping:
                    target_types = m.get("targetTypes")
                    self.mapping[self.mapping_id] = m
                    for t in target_types:
                        self.semantic_type_mapping[t.lower()] = self.mapping_id
                    self.mapping_id += 1
        print("UI generator successfully initialized")

    def get_mapping_for_semantic_type(self, t):
        current_id = self.semantic_type_mapping.get(t, -1)
        if current_id >= 0:
            return self.mapping.get(current_id)
        return None

    def generate_html_ui_from_file(self, path):
        with open(path, 'r') as f:
            jsonld_input = json.load(f)
            self.jsonld_td_input = jsonld_input
            return self.generate_html_ui(jsonld_input)

    def generate_html_ui(self, jsonld_td):
        self.__scan_and_replace_semantic_type_mappings(jsonld_td)
        actions = self.__extract_actions(jsonld_td)
        events = self.__extract_events(jsonld_td)
        properties = self.__extract_properties(jsonld_td)
        http_forms = self.__extract_http_methods(actions, properties, events)
        html_generator = HtmlGenerator()
        action_parse_res = self.__parse_actions(actions, http_forms, html_generator)
        full_html = html_generator.generate_ui_for_thing(jsonld_td.get("title"))
        print(full_html)
        return full_html

    def __scan_and_replace_semantic_type_mappings(self, jsonld, parents = []):
            semantic_type = jsonld.get('@type')
            if semantic_type:
                semantic_type = semantic_type.lower()
            print("scanning semantic type {}".format(semantic_type))
            mapping = self.get_mapping_for_semantic_type(semantic_type)
            if mapping:
                self.__replace_semantic_type_mapping(jsonld, semantic_type, mapping, parents)
            for k, el in jsonld.items():
                if type(el) == dict:
                    # we can dive in further to search for semantic types
                    self.__scan_and_replace_semantic_type_mappings(jsonld[k], parents + [k])


    def __replace_semantic_type_mapping(self, main_json_td, semantic_type, mapping, parents):
        print("replacing semantic type mapping {} for parent {}".format(semantic_type, parents))
        # TODO: check if sub semantic types exist, for PoC we just assume they do
        html_generator = HtmlGenerator()
        parent_json = self.jsonld_td_input
        current_json = parent_json
        if parents:
            for p in parents[:-1]:
                parent_json = parent_json.get(p)
            print(parent_json)
            current_json = parent_json[parents[-1]]
        trigger_el = mapping.get('triggerElement')
        ui_elements = mapping.get('uiElements')
        for json_ui_el in ui_elements:
            ui_el = json_ui_el.get('uiElement')
            if ui_el == 'ordered_domain_fixed_range_input':
                min_ = json_ui_el.get('min')
                max_ = json_ui_el.get('max')
                if trigger_el == json_ui_el.get('id'):
                    trigger_infos = self.__extract_trigger_infos(json_ui_el, main_json_td, semantic_type, parents)
                    html_generator.add_fixed_range_ordered_domain(mapping.get('title'), min_, max_, min_, trigger_infos)
                else:
                    html_generator.add_fixed_range_ordered_domain(mapping.get('title'), min_, max_, min_)
            elif ui_el == 'ordered_domain_input':
                html_generator.add_general_input(json_ui_el.get('title'))
            elif ui_el == 'stateless_trigger_button':
                if trigger_el == json_ui_el.get('id'):
                    trigger_infos = self.__extract_trigger_infos(json_ui_el, main_json_td, semantic_type, parents)
                    html_generator.add_trigger_button('test', 'example.com', 'args', trigger_infos)
                else:
                    print("ERROR: trigger button is not trigger element!!")

            elif ui_el == 'move_input':
                # TODO: for roller shutter example
                ''
        json_ui_elements = html_generator.generate_json_ui_elements()
        if parents:
            # there is one or more parents, replace the part of the json object with the json_ui_elements

        else:
            # the whole td is being replaced by the mapping
            self.jsonld_td_input = json_ui_elements

    def __extract_trigger_infos(self, json_ui_el, main_json_td, semantic_type, parents):
        # TODO: extract api and form infos which are necessary to generate code for trigger element
        return ''


    def __extract_http_methods(self, actions, properties, events):
        http_forms = []
        for action_name, a in actions.items():
            for form in a.get('forms'):
                http_forms.append(('action', HttpForm(action_name, form, isAction=True)))

        for property_name, p in properties.items():
            for form in p.get('forms'):
                http_forms.append(('property', HttpForm(property_name, form)))

        for event_name, e in events.items():
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

    def __map_number_type_input(self, json_key, jsonld, html_generator):
        # for both integer and number
        '''
            "type": "number",
            "minimum": 0.0,
            "maximum": 100.0
        '''
        min_ = jsonld.get('minimum')
        max_ = jsonld.get('maximum')
        # TODO: handle case when it's not a range or only bounded to one side
        html_generator.add_fixed_range_ordered_domain(json_key, min_, max_, min_)

    def __map_object_type_input(self, jsonld, html_generator):
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
        for p in props:
            self.__map_to_input_ui_elements(p, props.get(p), html_generator)

    def __map_to_input_ui_elements(self, json_key, jsonld, html_generator):
        t = jsonld.get('type')
        # TODO: also check for enum
        if t == 'object':
            return self.__map_object_type_input(jsonld, html_generator)
        elif t == 'integer' or  t == 'number':
            return self.__map_number_type_input(json_key, jsonld, html_generator)
        else:
            print("type not yet supported: {}".format(t))
            return None

    def __parse_actions(self, actions, http_forms, html_generator):
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
            input_ = a.get("input")
            # TODO: handle output
            # output_ = a.get("output")
            # TODO: should different actions be put into separate <div> containers?
            self.__map_to_input_ui_elements(action_name, input_, html_generator)
            num_ui_elements = html_generator.get_and_reset_count()
            if num_ui_elements > 1:
                # trigger button necessary, because there are multiple inputs for a single action
                html_generator.add_trigger_button(action_name, a.get("forms")[0].get('href'), "{} arguments".format(num_ui_elements))

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
    ui_generator = UserInterfaceGenerator('./Mappings.json')
    ui_generator.generate_html_ui_from_file('./tds/lampThingSampleTD.json')
    ui_generator.generate_html_ui_from_file('./tds/poppyErgoJr_RobotArm_TD.json')

if __name__== "__main__":
    main()