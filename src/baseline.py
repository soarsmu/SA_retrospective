import statistics
import time
import warnings
import cleaning
import sys
import os
import glob

import numpy as np
import pandas as pd

from sklearn import svm
from sklearn.svm import LinearSVC
from sklearn import tree
from sklearn.preprocessing import MinMaxScaler
from sklearn import preprocessing
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
from sklearn.dummy import DummyClassifier
from collections import defaultdict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import LabelEncoder

from pathlib import Path

import lime
import lime.lime_tabular
from lime import submodular_pick
import shap



""" NOTES:
      - requires Python 3.0 or greater
      - order of the original lists is not preserved
"""


def main(path, stop_at, clf, interesting_path, seed=0):

    training_x, training_y, testset_x, testset_y, training_canonical_ids, testing_canonical_ids = cleaning.data_clean(path, [interesting_path], seed)

    print("training_x:", training_x.shape)
    print("training_y:", len(training_y))
    print("testset_x:", testset_x.shape)
    print("testset_y:", len(testset_y))

    training_x.to_csv(path + "training_x.csv")
    testset_x.to_csv(path + "testset_x.csv")
    
    clf.fit(training_x, training_y)
    y_pred = clf.predict(testset_x)

    print(metrics.classification_report(testset_y, y_pred))
    print("accuracy:", metrics.accuracy_score(testset_y, y_pred))
    
    try:
        f1_score_pos = metrics.f1_score(testset_y, y_pred, average=None)[1]   # get the f1-score for the positive class only
        print(metrics.f1_score(testset_y, y_pred, average=None)[1])
        tn, fp, fn, tp = metrics.confusion_matrix(testset_y, y_pred).ravel()
        print("@@@ tn: {}, fp: {}, fn: {}, tp: {}".format(tn, fp, fn, tp))
    except IndexError:
        # this error must have meant that f1_score(...) returned only 1 value (f1 of negative class)
        # this occurs on the 2018 data on jmeter
        if metrics.f1_score(testset_y, y_pred, average=None)[0] != 1:
            raise Exception('odd')
        print(metrics.f1_score(testset_y, y_pred, average=None))
        f1_score_pos = 0
        tn = 0
        tp = 0
        fn = 0
        tp = 0

    

    print("@@@ LIME - Creating explainer", flush=True)
    feature_names =  training_x.columns.values.tolist()
    explainer = lime.lime_tabular.LimeTabularExplainer(np.asarray(training_x), feature_names=feature_names, discretize_continuous=True)

    print("@@@ LIME - Random Sampling of Instances", flush=True)
    Path(path + "lime-random/").mkdir(parents=True, exist_ok=True)
    for iter in range(25):
        sample_no = np.random.randint(0, testset_x.shape[0])
        print("iter: %d, sample_no: %d, actual label: %s, predicted: %s" % (iter, sample_no, testset_y[sample_no], y_pred[sample_no]))
        exp = explainer.explain_instance(testset_x.iloc[sample_no], clf.predict_proba, num_features=10)
        exp.save_to_file(path + "lime-random/" + 'lime_random_' + str(iter) + '.html')

    # print("@@@ LIME - Submodular Pick", flush=True)
    # Path(path + "lime-sp/").mkdir(parents=True, exist_ok=True)
    # sp_obj = submodular_pick.SubmodularPick(explainer, np.asarray(training_x), clf.predict_proba, sample_size=100, num_features=10, num_exps_desired=10)
    # for iter in range(len(sp_obj.sp_explanations)):
    #     exp = sp_obj.sp_explanations[iter]
    #     exp.save_to_file(path + "lime-sp/" + 'lime_sp_obj_' + str(iter) + '.html')

    # print("@@@ LIME - Investigating interesting instances: predicted differs from actual label", flush=True)
    # Path(path + "lime-differs/").mkdir(parents=True, exist_ok=True)
    # df_pred_and_actual = pd.DataFrame({ 'y_pred': y_pred, 'testset_y': testset_y })
    # differs_list = df_pred_and_actual.index[ df_pred_and_actual['y_pred'] != df_pred_and_actual['testset_y'] ].tolist()
    # print("Samples where predicted and actual label differs:", differs_list)

    # for iter, sample_no in enumerate(differs_list):
    #     print("iter: %d, sample_no: %d, actual label: %s, predicted: %s" % (iter, sample_no, testset_y[sample_no], y_pred[sample_no]), flush=True)
    #     exp = explainer.explain_instance(testset_x.iloc[sample_no], clf.predict_proba, num_features=10)

        # exp.save_to_file(path + "lime-differs/" + 'lime_differs_' + str(iter) +  '__' + str(testing_canonical_ids.iloc[sample_no]) + '__' + str(testset_y[sample_no]) + "__"  + str(y_pred[sample_no]) + '.html')

    # print("@@@ SHAP - Creating explainer", flush=True)
    # shap_explainer = shap.KernelExplainer(clf.predict_proba, training_x.sample(200))

    # print("@@@ SHAP - Estimate the SHAP values for a set of samples", flush=True)
    # shap_values = shap_explainer.shap_values(training_x.sample(200), n_samples=2)

    # # print("@@@ SHAP - Predicting a sample", flush=True)
    # # shap.plots.waterfall(shap_values[0])

    # print("@@@ SHAP - Saving to file", flush=True)
    # fig = shap.summary_plot(shap_values, training_x, show=False)
    # plt.savefig(path + 'shap_summary.png')

    
    # pos_at = list(clf.classes_).index("yes")
    pos_at = list(clf.classes_).index(1)

    prob = clf.predict_proba(testset_x)[:, pos_at]

    auc = metrics.roc_auc_score(testset_y, prob)

    # metrics.plot_roc_curve(clf, testset_x, testset_y)   
    # plt.show()  

    # fpr, tpr, _ = metrics.roc_curve(testset_y, prob)
    # plt.plot(fpr,tpr,label="data 1, auc="+str(auc))
    # plt.legend(loc=4)
    # plt.show()

    sorted_label = []
    order = np.argsort(prob)[::-1][:]  # numpy.ndarray
    # pos_all = sum([1 for label_real in testset_y if label_real == "yes"])
    pos_all = sum([1 for label_real in testset_y if label_real == 1])
    num_all = sum([1 for label_real in testset_y])
    print("number of samples:", num_all)
    total_recall = []
    length = []
    for i in order:
        a = testset_y[i]  # real label
        sorted_label.append(a)
        # pos_get = sum([1 for label_real in sorted_label if label_real == "yes"])
        pos_get = sum([1 for label_real in sorted_label if label_real == 1])
        length.append(len(sorted_label) / num_all)
        total_recall.append(pos_get / pos_all)
        # print(pos_get, len(sorted_label))
# ######
    total_recall = total_recall[::10]
    rate = length[::10]
    # append(1) in case that list out of range
    total_recall.append(1)
    rate.append(1)

    if type(stop_at) is tuple:
        stop_at = stop_at[0]

    stop = 0
    for index in range(len(total_recall)):
        if total_recall[index] >= stop_at:
            stop = index
            break

    print("AUC", auc)
    print("pos_get", pos_get)
    print("total recall stop_at", total_recall[stop])
    return rate[stop], auc, f1_score_pos, tn, fp, fn, tp


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    clf1 = svm.SVC(kernel='linear', probability=True, class_weight='balanced')
    clf2 = RandomForestClassifier()
    clf3 = tree.DecisionTreeClassifier()
    clf4 = DummyClassifier(strategy="stratified")
    clf5 = DummyClassifier(strategy="constant", constant=1)

    clf_list = [clf1] # , clf2, clf3]
    if 'DUMMY' in os.environ and (os.environ["DUMMY"].startswith('T') or os.environ["DUMMY"].startswith('t')):
        clf_list = [clf4]
    if 'DUMMY' in os.environ and (os.environ["DUMMY"].startswith('constant')):
        clf_list = [clf5]
    if 'NN' in os.environ and (os.environ["NN"].startswith('T') or os.environ["NN"].startswith('t')):
        nn = KNeighborsClassifier(n_neighbors=1)
        clf_list = [nn]
    elif 'NN' in os.environ:
        nn = KNeighborsClassifier(n_neighbors=int(os.environ["NN"] ))
        clf_list = [nn]
    stopats = [1]

    path = r'../data/current/'
    # sys.stdout = open(path + 'stdout.txt', 'w')

    total_tn, total_fp, total_fn, total_tp = 0, 0, 0, 0
    interesing_list = sys.argv[1:] if len(sys.argv) >= 2 else [None]
    for argv in interesing_list:
        for clf in clf_list:
            print("@@@ A - classifier:", clf)
            for stopat_id in stopats:
                print("@@@ B - threshold stop at:", stopat_id)

                AUC = []
                cost = []
                f1_pos_list = []
                
                repeated_times = 10
                for i in range(1, 1+repeated_times):
                    print("@@@ C - Repeat number:", i, flush=True)
                    rate, auc, f1_pos, tn, fp, fn, tp = main(path, stop_at=stopat_id,
                                        seed=42 + i, clf=clf, interesting_path=argv )
                    AUC.append(auc)
                    cost.append(rate)
                    f1_pos_list.append(f1_pos)

                    # total_tn += tn 
                    # total_fp += fp 
                    # total_fn += fn 
                    # total_tp += tp 

                f1_pos_med = statistics.median(f1_pos_list)
                AUC_med = statistics.median(AUC)
                AUC_iqr = np.subtract(*np.percentile(AUC, [75, 25]))
                COST_med = statistics.median(cost)
                COST_iqr = np.subtract(*np.percentile(cost, [75, 25]))
                print("----------threshold stop at----------:", stopat_id)
                print('AUC', AUC)
                print("AUC_median", AUC_med)
                print("AUC_iqr", AUC_iqr)
                print('cost', cost)
                print("COST_med", COST_med)
                print("COST_iqr", COST_iqr)
                print("f1_pos_list", f1_pos_list)
                print("f1_pos_med", f1_pos_med)

    # print('total_tn', total_tn)
    # print('total_fp', total_fp)
    # print('total_fn', total_fn)
    # print('total_tp', total_tp)

    # final_p = total_tp / (total_tp + total_fp)
    # print('p=', final_p)
    # final_r = total_tp / (total_tp + total_fn)
    # print('r=', final_r)
    # print('f=', 2 * final_p * final_r / (final_p + final_r))

