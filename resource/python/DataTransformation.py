import dataiku
from dataiku import os
import json
import os
import logging

# -*- coding: utf-8 -*-
'''
Copyright © 2018 by Teradata.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

FUNCTION_CATEGORY="Data Transformation"

def getConnectionParamsFromDataset(inputDataset):
    return inputDataset.get_location_info(sensitive_info=True)['info']

# paylaod is sent from the javascript's callPythonDo()
# config and plugin_config are the recipe/dataset and plugin configured values
# inputs is the list of input roles (in case of a recipe)
def do(payload, config, plugin_config, inputs):
    map = json.loads(open('%s/mapping.json' % (os.getenv("DKU_CUSTOM_RESOURCE_FOLDER"))).read())
    files = [function["file_name"] for function in map if function["category"] == config['category']]
    
    choices = []
    for fle in files:
        try:
            print('=====================================' + fle + '================================')
            f = json.loads(open('%s/data/%s' % (os.getenv("DKU_CUSTOM_RESOURCE_FOLDER"), fle)).read())
            d = {"name":"",
                 "output_tables":"",
                 "arguments":"",
                 "asterarguments":"",
                 "partitionInputKind":[],
                 "partitionAttributes":"",
                 "isOrdered":False,
                 "orderByColumn":"",
                 "hasInputTable":False,
                 "isQueryMode": False,
                 "queries": []
                }
            keys = f.keys()
            required_input = []
            d['partitionInputKind']
            unaliased_inputs = {'desc':{}, 'values':[], 'count':0}
            if 'function_name' in keys:
                # d["name"]=f['function_name'].upper()
                d["name"]=f['function_name']
            if 'input_tables' in keys:
                d["hasInputTable"] = True
                input_tab_lst = f['input_tables']
                for input_tab in input_tab_lst:
                    required_input_dict = {"isRequired": True, "partitionAttributes":"", "orderByColumn": ""}
                    if 'isRequired' in input_tab.keys():
                        required_input_dict['isRequired'] = input_tab['isRequired']
                    if 'requiredInputKind' in input_tab.keys():
                        partitionByKey = next(iter(x for x in input_tab.get('requiredInputKind',[])), '')
                        if 'partitionByOne' in input_tab.keys() and input_tab['partitionByOne']:
                            partitionByKey = "PartitionByOne"
                        required_input_dict['kind'] = partitionByKey
                        required_input_dict['inputKindChoices'] = input_tab.get('requiredInputKind',[])
                    if 'isOrdered' in input_tab.keys():
                        required_input_dict['isOrdered'] = input_tab['isOrdered']
                    if 'name' in input_tab.keys() or ('Dimension' in input_tab.get('requiredInputKind',[]) and 0 < unaliased_inputs.get('count',0)):
                        required_input_dict['name'] = input_tab.get('name', 'Dimension')
                        required_input_dict['value'] = ""
                        required_input.append(required_input_dict)
                    else:
                        unaliased_inputs['count'] += 1
                        d["isOrdered"] = input_tab['isOrdered'] if 'isOrdered' in input_tab else False
                        d['partitionInputKind'] = ['PartitionByOne'] if 'partitionByOne' in input_tab.keys() and input_tab['partitionByOne'] else input_tab['requiredInputKind'] if 'requiredInputKind' in input_tab else []
            d["required_input"] = required_input
            d["unaliased_inputs"] = unaliased_inputs

            # Copied Argument clauses code
            if 'output_tables' in keys:
                ot = []
                out_tbl_lst = f['output_tables']
                for table in out_tbl_lst:
                    outtbl = {"name":"","isRequired":"","value":"", "datatype": "", "allowsLists":True}
                    if table.get('alternateNames', []):
                        outtbl["name"] = table.get('alternateNames', [''])[0]
                        # arg["name"] = argument.get('alternateNames', [''])[0].upper()
                    elif 'name' in table.keys():
                        outtbl["name"]=table['name']
                        # arg["name"]=argument['name'].upper()  
                    if 'isRequired' in table.keys():
                        outtbl["isRequired"]=table['isRequired']
                    if 'datatype' in table.keys():
                        outtbl["datatype"]=table['datatype']
                    if 'allowsLists' in table.keys():
                        outtbl["allowsLists"]=table['allowsLists']
                    if 'targetTable' in table.keys():
                        outtbl["targetTable"] = table['targetTable']
                    if 'isOutputTable' in table and table['isOutputTable']:
                        outtbl["isOutputTable"] = table['isOutputTable']
                    if 'defaultValue' in table:
                        outtbl["value"] = defaultValuesFromArg(table)
                    if 'permittedValues' in table:
                        outtbl["permittedValues"] = table['permittedValues']
                    ot.append(outtbl)
                d["output_tables"]=ot

            if 'argument_clauses' in keys:
                a = []
                arg_lst = f['argument_clauses']
                for argument in arg_lst:
                    arg = {"name":"","isRequired":"","value":"", "datatype": "", "allowsLists":True}
                    if argument.get('alternateNames', []):
                        arg["name"] = argument.get('alternateNames', [''])[0]
                        # arg["name"] = argument.get('alternateNames', [''])[0].upper()
                    elif 'name' in argument.keys():
                        arg["name"]=argument['name']
                        # arg["name"]=argument['name'].upper()  
                    if 'isRequired' in argument.keys():
                        arg["isRequired"]=argument['isRequired']
                    if 'datatype' in argument.keys():
                        arg["datatype"]=argument['datatype']
                    if 'allowsLists' in argument.keys():
                        arg["allowsLists"]=argument['allowsLists']
                    if 'targetTable' in argument.keys():
                        arg["targetTable"] = argument['targetTable']
                    if 'isOutputTable' in argument and argument['isOutputTable']:
                        arg["isOutputTable"] = argument['isOutputTable']
                    if 'defaultValue' in argument:
                        arg["value"] = defaultValuesFromArg(argument)
                    if 'permittedValues' in argument:
                        arg["permittedValues"] = argument['permittedValues']
                    a.append(arg)
                d["arguments"]=a
            if 'cascaded_functions' in keys:
                d["cascaded_functions"] = f['cascaded_functions']
            choices.append(d);
        except ValueError, e:
            logging.info("file is not valid json");
            
    print('=====================================end of ' + fle + '================================')

    # Get input table metadata.
    input_table_name = inputs[0]['fullName'].split('.')[1]
    input_dataset =  dataiku.Dataset(input_table_name)
    schema = input_dataset.read_schema()
    
    print('was able to obtain input schemas')
    
    inputschemas = {}
    for inputdataset in inputs:
        inputtablename = inputdataset['fullName'].split('.')[1]
        inputdataset = dataiku.Dataset(inputtablename)
        inputschemas[inputtablename] = inputdataset.read_schema()
        
    print('was able to forloop input schemas')
        

    # AAF schema from connection details
    connection = getConnectionParamsFromDataset(input_dataset)
    aafschema = ([property.get('value', '') for property in connection.\
                  get('connectionParams', {}).get('properties', {})
          if 'aafschema_700' == property.get('name', '')] or ['']).pop()

    return {'choices' : choices,
            'schema': schema,
            'inputs': inputs,
            'inputschemas': inputschemas,
            'aafschema': aafschema}

def isMultipleTagsInput(item):
    # if argument datatype is not column or table, and if it allows lists and it has no permitted value,
    # then argument values must be delimited by the null character
    return item.get('datatype', 'STRING') in ['STRING','DOUBLE','INTEGER','DRIVER','SQLEXPR', 'LONG']\
        and item.get('allowsLists', False)\
        and not item.get('permittedValues', [])

def defaultValuesFromArg(item):
    print('A - returning defaultvalues from ' + item.get('name', ''))
    defaultvalues = item.get('defaultValue', '')
    if isMultipleTagsInput(item) and isinstance(defaultvalues, (list, tuple)):
        DELIMITER = chr(0)
        return DELIMITER.join(str(x) for x in defaultvalues)
        print('B - returning defaultvalues from ' + item.get('name', ''))
    print('C - returning defaultvalues from ' + item.get('name', ''))
    #if isinstance(defaultvalues, basestring):
    #   defaultvalues = json.dumps(defaultvalues)
    return defaultvalues