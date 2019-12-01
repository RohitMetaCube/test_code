'''
    Read file "data.json", 
        and write a recursive function 
        to convert every value of key "quantity" to 23gm, 50gm and 260gm, 
    presently data is given for 100gm.
'''

import json
import copy


def change_quantity(data, quantity_fraction):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == 'quantity':
                data[k] = v * quantity_fraction
            elif isinstance(v, (dict, list, set, tuple)):
                change_quantity(v, quantity_fraction)
    elif isinstance(data, (list, set, tuple)):
        for d in data:
            change_quantity(d, quantity_fraction)


def generate_new_data(original_data, quantity, original_quantity=100):
    new_data = copy.deepcopy(original_data)
    change_quantity(new_data, float(quantity) / original_quantity)
    return new_data


def create_new_file_with_some_more_grams(required_grams=[23, 50, 260],
                                         available_gram=100,
                                         source_file_path='datasets/data.json',
                                         sink_file_path='datasets/data2.json'):
    data = json.load(open(source_file_path))
    original_data = data['data']['{}gm'.format(available_gram)]
    for rgm in required_grams:
        data['data']['{}gm'.format(rgm)] = generate_new_data(
            original_data, quantity=rgm, original_quantity=available_gram)
    '''
    # Test Code
    print data['data']["100gm"]["calorie_info"]
    print 
    print data['data']["23gm"]["calorie_info"]
    print
    print data['data']["50gm"]["calorie_info"]
    print
    print data['data']["260gm"]["calorie_info"]
    '''

    json.dump(data, open(sink_file_path, 'wb'))


if __name__ == "__main__":
    create_new_file_with_some_more_grams()
    print "Done"
