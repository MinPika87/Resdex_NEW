import pandas as pd
from scipy import sparse
import numpy as np
from time import time
import sys
import math, pickle
from time import sleep

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

class Feature2dMatrix():
    # def __init__(self, col1, col2, value_col, file_path = None, df = None, type = '2d', thres = 50):
    #     start = time()
        # self.row_vocab, self.col_vocab,\
        # self.row_vocab_dict, self.matrix = self.create_sparse_matrix(
        #     file_path,
        #     df,
        #     col1,
        #     col2,
        #     value_col,
        #     thres
        # )
    #     end_time = round(time() - start, 2)
    #     print ("time elapsed: ", end_time, " sec\n")

    def __init__(self, col1, col2, value_col, file_path = None, df = None, type = '2d', thres = 50, create_now = 0):
        start = time()
        if create_now:
            self.row_vocab, self.col_vocab,\
            self.row_vocab_dict, self.matrix = self.create_sparse_matrix(
                file_path,
                df,
                col1,
                col2,
                value_col,
                thres
                )
        else:
            self.row_vocab = self.load_pickle(file_path + '/row_vocab.pkl')
            self.col_vocab = self.load_pickle(file_path + '/col_vocab.pkl')
            self.row_vocab_dict = self.load_pickle(file_path + '/row_vocab_dict.pkl')
            self.matrix = sparse.load_npz(file_path + '/matrix.npz')

        end_time = round(time() - start, 2)
        print ("time elapsed: ", end_time, " sec\n")

    def load_pickle(self, path):
        with open(path, 'rb') as handle:
            return pickle.load(handle)

    def create_sparse_matrix(self, file_path, df, col1, col2, value_col, thres):
        if df is not None:
            df[value_col] = df[value_col] * 100
            df[value_col] = df[value_col].round(3)
            matrix = df.copy()
        else:
            matrix = pd.read_parquet(file_path, columns = [col1, col2, value_col, 'count'])
            matrix[value_col] = matrix[value_col] * 100
            matrix[value_col] = matrix[value_col].round(3)

        matrix_query_count = matrix.groupby(col1)['count'].sum().reset_index().rename(columns = {'count': 'query_feature_sum'})
        matrix = matrix.merge(matrix_query_count, on = [col1], how = 'inner')
        matrix = matrix[matrix['query_feature_sum'] > thres]
        matrix = matrix[[col1, col2, value_col]]
        matrix = matrix.pivot(index=col1, columns=col2, values=value_col).fillna(0)

        row_vocab = list(matrix.index)
        col_vocab = matrix.columns
        matrix = sparse.csr_matrix(matrix.values)
        row_vocab_dict = dict(zip(row_vocab, list(range(0, len(row_vocab)))))

        return row_vocab, col_vocab, row_vocab_dict, matrix
    
    def get_feature_value(self, values, topN = None, normalize = True):
        # if indices:
        #     output = list(zip(self.col_vocab, np.around(np.array(self.matrix[indices].mean(axis = 0))[0], 3)))
        #     output.sort(key = lambda x: -1 * x[1])
        #     if topN: output = output[0 : topN]
        #     output = dict(output)
        #     if normalize:
        #         total_sum = sum(output.values())
        #         output = {k : round(v / total_sum, 2) for k,v in output.items()}
        # else:
        #     output = {}
        indices = [self.row_vocab_dict.get(s) for s in values if self.row_vocab_dict.get(s) is not None]
        if indices:
            scores = np.array(self.matrix[indices].mean(axis = 0))[0]
            x = np.argsort(scores)[::-1][:topN]
            values = scores[x]
            if normalize : values = values / values.sum()
            vocab = np.array(self.col_vocab)[x]
            output = dict(zip(vocab.tolist(), values.tolist()))
        else:
            output = {}
        return output
    
    def get_size(self):
        data_size = self.matrix.data.nbytes
        indices_size = self.matrix.indices.nbytes
        indptr_size = self.matrix.indptr.nbytes

        byte_size = data_size + indices_size + indptr_size
        return byte_size

class Feature3dMatrix():
    def __init__(self, col1, col2, col3, value_col, file_path = None, type = '3d', thres=50):
        start = time()
        df = pd.read_parquet(file_path, columns = [col1, col2, col3, value_col, 'count'])
        # print (df.columns)

        self.col2List = df[col2].unique().tolist()
        self.col3List = df[col3].unique().tolist()

        self.col2Matrices = []
        for col2Val in self.col2List: 
            self.col2Matrices.append(Feature2dMatrix(col1, col3, value_col, file_path = None, df = df[df[col2] == col2Val], thres = thres, create_now = 1))
        
    def convert_dict_to_list(self, dict):
        return [dict.get(s) if dict.get(s) else 0 for s in self.col3List]
        
    def get_feature_value(self, values, col2_scores, topN = None, normalize = True):
    
        col2List = []
        output = []
    
        for i, m in enumerate(self.col2Matrices):
            m_out = m.get_feature_value(values)
            if m_out:
                output.append(self.convert_dict_to_list(m_out))
                col2List.append(self.col2List[i])

        if output:
            output = np.array(output)
            multiplier = np.array([col2_scores.get(s) if col2_scores.get(s) else 0 for s in col2List])
            multiplier = np.expand_dims(multiplier, axis = -1)
            output = output * multiplier
            output = list(zip(self.col3List, np.around(output.sum(axis = 0), 3)))
            output.sort(key = lambda x: -1 * x[1])
            if topN: output = output[0 : topN]
            output = dict(output)
            if normalize:
                total_sum = sum(output.values())
                output = {k : round(v / total_sum, 4) for k,v in output.items()}
        else:
            output = {}
        return output

    def get_size(self, ):
        return sum([m.get_size() for m in self.col2Matrices])

if __name__=='__main__':

    base_dir = '/data/analytics/rahul.mittal/data/ResdexQuery/Matrices/affinity_matrices_idDim/'

    titleToTitleFeature = Feature2dMatrix('query_desig_id', 'cand_desig_id', 'score', file_path = base_dir + "titleId_to_titleId.parquet")

    print ("titleToTitleFeature size : ", convert_size(titleToTitleFeature.get_size()))

    skillToskillFeature = Feature2dMatrix('query_skills_id', 'cand_skills_id', 'score', file_path = base_dir + "skillId_to_skillId.parquet")
    print ("skillToskillFeature size : ", convert_size(skillToskillFeature.get_size()))

    skill_to_seg_role = 'skillId_to_segmentId_to_roleId'

    # sleep(30)
    skillTosegToRoleFeature = Feature3dMatrix('query_skill_id', 'segmentId', 'roleId', 'score', file_path = base_dir + skill_to_seg_role)

    print(skillTosegToRoleFeature.col2List)
    print ("skillTosegToRoleFeature size : ", convert_size(skillTosegToRoleFeature.get_size()))

    print(skillTosegToRoleFeature.get_feature_value([1, 2, 4, 100], {10: 0.5, 2 : 0.1, 1 : 0.1, 8 : 0.4, 7 : 0.4, 4 : 0.1, 9 : 0.2, 5 : 0.1}))







    