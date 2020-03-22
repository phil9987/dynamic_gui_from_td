class HttpForm:
    def __init__(self, name, jsonld_description, isAction=False):
        #print(jsonld_description)
        self.name = name
        self.endpoint = jsonld_description.get('href', '')
        self.content_type = jsonld_description.get('contentType', '')
        self.http_methods = []
        if 'htv:methodName' in jsonld_description:
            self.http_methods.append(jsonld_description.get('htv:methodName'))
        elif isAction:
            self.http_methods.append('POST') #default for action acc. to w3c
        elif 'op' in jsonld_description:
            # default for these operations according to w3c standard
            ops = jsonld_description.get('op')
            if type(ops) is str:
                ops = [ops]
            for op in ops:
                if op in {'readproperty', 'readallproperties', 'readmultipleproperties'}:
                    self.http_methods.append('GET')
                elif op in {'writeproperty', 'writeallproperties', 'writemultipleproperties'}:
                    self.http_methods.append('PUT')
                elif op == 'invokeaction':
                    self.http_methods.append('POST')
                elif op in {'subscribeevent', 'unsubscribeevent'}:
                    print(jsonld_description)
                    if 'subprotocol' in jsonld_description:
                        self.http_methods.append(jsonld_description.get('subprotocol'))
                    else:
                        print("ERROR: httpmethod of subscribeevent and unsubscribeevent not clearly defined")
                else:
                    print("ERROR: no http method assigned for op " + op)

    def __str__(self):
        res = "Http_Form '" + self.name + "'\nendpoint: " + self.endpoint + "\ncontent_type: " + self.content_type + "\nhttp_methods: "
        for h in self.http_methods:
            res += h + ', '
        return  res