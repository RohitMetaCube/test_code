'''
The components that can be filtered include:
postal_code         : matches postal_code and postal_code_prefix.
country             : matches a country name or a two letter ISO 3166-1 country code.
route               : matches the long or short name of a route.
locality            : matches against locality and sublocality types.
administrative_area : matches all the administrative_area levels.

ex:
https://maps.googleapis.com/maps/api/geocode/json?components=administrative_area:DC|country:US&key=YOUR_KEY
'''
from pymongo import MongoClient
import requests
import time
import csv

MONGODB_HOST = "mongodb1.dev.zippia.com"
MONGODB_PORT = 27017
MONGODB_NAME = "zippia"
LOCATION_COLLECTION = "location"
LOCATION_DISPLAY_PROPERTY_COLLECTION = "location_display_property"
STATE_CODE = "state_code"
STATE_NAME = "state"
PLACE = "place"
LOCATION_TYPE = "type"
POPULATION = "population"
GEO_LOC = "loc"
GEO_LOC_TYPE = "type"
GEO_LOC_TYPE_POINT = "Point"
GEO_COORDINATES = "coordinates"
STATE_POPULATION_FILE_PATH = 'dataFiles/states_population.csv'
db = MongoClient(MONGODB_HOST, MONGODB_PORT)[MONGODB_NAME]


class GeoCodeAPI:
    def __init__(self):
        self.BASE_URL = "https://maps.googleapis.com/maps/api/geocode"
        self.GOOGLE_GEO_CODE_API_KEY = 'AIzaSyBZd50nGuQbY-JbxPoKNKYZxENAjLmOM8o'
        self.MAX_RETRY_COUNTS = 1

    def geoCodeGenerator(self,
                         address=None,
                         components={
                             "administrative_area": None,
                             "country": None,
                             "postal_code": None,
                             "route": None,
                             "locality": None
                         },
                         response_type="json",
                         retry_counter=0):

        valid_components_count = sum(
            [1 if v else 0 for v in components.values()]) if components else 0
        url = "{}/{}?{}".format(self.BASE_URL, response_type, "&".join(([
            "address={}".format(address), "components={}".format(
                "|".join("{}:{}".format(k, v) for k, v in components.items()
                         if v)) if valid_components_count else ''
        ] if valid_components_count else ["address={}".format(
            address)]) if address else [
                "components={}".format("|".join("{}:{}".format(
                    k, v) for k, v in components.items() if v))
                if valid_components_count else ''
            ]))

        print url
        if address or valid_components_count:
            url += "&key={}".format(self.GOOGLE_GEO_CODE_API_KEY)
            r = requests.get(url)
            if r.status_code != 200 and retry_counter < self.MAX_RETRY_COUNTS:
                time.sleep(10)
                print "Going to Retry for Address: {}, Components: {}, with retryCounter: {}".format(
                    address, components, retry_counter + 1)
                r = self.geoCodeGenerator(
                    address=address,
                    components=components,
                    response_type=response_type,
                    retry_counter=retry_counter + 1)
            return (r.json() if r.status_code == 200 else {
                "status": "Unknown Error",
                "status_code": r.status_code
            }) if not isinstance(r, dict) else r
        else:
            print "Please Provide Valid Address."

    def test(self):
        print "TEST 1 ::: Only Components"
        r = self.geoCodeGenerator(
            components={"administrative_area": "DC",
                        "country": "US"})
        if r and r["status"] == "OK":
            print r['results'][0]['geometry']['location']

        print
        print "TEST 2 ::: Only Address"
        r = self.geoCodeGenerator(address='DC')
        if r and r["status"] == "OK":
            print r['results'][0]['geometry']['location']

        print
        print "TEST 3 ::: Both Address and Components"
        r = self.geoCodeGenerator(address="DC", components={"country": "US"})
        if r and r["status"] == "OK":
            print r['results'][0]['geometry']['location']

        print
        print "TEST 4 ::: None of the Address and Components used default"
        r = self.geoCodeGenerator()
        if r and r["status"] == "OK":
            print r['results'][0]['geometry']['location']

        print
        print "TEST 5 ::: Set both Address and Components as None"
        r = self.geoCodeGenerator(address=None, components=None)
        if r and r["status"] == "OK":
            print r['results'][0]['geometry']['location']


def read_state_populations(file_path=STATE_POPULATION_FILE_PATH):
    print "Going to Generate State Population Map ...."
    state_population_map = {}
    f = open(file_path, 'rb')
    fr = csv.DictReader(f)
    for row in fr:
        state_name = row["Geography"]
        population = row["Population Estimate (as of July 1) - 2017"]
        e = db[LOCATION_COLLECTION].find_one({
            STATE_NAME: {
                "$in": [
                    state_name, state_name.title(), state_name.lower(),
                    state_name.upper()
                ]
            }
        }, {STATE_NAME: 1})
        if e:
            state_population_map[e[STATE_NAME]] = int(
                population) if isinstance(population,
                                          (str, unicode)) else population
    print "State Population Map Generation Done"
    return state_population_map


def states_populator(geo_api, state_population_map):
    print "Going to Import States ... "
    state_codes = db[LOCATION_COLLECTION].distinct(STATE_CODE)
    success_counter = 0
    total_counter = 0
    for state_code in state_codes:
        total_counter += 1
        if state_code:
            e = db[LOCATION_COLLECTION].find_one({
                STATE_CODE: state_code,
                STATE_NAME: {
                    "$nin": [None, ""]
                }
            }, {STATE_NAME: 1})
            state_name = e[STATE_NAME] if e else ''
            state_data = {}
            state_data[STATE_CODE] = state_code
            state_data[STATE_NAME] = state_name
            state_data[PLACE] = state_name if state_name else state_code
            state_data[LOCATION_TYPE] = "state"
            state_data[POPULATION] = state_population_map[
                state_name] if state_name in state_population_map else None
            state_data[GEO_LOC] = {}
            r = geo_api.geoCodeGenerator(components={
                "administrative_area": state_code,
                "country": "US"
            })
            if not r or r["status"] != "OK":
                r = geo_api.geoCodeGenerator(address=state_name)
            state_data[GEO_LOC][GEO_COORDINATES] = [
                r['results'][0]['geometry']['location']['lng'],
                r['results'][0]['geometry']['location']['lat']
            ] if r and r["status"] == "OK" else None
            state_data[GEO_LOC][
                GEO_LOC_TYPE] = GEO_LOC_TYPE_POINT if state_data[GEO_LOC][
                    GEO_COORDINATES] else None
            location_id = db[LOCATION_COLLECTION].insert(state_data)
            db[LOCATION_DISPLAY_PROPERTY_COLLECTION].insert({
                'display_name': state_data[PLACE],
                'location_id': location_id
            })
            success_counter += 1
            print "Successfully Imported {} states out of {}  states.".format(
                success_counter, total_counter)
    print "Successfully Imported {} states out of {}  states.".format(
        success_counter, total_counter)


if __name__ == "__main__":
    geo_api = GeoCodeAPI()
    #geo_api.test()
    state_population_map = read_state_populations()
    states_populator(geo_api, state_population_map)
    print "Done"
