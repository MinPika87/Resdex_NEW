import numpy as np


from MatrixFeatures import MatrixFeatures
from taxonomy.common_functions import SkillConvertor, TitleConvertor

if __name__ == '__main__':
    sc = SkillConvertor()
    tc = TitleConvertor()

    mf = MatrixFeatures()

    example_skills = ['python', 'data science']
    

    skill_id_list = [sc.convert(i) for i in example_skills]

    # input is list of skill/title ids
    
    print(skill_id_list)

    out = mf.skillToSkillFeature.get_feature_value(skill_id_list, topN = 25, normalize = True)

    # similarly use skillToTitle / titleToTitleFeature for expansion as needed (check MatrixFeatures.py for names if needed  )

    print(out)

    # output is a dictionary of key as entity ids and value as their similarirty score
    # this is expansion of entire list of entities given
