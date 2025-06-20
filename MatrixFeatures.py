from FeatureMatrixLoader import Feature2dMatrix , convert_size
from time import time
import os
from dotenv import load_dotenv
#load_dotenv(os.environ.get('ENV_FILE_PATH', ''))
import warnings
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)


class MatrixFeatures():
    def __init__(self):
        self.data_dir =  '/data/analytics/dev.panghate/QueryRelaxation/data' #os.environ.get('ROOT_DIR', '') + '/data/'
        self.base_dir =  self.data_dir + "/Matrices/feature_matrices/"

        print ("Loading Matrix Features")
        
        start = time()
        self.skillToSkillFeature = Feature2dMatrix('query_skill_id', 'cand_skill_id', 'score', file_path = self.base_dir + "skillToSkillFeature", thres = 200)
        self.titleToSkillFeature = Feature2dMatrix('query_title_id', 'cand_skill_id', 'score', file_path = self.base_dir + "titleToSkillFeature", thres = 50)
        
        self.skillToTitleFeature = Feature2dMatrix('query_skill_id', 'cand_desig_id', 'score', file_path = self.base_dir + "skillToTitleFeature", thres = 50)
        self.titleToTitleFeature = Feature2dMatrix('query_title_id', 'cand_desig_id', 'score', file_path = self.base_dir + "titleToTitleFeature", thres = 5)

        self.size = self.skillToSkillFeature.get_size() + self.titleToSkillFeature.get_size() + self.skillToTitleFeature.get_size() + \
                            self.titleToTitleFeature.get_size()

        print ("Total Size of Matrix Features : ", convert_size(self.size))    
        print ("Time Elapsed in Loading Matrix Features : ", round(time() - start, 2), " sec")
    
    def l2_norm(self, feature):
        if (feature != feature) or (feature is None):
            return 0.0
        return (sum([x**2 for x in feature.values()]))**(0.5)

    def get_transformed_vector(self, feature):
        if len(feature) == 0:
            return feature
        
        return {int(k): (v) / (self.l2_norm(feature)) for k, v in feature.items() if v != 0}


    def combine(self, from_s, from_t, constant_score_feature = 0):
        all_keys = list(set(list(from_s.keys()) + list(from_t.keys())))
        output = {}
        for ent in all_keys:
            from_s_score = from_s.get(ent) if from_s.get(ent) else 0
            from_t_score = from_t.get(ent) if from_t.get(ent) else 0
            if constant_score_feature:
                output.update({ent : round(100 * 100 * (from_s_score + from_t_score), 3)})
            else:
                output.update({ent : round(100 * (from_s_score + from_t_score), 3)})
        return output
    

   

    def getHardSkillFeature(self, input_values, swr_feature = False):
        skills = input_values['skills']
        if swr_feature:
            return {int(skillId): 100*100 / len(skills) for skillId in skills}
        keywords = input_values['keywordsNew']
        return {int(skillId): 100*100 / (len(skills) + len(keywords)) for skillId in skills}

    def getHardTitleFeature(self, input_values):
        titles = input_values['titles']
        return {int(titleId):  (100 * 100) for titleId in titles}

    def getSkillFeature(self, input_values):
        skills = input_values['skills']
        titles = input_values['titles']
        from_s = self.skillToSkillFeature.get_feature_value(skills, topN = 15, normalize = True)
        from_s_transformed = self.get_transformed_vector(from_s)
        from_t = self.titleToSkillFeature.get_feature_value(titles, topN = 15, normalize = True)
        from_t_transformed = self.get_transformed_vector(from_t)
        return {'from_skill':from_s_transformed, 'from_title':from_t_transformed}
    

    def getTitleFeature(self, input_values):
        skills = input_values['skills']
        titles = input_values['titles']
        from_s = self.skillToTitleFeature.get_feature_value(skills, topN = 15, normalize = True)
        from_s_transformed = self.get_transformed_vector(from_s)
        from_t = self.titleToTitleFeature.get_feature_value(titles, topN = 15, normalize = True)
        from_t_transformed = self.get_transformed_vector(from_t)
        return {'from_skill':from_s_transformed, 'from_title':from_t_transformed}
        
    
if __name__=='__main__':
    mf = MatrixFeatures()
    print ("Size : ", convert_size(mf.size))
