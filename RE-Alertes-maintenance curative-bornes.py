# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 13:47:49 2022

@author: a2ste
"""

import pandas as pd 
import ast
import numpy as np
import os
import shutil
import datetime



def error_descriptions(array_of_error_code):
    #input : Error Code
    #output : description of error code
    #edit this function depending on the description of the error. For now, I just copied what ilyes wrote.
    error_description = {'101':'groundfailure - redémarrer - remonter le disjoncteur',
    '102':'changer la carte de puissance : pb de voltage',
    '105':'pas de mesure de puissance - intervention',
    '106':'groundfailure - redémarrer - remonter le disjoncteur',
    '201':'protections - bloquant - changer les protections',
    '202':'pas assez de voltage territoire - utilisation possible',
    '208':'trop de voltage - temporaire',
    '211':'lock moteur prise - mauvaise manip - changer le moteur - la charge ne se lance pas - pas de débranchement',
    '212':'manque une phase sur un triphasé - rebrancher / changer fil - utilisation possible',
    '302':'trop de courant - temporaire',
    '303':"trop d'essais client - <1min - patienter",
    '404':'câble bloqué - pb client - temporaire',
    '406':'câble pb client',
    '0': 'erreur pas specifiée par virta ???',
    '111':'borne offline très souvent (>50%)',# dont include offline here, seperate in another code
    '222':'borne faulted >25%' 
    }
    error_descriptions = []
    for code in array_of_error_code:
        error_descriptions.append(error_description[code])
    return error_descriptions

def serious_error(occurences):
    #function returns true or false depending on the number of occurences of an error
    seuil = 10
    if occurences >seuil :
        return True
    else:
        return False
    
def which_territory(coordinate):
    #function receives coordinate in tuple form, outputs department code
    #maybe should change in case GT goes international? like St. Lucia
    #The coordinates are based on approximate bounding boxes of the islands 
    lat = coordinate[0]
    lon = coordinate[1]
    if lat<= 14.892 and lat>= 14.386 and lon<=-60.8 and lon>=-61.34:
        return 972 #martinique
    elif lat<= 16.53 and lat>=15.91 and lon>=-61.81 and lon<=-60.987:
        return 971 #guadaloupe
    elif lat>=17.873414  and lat<=17.958522 and lon>=-62.872415 and lon<=-62.777062:
        return 971 #guadaloupe st barthelemy
    elif lat<= 5.857 and lat>=1.962 and lon>=-54.9 and lon<= -51.5654:
        return 973 #guyane
    elif lat>=-21.44 and lat<=-20.8 and lon>=55.2 and lon<=55.91:
        return 974 #la reunion
    elif lat==0 and lon ==0:
        return 0

def move_scraps_to_gdrive(downloads_filepath,virta_csv_gdrive_filepath,stations_all_filepath ):
    #because the scrapping routine made by ilyes saves the virta files csv into the downloads folder,
    #this function moves the 4 files downloaded to a dedicated folder in the gdrive
    #to use this function, gdrive needs to be connected to the file explorer (G:)
    #input: downloads folder filepath, gdrive folder filepath

    now = datetime.datetime.now()
    today = now.strftime("%d.%m.%Y")
    #today_err = now.strftime("%m.%d.%Y")
    yesterday_ = now - datetime.timedelta(days=1)
    yesterday = yesterday_.strftime("%d.%m.%Y")
    before_ = now - datetime.timedelta(days=30)
    before = before_.strftime("%d.%m.%Y")
    #before_err = before_.strftime("%m.%d.%Y")
    before_week = now - datetime.timedelta(days=7)
    before_week = before_week.strftime("%d.%m.%Y")
    daterange = str(before)+" - "+str(today)
    daterange_week = str(before_week)+" - "+str(today)
    #daterange_err = str(before_err)+" - "+str(today_err)
    csvs = ['error-messages','kpiScorecard_'+before+' - '+yesterday,'empchargeevents_'+daterange,'offlinestations_'+daterange_week]
    try:
        os.mkdir(virta_csv_gdrive_filepath +'//'+today)
    except FileExistsError:
        pass
    virta_csv_filepaths = []
    for csv in csvs:
        old_path = downloads_filepath +'/'+csv+'.csv'
        new_path = virta_csv_gdrive_filepath +'\\'+today+'\\'+csv+'.csv'
        virta_csv_filepaths.append(new_path)
        try:
            shutil.move(old_path, new_path)
        except FileNotFoundError:
            print(old_path+' is missing or not named correctly')
            pass
    return virta_csv_filepaths


def routine_maintenance(virta_csv_filepaths,stations_all_filepath):
    #this function is essentially a remake of the maintenance routines bornes by Ilyes
    #it takes as inputs the filepath of the csvs downloaded by virta from the scrapping routine
    #and creates an excel file test_maintenance.xlsx which is connected to greendata
    #https://sites.google.com/greentechnologie.net/portail/op%C3%A9rations
    
    
    #load csv files from virta
    charges_30 = pd.read_csv(virta_csv_filepaths[2],skiprows=1)
    kpi_30 = pd.read_csv(virta_csv_filepaths[1],skiprows=1)
    errors_30 = pd.read_csv(virta_csv_filepaths[0],sep=';')

    #offline_30 = pd.read_csv(virta_csv_filepaths[3],skiprows=1)
    
    #this one is not auto yet - have to change
# =============================================================================
# =============================================================================
    stations_all =pd.read_csv(stations_all_filepath)
# =============================================================================
# =============================================================================
    #change to date time type for all timestamp columns and sort from most recent to least
    #    time_columns = [charges_30["Created"],offline_30['Station offline'],offline_30['Station online']]

    charges_30["Created"] = pd.to_datetime(charges_30["Created"])
    
    #for column in time_columns:
    #    column = pd.to_datetime(column)
    
    
    #offline_30.sort_values(by='Station online',inplace=True,ascending=False)
    charges_30.sort_values(by='Created', inplace=True,ascending = False)
    
    #fill na with 0
    errors_30['Vendor Error Code'].fillna(0,inplace=True )
    #change to int type the station ID and the error code 
    errors_30['Vendor Error Code'] = errors_30['Vendor Error Code'].astype(int)
    errors_30['Station ID'] =  errors_30['Station ID'].astype(int)
    
    #get all the different error codes and all the station IDs
    uniq_error_codes = errors_30['Vendor Error Code'].unique().astype(int)
    uniq_error_codes[uniq_error_codes <0 ] = 0
    #uniq_stations= errors_30['Station ID'].unique()
    
    # =============================================================================
    # Most recurring errors
    # =============================================================================
    #create a dictionary of dataframes for each error code
    #each dataframe as the station ID as an index, with the number of error occurences and an Error boolean
    #if occurences larger than seuil, error is true
        
    error_count_dict = {} #dict
    seuil_occurence = 10 #threshold
    count_errors = errors_30.groupby(['Vendor Error Code','Station ID'])['Error Code'].count()
    for error_code in uniq_error_codes:
        error_count_df = pd.DataFrame(columns = ['Occurences','Error'],index=count_errors.loc[error_code,:].reset_index()['Station ID'])
        error_count_df['Occurences'] = count_errors.loc[error_code,:].reset_index()['Error Code'].values #insert occurences in dataframe
        error_count_df['Error'] = error_count_df['Occurences']>seuil_occurence #set TRUE for Error if occurences above threshold
        error_count_dict[error_code]=error_count_df #place dataframe in dict
        
    # =============================================================================
    # Offline for longest Period
    # =============================================================================
    seuil_offline = 50 #smallest % of time borne is offline after which it is considered serious
    offline_often= kpi_30[['Station ID','Offline %']]
    offline_often.loc[:,'Error'] = offline_often.loc[:,'Offline %']>seuil_offline
    offline_often = offline_often.set_index('Station ID')
    error_count_dict[111]=offline_often #place dataframe in dict
        
    # =============================================================================
    # Faulted for longest Period
    # =============================================================================
    seuil_faulted = 25 
    faulted_longest = kpi_30.loc[:,['Station ID','Faulted %']]
    faulted_longest.loc[:,'Error'] = faulted_longest.loc[:,'Faulted %']>seuil_faulted
    faulted_longest= faulted_longest.set_index('Station ID')
    error_count_dict[222]=faulted_longest #place dataframe in dict
    
    # =============================================================================
    # Errors - most recurring
    # =============================================================================
    seuil_error = 50
    error_most = kpi_30.loc[:,['Station ID','Errors']]
    error_most.loc[:,'Error'] = error_most.loc[:,'Errors']>seuil_error
    
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # # # Dataframe of all Bornes in each territory 
    # =============================================================================
    # =============================================================================
    # =============================================================================
    
    def string_to_tuple_coord(string_coord):
        if string_coord == ',' :
            return (0,0)
        else:
            return ast.literal_eval(string_coord)
        
    stations_all['position']=stations_all['position'].astype('string')
    stations_all['position']=stations_all['position'].fillna('0,0')
    stations_all['position']=[ string_to_tuple_coord(coordinate) for coordinate in stations_all['position'] ]
    stations_all['country']=stations_all['position'].apply(which_territory)
    
    
    # =============================================================================
    # Get all stations with considerable errors
    # =============================================================================
    
    # =============================================================================
    # #there are types of errors:
    #   error most
    #   faulted longest
    #   offline longest
    #   error count for each type of error
    # =============================================================================
    
    #list all their stations and their respective errors
    Station_ID_errors = []
    Station_ID = []
    
    for error in error_count_dict:
        print(error)
        try:
            Station_ID = np.append(Station_ID,error_count_dict[error].groupby('Error').get_group(True).index)
            Station_ID_errors = np.append(Station_ID_errors,[error]*len(error_count_dict[error].groupby('Error').get_group(True).index))
        except KeyError:
            pass
    
    
    #create a dataframe with all problem stations, their errors and their countries
    problem_stations = pd.DataFrame( columns = ['Station ID','name','Error Code','Country'])
    problem_stations['Station ID'] = Station_ID.astype(int)
    problem_stations['Error Code']=Station_ID_errors.astype(int)
    problem_stations=problem_stations.groupby(['Station ID'])['Error Code'].apply(lambda x: ','.join(x.astype(str))).reset_index()
    all_stations_grpby = stations_all.groupby('station_ID')['country']
    
    #put in department codes (yeah there is definitely a smarter way to do this but i dont know it)
    countries = []
    for station in problem_stations['Station ID'].values:
        countries = np.append(countries,all_stations_grpby.get_group(station).values.astype(int)[0] )
    problem_stations['Country'] =  countries

    
    
    #put names in problem stations df
    name_dict = dict(zip(stations_all['station_ID'],stations_all['name']))
    problem_stations['name'] = problem_stations['Station ID'].map(name_dict)
    problem_stations['Error Code'] = problem_stations['Error Code'].str.split(',')
    problem_stations['Error Description'] = problem_stations['Error Code'].apply(error_descriptions)
    
    #reattach details such as public/private and last charge
    problem_stations = problem_stations.reset_index()
    problem_stations['Public/Private'] = problem_stations['Station ID'].map(stations_all.set_index('station_ID')['accessibility'])
    problem_stations['Derniere Connection'] = problem_stations['Station ID'].map(stations_all.set_index('station_ID')['lastconnect'])
    # =============================================================================
    # Figure out which country each borne is in
    # =============================================================================
    error_country_dict={}
    country_keys = [972,971,973,0]
    for country in country_keys:
        error_country_dict[country] =problem_stations.groupby('Country').get_group(country).sort_values(by = 'Derniere Connection',ascending=True ).drop('Country',axis=1)
    #delete error bornes (country in 0)
    error_country_dict.pop(0) #can comment if u want to see all error bornes
    
   
    # =============================================================================
    # create dashboard of countries
    # =============================================================================
    country_dashboard = pd.DataFrame(columns = ['Interventions'], index = [971,972,973])
    country_dashboard.index.name='Département'
    for country in country_dashboard.index:
        country_dashboard['Interventions'].loc[country] = error_country_dict[country]['Station ID'].count()
    
    
    # =============================================================================
    # save to google sheets
    # =============================================================================
    
    # create a excel writer object
    with pd.ExcelWriter(r'C:\Users\a2ste\Dropbox\My PC (LAPTOP-BG2PFRET)\Documents\GT\EzMaintenance\test_maintenance.xlsx') as writer:
        country_dashboard.to_excel(writer, sheet_name='Sommaire', index=True)
        for country in error_country_dict:
        # use to_excel function and specify the sheet_name and index
        # to store the dataframe in specified sheet
            error_country_dict[country].drop('index',axis=1).to_excel(writer, sheet_name=str(country), index=False)
            for column in error_country_dict[country]:
                column_width = max(error_country_dict[country][column].astype(str).map(len).max(), len(column))
                col_idx = error_country_dict[country].columns.get_loc(column)
                writer.sheets[str(country)].set_column(col_idx, col_idx, column_width)
    writer.save()
    shutil.move(r'C:\Users\a2ste\Dropbox\My PC (LAPTOP-BG2PFRET)\Documents\GT\EzMaintenance\test_maintenance.xlsx', r'G:\Shared drives\Mes outils OPE\EzMaintenance\test_maintenance_bornes.xlsx')

def offline_stations(virta_csv_filepaths):
    #routine_maintenance(virta_csv_filepaths)
    


#move csv files from scrapping to designated gdrive folder
downloads_filepath = 'C:/Users/a2ste/Downloads'
virta_csv_gdrive_filepath = r'G:\Shared drives\Mes outils OPE\EzMaintenance\csv_mensuel'
stations_all_filepath = r'C:/Users/a2ste/Downloads/station-list.csv' 

virta_csv_filepaths = move_scraps_to_gdrive(downloads_filepath,virta_csv_gdrive_filepath )
routine_maintenance(virta_csv_filepaths)
    