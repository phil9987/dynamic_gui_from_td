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
        actions = self.__extract_actions(jsonld_td)
        events = self.__extract_events(jsonld_td)
        properties = self.__extract_properties(jsonld_td)
        http_forms = self.__extract_http_methods(actions, properties, events)
        html_generator = HtmlGenerator()
        action_parse_res = self.__map_actions_to_ui_elements(jsonld_td, actions, http_forms, html_generator)
        # TODO: also parse events and properties, this has not yet been implemented
        full_html = html_generator.generate_ui_for_thing(jsonld_td.get("title"))
        print(full_html)
        return full_html

    def __extract_semantic_type_mapping(self, jsonld):
        semantic_type = jsonld.get('@type')
        if semantic_type:
            semantic_type = semantic_type.lower()
            print("Found semantic type {}".format(semantic_type))
            mapping = self.get_mapping_for_semantic_type(semantic_type)
            if mapping:
                print("Found mapping!")
                return semantic_type, mapping
        # No semantic type or no match was found
        return None, None

    def __generate_ui_elements_from_semantic_type_mapping(self, main_json_td, semantic_type, mapping, html_generator):
        print("applying semantic type mapping {}".format(semantic_type))
        # TODO: check if sub-semantic-types exist, for PoC we just assume they do
        print(mapping)
        print(mapping.get('title'))
        trigger_el = mapping.get('triggerElement')
        trigger_infos = self.__extract_trigger_infos(mapping, main_json_td, semantic_type)
        ui_elements = mapping.get('uiElements')
        for json_ui_el in ui_elements:
            ui_el = json_ui_el.get('uiElement')
            if ui_el == 'ordered_domain_fixed_range_input':
                min_ = json_ui_el.get('min')
                max_ = json_ui_el.get('max')
                if trigger_el == json_ui_el.get('id'):
                    html_generator.add_fixed_range_ordered_domain(json_ui_el.get('id'), mapping.get('title'), min_, max_, min_, trigger_infos)
                else:
                    html_generator.add_fixed_range_ordered_domain(json_ui_el.get('id'), mapping.get('title'), min_, max_, min_)
            elif ui_el == 'ordered_domain_input':
                html_generator.add_general_input(json_ui_el.get('id'), json_ui_el.get('designator'))
            elif ui_el == 'stateless_trigger_button':
                print("DEBUG: stateless trigger button is being created")
                if trigger_el == json_ui_el.get('id'):
                    html_generator.add_trigger_button(json_ui_el.get('id'), json_ui_el.get('designator'), trigger_infos)
                else:
                    print("ERROR: trigger button is not trigger element!!")

            elif ui_el == 'move_input':
                # TODO: for roller shutter example
                ''

    def __extract_trigger_infos(self, mapping, main_json_td, semantic_type):
        # TODO: also consider output elements, currently this assumes that the mapping only maps to input elements, i.e. the semantic types are always in 'to'
        iris = []
        for i, t in enumerate(mapping.get('to')):
            arg, iri = self.__find_semantic_type_infos_in_action_input(t, main_json_td)
            if mapping.get('aggregationFunction'):
                ''
                # TODO: add aggregation function info
                from_type = 'aggregationFunctionRes_{}'.format(i)
            else:
                # 'from' maps 1:1 to 'to'
                from_type = mapping.get('from')[i]
            iri.add_arg(arg, from_type)
            iris.append(iri)
        return iris

    def __find_semantic_type_infos_in_action_input(self, semantic_type, json_td):
        for action_name, a in json_td.get('actions').items():
            input_ = a.get('input')
            input_type = input_.get('type')
            action_semantic_type = a.get('@type')
            if input_type == 'object':
                # for now we only consider one layer of nesting
                for property_name, p in input_.get('properties').items():
                    current_semantic_type = p.get('@type')
                    if (action_semantic_type and action_semantic_type.lower() == semantic_type.lower()) or (current_semantic_type and current_semantic_type.lower() == semantic_type.lower()):
                        # this is the parameter we we were looking for!
                        return property_name, self.http_forms.get('action_' + action_name)
            else:
                print("ERROR: Unclear how the input has to be provided to the api as no designator is provided in the TD")
        print("ERROR, semantic type could not be mapped to action input element")
        return None, None




    def __extract_http_methods(self, actions, properties, events):
        http_forms = {}
        for action_name, a in actions.items():
            for form in a.get('forms'):
                http_forms['action_' + action_name] = HttpForm(action_name, form, isAction=True)

        for property_name, p in properties.items():
            for form in p.get('forms'):
                http_forms['property_' + property_name] = HttpForm(property_name, form)

        for event_name, e in events.items():
            for form in e.get('forms'):
                http_forms['event_' + property_name] = HttpForm(event_name, form)

        for name, f in http_forms.items():
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
        html_generator.add_fixed_range_ordered_domain(json_key, json_key, min_, max_, min_)

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

    def __map_actions_to_ui_elements(self, jsonld_td, actions, http_forms, html_generator):
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
        semantic_type, mapping = self.__extract_semantic_type_mapping(jsonld_td)
        if semantic_type:
            # for now we only check for semantic types on the top level of the TD, this might be also useful on a more finegrained level, i.e. per action
            self.__generate_ui_elements_from_semantic_type_mapping(jsonld_td, semantic_type, mapping, html_generator)
        else:
            for action_name, a in actions.items():
                input_ = a.get("input")
                # TODO: handle output
                # output_ = a.get("output")
                # TODO: should different actions be put into separate <div> containers?
                self.__map_to_input_ui_elements(action_name, input_, html_generator)
                num_ui_elements = html_generator.get_and_reset_count()
                if num_ui_elements > 1:
                    # trigger button necessary, because there are multiple inputs for a single action
                    html_generator.add_trigger_button('action_' + action_name, action_name, (a.get("forms")[0].get('href'), "{} arguments".format(num_ui_elements)))

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

    def __map_properties_to_ui_elements(self, http_forms):
        '''
            According to w3c standard: "Property instances are also instances of the class DataSchema.
            Therefore, it can contain the type, unit, readOnly and writeOnly members, among others."
        '''
        for property_name, p in self.properties.items():
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

    def __map_events_to_ui_elements(self, http_forms):
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
    with open('./lampThing.html', 'w') as f:
        f.write(ui_generator.generate_html_ui_from_file('./tds/lampThingSampleTD.json'))
    with open('./robotArmThing.html', 'w') as f:
        f.write(ui_generator.generate_html_ui_from_file('./tds/poppyErgoJr_RobotArm_TD.json'))

if __name__== "__main__":
    main()