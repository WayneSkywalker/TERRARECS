import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

## get max and min values of the dataset
def get_df_max_min(df):
    return df.max(), df.min()

## normalize data values to range(0, 1) for better performance
def normalize_data(df):
# def normalize_data(df, maxs, mins):
    maxs, mins = get_df_max_min(df)
    columns = df.columns.tolist()
    for column in columns:
        df[column] = (df[column] - mins[column]) / (maxs[column] - mins[column])
    return df

# from math import sin, cos, sqrt, atan2, radians

# def get_distance(x1,y1,x2,y2):
#     # approximate radius of the earth in km.
#     R = 6373.0
#     latitude_1 = radians(x1)
#     longitude_1 = radians(y1)
#     latitude_2 = radians(x2)
#     longitude_2 = radians(y2)

#     d_longitude = longitude_2 - longitude_1
#     d_latitude = latitude_2 - latitude_1

#     a = sin(d_latitude / 2)**2 + cos(latitude_1) * cos(latitude_2) * sin(d_longitude / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
#     distance = R * c

#     return distance

class CBRecommender:

    MODEL_NAME = 'Content - Based'

    def __init__(self, df_pages = None):
        self.df_pages = df_pages

    def get_model_name(self):
        return self.MODEL_NAME

    def prepare_page_features(self):
        df_pages = self.df_pages

        df_house_type_ohe = pd.get_dummies(df_pages.house_type, prefix='house_type')
        df_pages['house_type_detached_house'] = df_house_type_ohe['house_type_6']
        df_pages['house_type_condominium'] = df_house_type_ohe['house_type_7']
        df_pages['house_type_land'] = df_house_type_ohe['house_type_8']
        df_pages['house_type_townhouse'] = df_house_type_ohe['house_type_9']
        df_pages['house_type_shophouse'] = df_house_type_ohe['house_type_10']
        df_pages['house_type_other'] = df_house_type_ohe['house_type_11']
        df_pages['house_type_semi_detached_house'] = df_house_type_ohe['house_type_197']
        df_pages['house_type_home_office'] = df_house_type_ohe['house_type_198']
        df_pages['house_type_factory'] = df_house_type_ohe['house_type_206']
        df_pages['house_type_warehouse'] = df_house_type_ohe['house_type_207']
        df_pages['house_type_office'] = df_house_type_ohe['house_type_208']
        df_pages['house_type_apartment'] = df_house_type_ohe['house_type_209']
        df_pages['house_type_hotel'] = df_house_type_ohe['house_type_210']
        del df_house_type_ohe
        
        post_type_sale = []
        post_type_sale_down = []
        post_type_rent = []
        for index, row in df_pages.iterrows():
            if row['post_type'] == 1:
                post_type_sale.append(1)
                post_type_sale_down.append(0)
                post_type_rent.append(0)
            elif row['post_type'] == 2:
                post_type_sale.append(0)
                post_type_sale_down.append(1)
                post_type_rent.append(0)
            elif row['post_type'] == 3:
                post_type_sale.append(1)
                post_type_sale_down.append(0)
                post_type_rent.append(1)
            elif row['post_type'] == 4:
                post_type_sale.append(0)
                post_type_sale_down.append(0)
                post_type_rent.append(1)
        df_pages['post_type_sale'] = post_type_sale
        df_pages['post_type_sale_down'] = post_type_sale_down
        df_pages['post_type_rent'] = post_type_rent
        del post_type_sale, post_type_sale_down, post_type_rent
        
        df_pages.replace({'room_type' : { 49 : 48, 50 : 48, 51 : 48, 52 : 48, 53 : 48}}, inplace = True)
        df_room_type_ohe = pd.get_dummies(df_pages.room_type, prefix = 'room_type')
        df_pages['room_type_penhouse'] = df_room_type_ohe['room_type_41']
        df_pages['room_type_duplex'] = df_room_type_ohe['room_type_42']
        df_pages['room_type_studio'] = df_room_type_ohe['room_type_43']
        df_pages['room_type_1'] = df_room_type_ohe['room_type_44']
        df_pages['room_type_2'] = df_room_type_ohe['room_type_45']
        df_pages['room_type_3'] = df_room_type_ohe['room_type_46']
        df_pages['room_type_4'] = df_room_type_ohe['room_type_47']
        df_pages['room_type_5+'] = df_room_type_ohe['room_type_48']
        del df_room_type_ohe
        
        # ohe with area id
        df_area_ohe = pd.get_dummies(df_pages.area_id, prefix = 'area_id')
        df_pages['area_id_1'] = df_area_ohe['area_id_1']
        df_pages['area_id_2'] = df_area_ohe['area_id_2']
        df_pages['area_id_3'] = df_area_ohe['area_id_3']
        df_pages['area_id_4'] = df_area_ohe['area_id_4']
        df_pages['area_id_5'] = df_area_ohe['area_id_5']
        df_pages['area_id_6'] = df_area_ohe['area_id_6']
        df_pages['area_id_7'] = df_area_ohe['area_id_7']
        df_pages['area_id_8'] = df_area_ohe['area_id_8']
        df_pages['area_id_9'] = df_area_ohe['area_id_9']
        df_pages['area_id_10'] = df_area_ohe['area_id_10']
        df_pages['area_id_11'] = df_area_ohe['area_id_11']
        df_pages['area_id_12'] = df_area_ohe['area_id_12']
        df_pages['area_id_13'] = df_area_ohe['area_id_13']
        df_pages['area_id_14'] = df_area_ohe['area_id_14']
        df_pages['area_id_15'] = df_area_ohe['area_id_15']
        df_pages['area_id_16'] = df_area_ohe['area_id_16']
        df_pages['area_id_17'] = df_area_ohe['area_id_17']
        df_pages['area_id_18'] = df_area_ohe['area_id_18']
        df_pages['area_id_19'] = df_area_ohe['area_id_19']
        df_pages['area_id_20'] = df_area_ohe['area_id_20']
        df_pages['area_id_21'] = df_area_ohe['area_id_21']
        df_pages['area_id_22'] = df_area_ohe['area_id_22']
        df_pages['area_id_23'] = df_area_ohe['area_id_23']
        df_pages['area_id_24'] = df_area_ohe['area_id_24']
        df_pages['area_id_25'] = df_area_ohe['area_id_25']
        del df_area_ohe
        
        # calculate distances from supermarket, department store, and education
        # df_places = pd.read_csv('df_from_longdo.csv')
        # df_place_supermarket = df_places[df_places['poi_type'] == 'Supermarket/ Convenience Store']
        # df_place_department_store = df_places[df_places['poi_type'] == 'Department Store']
        # df_place_education = df_places[df_places['poi_type'] == 'school, university, education places']
        
        # distances_supermarket = []
        # distances_department_store = []
        # distances_education = []
        # for index, row in df_pages.iterrows():
        #     supermarket_distance = 10000000
        #     department_store_distance = 10000000
        #     education_distance = 10000000
        #     for index_supermarket, row_supermarket in df_place_supermarket.iterrows():
        #         d = get_distance(row['lat'], row['lng'], row_supermarket['latitude'], row_supermarket['longitude'])
        #         if d < supermarket_distance:
        #             supermarket_distance = d
        #     for index_department_store, row_department_store in df_place_department_store.iterrows():
        #         d = get_distance(row['lat'], row['lng'], row_department_store['latitude'], row_department_store['longitude'])
        #         if d < department_store_distance:
        #             department_store_distance = d
        #     for index_education, row_education in df_place_education.iterrows():
        #         d = get_distance(row['lat'], row['lng'], row_education['latitude'], row_education['longitude'])
        #         if d < education_distance:
        #             education_distance = d
        #     distances_supermarket.append(supermarket_distance)
        #     distances_department_store.append(department_store_distance)
        #     distances_education.append(education_distance)
        
        # df_pages['distances_supermarket'] = distances_supermarket
        # df_pages['distances_department_store'] = distances_department_store
        # df_pages['distances_education'] = distances_education
        
        columns_unused = ['title_th','title_en','area_id','post_type','district_id','amphur_id','province_id','room_type','house_type']
        # columns_unused = ['title_th','title_en','area_id','post_type','room_type','house_type']
        df_features = df_pages.drop(columns = columns_unused).set_index('page_id')
        
        df_features = normalize_data(df_features) # normalize data
        
        return df_features

    def recommend(self, page_id, k = 10): # KNN model
        
        df_features = self.prepare_page_features()
        
        if page_id in df_features.index.tolist():
            query_index = df_features.index.get_loc(page_id)
        else:
            raise Exception('Cannot find a page with this id.')
        
        query_page = df_features.iloc[query_index,:]
        
        # cut a feature with post_type
        if query_page['post_type_sale'] != 1 or query_page['post_type_rent'] != 1:
            if query_page['post_type_sale'] == 1:
                query_page = query_page.drop(labels = ['rent_price'])
            elif query_page['post_type_rent'] == 1:
                query_page = query_page.drop(labels = ['sale_price'])
        elif query_page['post_type_sale_down'] == 1:
            query_page = query_page.drop(labels = ['rent_price'])
        
        # cut features with house_type
        if query_page['house_type_condominium'] == 1:
            query_page = query_page.drop(labels = ['landarea_total_sqw'])
        elif query_page['house_type_land'] == 1:
            query_page = query_page.drop(labels = ['areasize_sqm','room_type_penhouse','room_type_duplex','room_type_studio','room_type_1','room_type_2','room_type_3','room_type_4','room_type_5+'])
        elif query_page['house_type_factory'] == 1 or query_page['house_type_warehouse'] == 1 or query_page['house_type_office'] == 1:
            query_page = query_page.drop(labels = ['room_type_penhouse','room_type_duplex','room_type_studio','room_type_1','room_type_2','room_type_3','room_type_4','room_type_5+'])
        
        if query_page.isnull().any():
            query_page_null_value_feature_list = query_page[query_page.isnull()].index.tolist()
            query_page = query_page.drop(labels = query_page_null_value_feature_list)
        
        query_feature_list = query_page.index.tolist()
        
        df_selected_features = df_features[~df_features[query_feature_list].isnull()][query_feature_list]
        
        # sparse matrix
        df_features_matrix = csr_matrix(df_selected_features.values)
        
        # train model
        model_knn = NearestNeighbors(n_neighbors = k, metric = 'euclidean', algorithm = 'brute')
        model_knn.fit(df_features_matrix)
        
        distances, indices = model_knn.kneighbors(df_selected_features.iloc[query_index,:].values.reshape(1, -1), n_neighbors = k)
        
        recommendation_list = []
        knn_distances_list = []
        for i in range(0, len(distances.flatten())):
            if i != 0:
                # print('{0}: {1}, with distance of {2}:'.format(i, df_features.index[indices.flatten()[i]], distances.flatten()[i]))
                recommendation_list.append(df_features.index[indices.flatten()[i]])
                knn_distances_list.append(distances.flatten()[i])
                
        temp = pd.DataFrame({'page' : recommendation_list, 'distance' : knn_distances_list}).sort_values(['page'])
        
        df_recommendation = self.df_pages[self.df_pages.page_id.isin(recommendation_list)]
        df_recommendation['distance'] = temp['distance'].tolist()
        df_recommendation = df_recommendation.sort_values(['distance'])
        df_recommendation = df_recommendation[df_recommendation.page_id != page_id].reset_index(drop = True)
        
        del temp
        
        return df_recommendation
