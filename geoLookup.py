#%%

import pandas as pd 
import numpy as np
import country_converter as coco
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
#%%
class geoLookup:
    def __init__(self, name="lookUp"):
        self.name = name
        self.longitude = []
        self.latitude = []
    
    def findGeocode(self, country_name, country_code):
       
        # try and catch is used to overcome
        # the exception thrown by geolocator
        # using geocodertimedout  
        try:
            # Specify the user_agent as your
            # app name it should not be none
            geolocator = Nominatim(user_agent="your_app_name")
            return geolocator.geocode(country_name, country_codes=country_code)
        except GeocoderTimedOut:
            return np.nan   

    def convrt2code(self, country_in):
        iso2_codes = coco.convert(country_in, to='ISO2')
        return iso2_codes

    def get_lat(self, country_name):
        lat = self.findGeocode(country_name, self.convrt2code(country_name)).latitude
        return lat

    def get_long(self, country_name):
        long = self.findGeocode(country_name, self.convrt2code(country_name)).longitude
        return long

