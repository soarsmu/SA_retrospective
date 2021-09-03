import numpy as np
import glob
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn import preprocessing
from sklearn.preprocessing import LabelBinarizer
from IPython import embed
import sys
import os

def read_training_testing_files(path):
    trainingFiles = glob.glob(path + "/train/*.csv")
    testingFiles = glob.glob(path + "/test/*.csv")

    list_training = []  # training set list
    list_testing = []  # training set list
    list_header = []  # get the list of headers of dfs for training & testing

    for file in trainingFiles:
        df = pd.read_csv(file, index_col=None, header=None, skiprows=0)
        head = df.iloc[0]
        list_header.append(head.tolist())
        list_training.append(df)

    for file in testingFiles:
        df = pd.read_csv(file, index_col=None, header=None, skiprows=0)
        head = df.iloc[0]
        list_header.append(head.tolist())
        list_testing.append(df)

    return list_training, list_testing, list_header


def df_get(df):
    """
    :param df: a data frame with header
    :return: get rid of the header of data frame
    """
    header = df.iloc[0]
    # Create a new variable called 'header' from the first row of the dataset

    # Replace the dataframe with a new one which does not contain the first row
    df = df[1:]

    # Rename the dataframe's column values with the header variable
    df = df.rename(columns=header)
    h1 = list(df.columns.values)  # get the value of header of the df
    return df, h1


def common_get(list_header):
    """
    :param list_header: list of training & testing headers
    :return: common header
    """

    golden_fea_drop_leak = ["F123", "F105", "F68", "F101", "F104", "F65", "F22",
                  " F94", "F71", "F72", "F25", "F3-", "F15", "F126", "F41", "F77"]  # removed leaked features
    golden_fea_reimplement_leak = ["F116", "F115", "F117", "F120", "F123", "F110", "F105", "F68", "F101", "F104", "F65", "F22",
                  " F94", "F71", "F72", "F25", "F3-", "F15", "F126", "F41", "F77"]
    # golden_fea_and_semantic = ["F123", "F105", "F68", "F101", "F104", "F65", "F22",
    #               " F94", "F71", "F72", "F25", "F3-", "F15", "F126", "F41", "F77", 
    #               'pattern_0', 'pattern_1', 'pattern_2', 'pattern_3', 'pattern_4', 'pattern_5', 'pattern_6', 'pattern_7', 'pattern_8', 'pattern_9' ,'pattern_10'
    #               'pattern_11', 'pattern_12', 'pattern_13', 'pattern_14', 'pattern_15', 'pattern_16', 'pattern_17', 'pattern_18', 'pattern_19',
    #               ] 

    # golden_fea_and_semantic_with_reimplemented = ["F116", "F115", "F117", "F120", "F123", "F105", "F68", "F101", "F104", "F65", "F22",
    #               " F94", "F71", "F72", "F25", "F3-", "F15", "F126", "F41", "F77", 
    #               'pattern_0', 'pattern_1', 'pattern_2', 'pattern_3', 'pattern_4', 'pattern_5', 'pattern_6', 'pattern_7', 
    #               # 'pattern_8', 'pattern_9' ,'pattern_10'
    #               # %'pattern_11', 'pattern_12', 'pattern_13', 'pattern_14', 'pattern_15', 'pattern_16', 'pattern_17', 'pattern_18', 'pattern_19',
    #               ] 
    # only_semantic = ['pattern_0', 'pattern_1', 'pattern_2', 'pattern_3', 'pattern_4', 'pattern_5', 'pattern_6', 'pattern_7', 
    # # 'pattern_8', 'pattern_9' ,'pattern_10'
                  # 'pattern_11', 'pattern_12', 'pattern_13', 'pattern_14', 'pattern_15', 'pattern_16', 'pattern_17', 'pattern_18', 'pattern_19'
                  # ]

   

    
    features_to_use = golden_fea_reimplement_leak

    if 'DROP' in os.environ and os.environ['DROP'] in ['true', 'TRUE', 'True']:
        print('will not use leaked features')
        features_to_use =golden_fea_drop_leak
        # features_to_use.remove('F22')
    if 'ONLY_LEAKED' in os.environ and os.environ['ONLY_LEAKED'] in ['true', 'TRUE', 'True']:
        features_to_use = ["F116", "F115", "F117", "F120", 'F110']
    # features_to_use.remove('F15')
    
    golden_list = []
    count_list = []
    for header in list_header:
        golden = []
        count = 0
        for i in header:
            if i.startswith(tuple(features_to_use)) or features_to_use == '*':
                count += 1
                golden.append(i)
        count_list.append(count)
        golden_list.append(golden)


    common = set(golden_list[0]) 
    for s in golden_list[1:]:
        common.intersection_update(s)

    common.add('category')
    return common


def trim(list_df, common):
    final_df = pd.DataFrame()

    for df in list_df:
        df1, header = df_get(df)
        for element in header:
            if element not in common:
                df1 = df1.drop(element, axis=1)
        df_trim = df1
        final_df = pd.concat([final_df, df_trim])

    return final_df


def intersect(a, b):
    """ return the intersection of two lists """
    return list(set(a) & set(b))


def merge1(testing, list1, list2):
    # not in use
    """
    :param testing: testing set
    :param list1: list of training data frame
    :param list2: list of headers of training set
    :return: get rid of uncommon parts of 5 version in training set
    """

    head5 = testing.iloc[0].tolist()
    holder = head5
    for i in list2:
        common = intersect(i, holder)
        holder = common

    common_header = common

    df, header = df_get(list1[0])  # ONLY USE THE VERSION 4 FOR TRAINING
    for element in header:
        if element not in common_header:
            df = df.drop(element, axis=1)
    df_merge = df

    # df_merge = pd.concat([i for i in list1], ignore_index=True, sort=True)

    return df_merge, common_header


def is_number(df):
    '''
    :param df: input should be training_x, testset_x(type: data frame)
    :return: return is index of numeric features
    '''

    index = []
    position = 0
    for i in range(len(df.iloc[0])):
        s = df.iloc[0, i]
        try:
            float(s)  # for int, long and float
            index.append(i)
        except ValueError:
            position += 1
    return index

def read_interesting_clazz_and_bug_patterns(filepaths):
    
    interestings = []
    for filepath in filepaths:
        with open(filepath) as infile:
            for line in infile:
                clazz, bug_pattern, commit, file_depth, canonical_id = line.strip().split(',')
                interestings.append((clazz, bug_pattern, commit, canonical_id))

    # print(interestings)
    return interestings


def remove_uninteresting_bug_patterns(data, filepaths, is_training):
    interestings =read_interesting_clazz_and_bug_patterns(filepaths)

    for i in range(0, len(data)):
        # print("np.where(data[i].iloc[0] == 'F20')", np.where(data[i].iloc[0] == 'F20'))
        bug_pattern_index = np.where(data[i].iloc[0] == 'F20')[0][0]
        index = []

        clazz_index = np.where(data[i].iloc[0] == 'F55')[0][0]

        for j in range(1, len(data[i])):
            # print(data[i].iloc[j, bug_pattern_index])
            bug_pattern = data[i].iloc[j, bug_pattern_index]
            clazz = data[i].iloc[j, clazz_index]
            if is_training:
                commit = 'B'
            else:
                commit = 'C'

            canonical_id = data[i].iloc[j, 0]
            # print(canonical_id)
            if  (clazz, bug_pattern, commit, canonical_id) not in interestings:
                print('to remove ', canonical_id)
                
                index.append(j)  # index is a list of index of samples to delete

        data[i] = data[i].drop(sorted(index, reverse=True))

        
    return data


# without using canonical id, using only commit, etc
# def remove_uninteresting_bug_patterns(data, filepath, is_training):
#     interestings =read_interesting_clazz_and_bug_patterns(filepath)

#     for i in range(0, len(data)):
#         # print("np.where(data[i].iloc[0] == 'F20')", np.where(data[i].iloc[0] == 'F20'))
#         bug_pattern_index = np.where(data[i].iloc[0] == 'F20')[0][0]
#         index = []

#         clazz_index = np.where(data[i].iloc[0] == 'F55')[0][0]

#         for j in range(1, len(data[i])):
#             # print(data[i].iloc[j, bug_pattern_index])
#             bug_pattern = data[i].iloc[j, bug_pattern_index]
#             clazz = data[i].iloc[j, clazz_index]
#             if is_training:
#                 commit = 'B'
#             else:
#                 commit = 'C'
#             if  (clazz, bug_pattern, commit) not in interestings:
#                 # print('to remove ',j, (clazz, bug_pattern))

#                 index.append(j)  # index is a list of index of samples to delete

#         data[i] = data[i].drop(sorted(index, reverse=True))


#     return data

def preprocess1(Y, X):
    index = []
    label = []
    for i in range(0, len(Y)):
        # y = Y[0][i]
        y = Y.iloc[i]
        if y == "close":
            # y = "yes"
            y = 1
        elif y == "open":
            # y = "no"
            y = 0
        elif y == "deleted":
            index.append(i)  # index is a list of index for deleted samples

        label.append(y)

    for i in sorted(index, reverse=True):  # delete samples with deleted label
        del label[i]
        del X[i]

    return label, X


def one_hot(df, index_num):
    """
    :param df: training_x or testset_x, type: data frame
    :param index_num: the index list of numerical features
    :return:
    """
    lb = LabelBinarizer()
    list_len = list(range(len(df.iloc[0])))
    index_onehot = list(set(list_len) - set(index_num))
    for i in index_onehot:
        df.iloc[:, i] = lb.fit_transform(df.iloc[:, 26]).tolist()
    return df


def data_clean(path, filepaths_to_interesting_cases, seed = 0):
    list_training, list_testing, list_header = read_training_testing_files(path)

    if len(filepaths_to_interesting_cases) > 0 and filepaths_to_interesting_cases[0] != None:
        interesting_training = remove_uninteresting_bug_patterns(list_training, filepaths_to_interesting_cases, is_training=True)
        # interesting_training = list_training
        interesting_testing = remove_uninteresting_bug_patterns(list_testing, filepaths_to_interesting_cases, is_training=False)

    else:
        interesting_training = list_training
        interesting_testing = list_testing

   

    has_canonical_id = 'canonical_id' in list_header

    # print('list_header', list_header)
    common_header = common_get(list_header)
    if has_canonical_id:
        common_header.add('canonical_id')
    print("@@@ D - common_header: ", common_header)

    np.random.seed(seed)
    # training set
    training_trim = trim(interesting_training, common_header)
    training_trim.to_csv(path + "training_trim.csv")

    # testing set
    testing_trim = trim(interesting_testing, common_header)
    testing_trim.to_csv(path + "testing_trim.csv")


    if has_canonical_id:
        training_canonical_ids = training_trim.iloc[:, 0]
        testing_canonical_ids = testing_trim.iloc[:, 0]


        print(training_canonical_ids[:5])

        training_trim = training_trim.drop('canonical_id', axis=1)
        testing_trim = testing_trim.drop('canonical_id', axis=1)
    else:
        training_canonical_ids = None
        testing_canonical_ids = None


    # training set
    training_x = training_trim.iloc[:, :-1]
    training_y = training_trim.iloc[:, -1]

    # testing set
    testset_x = testing_trim.iloc[:, :-1]
    testset_y = testing_trim.iloc[:, -1]

    # remove the samples in training and test set with label "deleted"
    training_y, training_x = preprocess1(training_y, training_x)
    testset_y, testset_x = preprocess1(testset_y, testset_x)

    le = preprocessing.LabelEncoder()

    print(training_x[:3])
    # normalize the x for training and test sets
    min_max_scaler = preprocessing.MinMaxScaler()
    scaler = MinMaxScaler()

    # testset_x = min_max_scaler.fit_transform(np.asarray(testset_x))
    # training_x = min_max_scaler.fit_transform(np.asarray(training_x))
    testset_x = pd.DataFrame(scaler.fit_transform(testset_x), columns = testset_x.columns)
    training_x = pd.DataFrame(scaler.fit_transform(training_x), columns = training_x.columns)
    print(';.;')
    print(training_x[:3])

    return training_x, training_y, testset_x, testset_y, training_canonical_ids, testing_canonical_ids
