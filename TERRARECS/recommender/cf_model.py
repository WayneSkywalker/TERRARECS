import numpy as np
import pandas as pd

import warnings
from sklearn.decomposition import TruncatedSVD

class CFRecommender:
    
    MODEL_NAME = 'Collaborative Filtering'    
    
    def __init__(self, df_txns, df_pages):
        self.df_txns = df_txns
        self.df_pages = df_pages
        
    def get_model_name(self):
        return self.MODEL_NAME
    
    def prepare_txn_features(self):
        df_txns = self.df_txns
        
        df_pages_renamed = self.df_pages.rename(columns = {"id":"page"})
        df_txns = df_txns[df_txns.page.isin(df_pages_renamed.page.to_list())]
        
        combine_page_txns = pd.merge(df_txns, df_pages_renamed, on = 'page')
    
        df_page_viewed_count = combine_page_txns.groupby(by = ['page'])['event_strength'].count().reset_index().rename(columns = {'event_strength': 'total_views_count'})
        
        df_viewed_with_page_viewed_count = combine_page_txns.merge(df_page_viewed_count, how = 'left', left_on = 'page', right_on = 'page')
        
        df_features = df_viewed_with_page_viewed_count.pivot_table(index = 'userID', columns = 'page', values = 'event_strength').fillna(0)
        
        return df_features
    
    def recommend(self, page_id): # SVD model
         
        df_features = self.prepare_txn_features()
        
        if page_id not in df_features.columns.tolist():
            # raise Exception('Cannot find any user_behavior who view a page with this id.')
            page_columns = self.df_pages.columns.tolist()
            page_columns.append('corr')
            return pd.DataFrame(columns = page_columns)
        
        df_features_T = df_features.values.T
        
        from sklearn.decomposition import TruncatedSVD
        SVD = TruncatedSVD(n_components = 4)
        matrix = SVD.fit_transform(df_features_T)
        
        import warnings
        warnings.filterwarnings("ignore", category = RuntimeWarning)
        corr = np.corrcoef(matrix)
        
        page_titles = df_features.columns
        page_title_list = page_titles.tolist()
        
        query_index = page_title_list.index(page_id)
        corr_query_page = corr[query_index]
        
        corr_recs_list = corr_query_page[(corr_query_page >= 1)].tolist()
        
        df_recommendation = self.df_pages[self.df_pages.id.isin(list(page_titles[(corr_query_page >= 1)]))]
        df_recommendation['corr'] = corr_recs_list
        df_recommendation = df_recommendation[df_recommendation.id != page_id].reset_index(drop = True)
        
        return df_recommendation