# -*- coding: utf-8 -*-
"""
Created on Wed May 11 10:07:27 2022

@author: Trevor Gratz trevor.gratz@piercecountywa.gov

This file pulls creates a function to easily make api calls to the American 
Community Survey's Data Profile tables. 

NOTE: The zip code geography doesn't allow for subsetting in its current form.

"""
import requests as req
import io
import pandas as pd

class ACS():
    def __init__(self, cen_key=''):
        
        '''
        A class for making API calls to the American Community Survey 
        Data Profiles, Detailed tables, and Subject tables data products.
        
        Accepts a Census API key upon initialization, or can be reset by 
        accessing the cen_key attribute. 
        
        Stores a list of API calls made. Useful for documentation and for 
        debugging.
        
        Primary function is the "call" function. The rest of the functions are
        helper functions.
        
        '''
        
        self.cen_key = cen_key
        self.calls_list = []
        # I WANT TO MAKE A CHANGE.

        

    def call(self, geography='county', year='2020', acsversion='5', variables=[],
                   state=['*'], county =['*'], place =['*'], tract=['*'],
                   blockgroup =['*']):
        
        '''
        This function makes api calls to the American Community Survey's Data 
        Product (Data Profiles, Detailed Tables, and Subject Tables). 
        
    
        Parameters
        ----------
        geography : TYPE string
            DESCRIPTION. Determines what level to grab the data at, options are
                        'state', 'county', 'tract', 'blockgroup',  'zip'. The
                        other location based variables (state, county, place,
                        tract, and blockgroup) specify which of the desired 
                        geographies to collect. For example, if you want all
                        counties within Washington, the geography variable
                        would be set to 'county' and the state variables would
                        be set to '53'. More on this and examples below.
                        
                        The default is 'county'. blockgroups can only be 
                        specified when performing a call to the detailed 
                        tables. Zips cannot be subsetted by state
                        or county.
                        
        year : TYPE, string
            DESCRIPTION. What ACS year of the dataset to grab The default is
                        '2020'. 
                        
        acsversion : TYPE, optional
            DESCRIPTION. Options are 5 or 1. The default is '5'.
            
        variables : TYPE, list of strings
            DESCRIPTION. This allows the user to select individual or multiple
                          variables. For example, ['DP03_0001E', 'B03002_001E']
                          selects two variables from two different data tables
                          and different data products (the Data Profiles and the
                          Detailed tables). To select the entire table, just
                          feed the variables list the name of the table. In the 
                          above example this would mean setting the variables 
                          argument to ['DP03', 'B03002']. The documentation in
                          this repository should provide a primer on how to
                          find the variables and tables you are intersted in.
                          
                          
        state : TYPE List of strings, optional
            DESCRIPTION. A list of fips state codes. The default is ['*'].
                         Washington State's FIPS is '53'.
            
        county : TYPE List of strings , optional
            DESCRIPTION. A list of fips county codes. The default is ['*'].
                         Pierce County's FIPs is '053'. Double 53s yay!
            
        place : TYPE List of strings , optional
            DESCRIPTION. A list of fips place codes. The default is ['*'].
            When using a list of places, you must provide the state fips codes
            that the place is nested under. For this reason, only places from
            a single state can be pulled at this time.
            
        tract : TYPE List of strings, optional
            DESCRIPTION. List of fips tract codes. The default is ['*'].
            
        blockgroup : TYPE List of strings, optional
            DESCRIPTION. List of fips blockgroup codes. The default is ['*'].

    
        Returns
        -------
        outdf : Pandas dataframe containing data.
    
        Examples
        -------
        
        # Calling different geographies
        
        e1 = ACS().call(geography='state', year='2020', acsversion='5',
                        variables=['DP04_0005E'])
        
        e2 = ACS().call(geography='county', year='2020', acsversion='5',
                          variables=['DP04_0005E'])
        
        e3 = ACS().call(geography='county', year='2020', acsversion='5',
                        variables=['DP04_0005E'],
                        county=['053'], state = ['53'])
        
        e4= ACS().call(geography='place', year='2020', acsversion='5',
                       variables=['DP04_0001E'], place=['00135'], state=['53'])
    
        # Calling all nested geographies under specified higher geo levels. 
        
        e5 = ACS().call(geography='county', year='2020', acsversion='5',
                        county=['*'], state = ['53', '41'],
                        variables = ['DP02_0001E', 'DP04_0005E']) 
    
        # Calling across tables
        
        e6 = ACS().call(geography='county', year='2020', acsversion='5',
                        variables = ['DP02_0001E', 'B03002_004E',
                                     'S0101_C01_001E'], 
                        county='*', state = '53')
        
        # Calling entire tables
        
        e7 = ACS().call(geography='county', year='2020', acsversion='5',
                        variables = ['DP02', 'B03002',
                                     'S0101'], 
                        county='*', state = '53')

    '''
        
        
        basecall = f'https://api.census.gov/data/{year}/acs/acs{acsversion}'
        
        # Process variables into a table: [Variable] dictionnary
        vdict = self.process_variables(varls=variables)
        
        # Convert the geography variables into API text.
        geo = self.process_geography(geography=geography, state=state,
                                county=county, place=place, tract=tract)
        
        # Initialize the storage DF
        outdf = pd.DataFrame(columns=['NAME', 'state', 'county', 'tract',
                                      'block group',
                                      'zip code tabulation area'])
        
        # Loop through tables in the dictionary and make the API calls
        for table, vrs in vdict.items():
            
            # Is the table a Data Profile, Detailed table, or Subject Table
            if table[0] == 'D':
                product = r'/profile'
            elif table[0] == 'B':
                product = r''
            elif table[0] == 'S':
                product = '/subject'
            else:
                raise Exception('The variables provided do not appear to have names that confirm to the three data produce naming conventions.')

            # If only a table name was provided in the variables call,
            # pull the entire table.
            # Entire Table
            if len(vrs) == 0:
                updatecall = basecall + f'{product}?get=group({table})&{geo}'
            # Non-missing variable list
            else:
                if len(vrs) > 8 :
                    raise Exception('Unfortunately, we are limited to 8 variables per call, try calling the whole table or looping through calls')
                vrs = ','.join(vrs).upper()
                updatecall = basecall + f'{product}?get=NAME,{vrs}&{geo}'
            
            # If provided add the Census Key
            if self.cen_key != '':
                updatecall = updatecall + f'&key={self.cen_key}'
        
            # Finally, time to execute our API call.
            tempdf = self.execute_call(apicall=updatecall)
            
            # Variables to merge our tempdf to our storage df, if they exist.
            mvars = [i for i in tempdf.columns if i in ['NAME', 'state', 'county', 'tract',
                                                    'block group', 'zip code tabulation area']]
            outdf = pd.merge(outdf, tempdf, on = mvars, how='outer')
            
        return outdf

    def process_variables(self, varls):
        '''
        Create a dictionary where the keys are the tables the varialbe belong
        to and the values are the variable nested under those tables.
        '''
        # If a single variable is entered as a sting, convert to a list
        if type(varls) == str: varls=[varls]
        
        tset = {v.split('_')[0] for v in varls}      
        storedict = {t:[] for t in tset}
        for t in tset:
            varset = [v for v in varls if ((t in v) and (t != v))]
            storedict[t] = varset
        
        return storedict
            
    def process_geography(self, geography='county', state=['*'], county =['*'],
                          place =['*'], tract=['*']):
        
        # If geography variables are entered as single strings, convert to list
        if type(state) == str: state=[state]
        if type(county) == str: county=[county]
        if type(place) == str: place=[place]
        if type(tract) == str: tract=[tract]
        
        state = ','.join(state)
        county = ','.join(county)
        place = ','.join(place)
        tract = ','.join(tract)
        
        # Currently supports pulling states, counties, and tracts
        if geography == 'state':
            geo = f'for=state:{state}'

        elif geography == 'county':
            geo = f'for=county:{county}&in=state:{state}'

        elif geography == 'place':
            geo = f'for=place:{place}&in=state:{state}'
            
        elif geography == 'tract':
            geo = f'for=tract:{tract}&in=state:{state}&in=county:{county}'
        
        elif geography == 'blockgroup':
            geo = f'for=block%20group:*&in=state:{state}&in=county:{county}'
        
        elif geography == 'zip':
            geo = r'for=zip%20code%20tabulation%20area:*'
        
        return geo

    def execute_call(self, apicall):
        
        self.calls_list.append(apicall)
        
        # Try three times incase there is a browser connection issue
        counter = 0
        success = False
        while ((counter < 3) & (success == False)):
            
            try:
                r = req.get(apicall)
                rawdata = pd.read_json(io.StringIO(r.content.decode('utf-8')))
                rawdata.columns = rawdata.iloc[0]
                rawdata = rawdata.drop(index=0)
                success = True
            except:
                counter += 1
        if counter == 3:
            raise Exception('Errored out on the request. Please examine the API call in the .calls_list atribute')
        return rawdata
