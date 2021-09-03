# Retrospective of Golden Features for detecting actionable warnings


This repository contains the replication package of the paper "Detecting False Alarms from Automatic Static Analysis Tools: How Far are We?",
which performs a retrospective and analysis of the studies and approaches to differentiate false alarms from actionable warnings.

This repository contains 
1) the raw data of the features extracted using Wang et al.'s feature extractor (https://github.com/wangjunjieISCAS/SAWarningIdentification)
2) the findbugs xml reports for each project
3) human annotated labels for closed warnings
4) a script to generate the numbers reported in the paper.
5) brief description of the golden features
6) revisions of the projects used in the experiments
7) script to compare the findbugs filter file with the feature file



## Data for the tables in the paper
The raw data of the extracted features are in the `data` directory

## Findbugs XML reports
The findbugs XML reports used in this study are in the `findbugs_xml_reports` directory.


## Script to generate the reports

run.sh is a a script that runs the classification, printing the output into `logs`.
This can be run again to generate the results, but a set of logs have already been provided.


In the paper, the results and number in various tables can be found in `logs`.
The numbers reported in the paper can be obtained from the logs based on the file name.


For experiments without the leaked features, check the files: 
* baseline_without_leaked_features_table3b_<project>.log

For experiments with only the leaked features, check the files: 
* only_leaked_table4_<project>.log

For the experiments using kNN, check the files: 
* nn<size:1/3/5/10>_table4_<project>.log

For the experiments without the duplicated data, check the files: 
* <baseline/dummy>_table3c_<project>.log (with leaked) and 
* baseline_without_leaked_features_table3d_<project>.log (without leaked).

For the experiments of the effects of the choice of reference revision:
* baseline_2016_<project>.log
* baseline_2017_<project>.log
* baseline_2018_<project>.log
* dummy_2016_<project>.log
* dummy_2017_<project>.log
*dummy_2018_<project>.log

For the experiments regarding manually labelled data, check the files:
* <baseline/dummy>_table7a_<project>.log

For the experiments using projects with a findbugs filter, check the files:
* <baseline/dummy>_table7b_<project>.log	 (all data, but no data duplicates)
* <baseline/dummy>_table7c_<project>.log	 (removed unconfirmed false alarms)

The baseline in the file name refers to the Golden Features SVM, and dummy refers to the strawman classifier that always predicts a single label.


## Human annotated data

The human annotated data can be found in the `labelled` directory.



## Description of features

The Golden Features were analyzed by Wang et al..
Our paper found data leakage in the 5 features that depend on the computation of the proportion of actionable warnings.
The data leakage occurs because the actionability of each warning in the context (e.g. a file) has to be determined, and this is done by comparing the warnings against the reference revision.
The test warning is also a warning in the context (e.g. the file), and this means the ground-truth label is used as part of the computation of the "warning context".


|  Feature | brief explanation|
|----------|------------------|
| warning context in method  |  described in the paper. ~= Proportion of actionable warnings in the method that the current test warning is in |
| warning context in file  | described in the paper. ~= Proportion of actionable warnings in the file that the current test warning is in |
| warning context for warning type |  described in the paper. ~= Proportion of actionable warnings for the category (.e.g STYLE) of bug pattern  that the current test warning has | 
| defect likelihood for warning pattern |  described in the paper. ~= Proportion of actionable warnings for the bug pattern of the current test warning |
| discretization of defect likelihood average lifetime for warning type | described in the paper. Proportion to the difference in defect pattern from the bug pattern category | 
| comment-code ratio  |  ratio of comment length to code length in the file |
| method depth  |  relative line number of the warning divided by total length of method | 
| file depth  | line number of the warning divided by total length of file |
| methods in file  |  number of methods in the file |
| classes in package |  the number of classes in the package |
| warning pattern  | name of the bug pattern  (e.g. NP_GUARANTEED_DEREF_ON_EXCEPTION_PATH) |
| warning type  | category of the bug pattern (e.g. CORRECTNESS, STYLE) |
| warning priority | e.g. 1 (see https://stackoverflow.com/questions/15103063/what-is-the-actual-meaning-of-priority-confidence-in-findbugs) |
| package |  package name |
| file age  |  number of days that the file has existed |
| file creation  | file creation revision |
| developers |  set of the developer's identifier (e.g. email) |
| parameter signature  | type signature of the parameters (e.g. int) |
| method visibility | e.g. public, protected |
| LOC added in file (last 25 revisions)  | lines of code added to the file |
| LOC added in package (past 3 month)  | lines of code added to the package |

Many of the features above were initially proposed in these papers:

[a] Ted Kremenek, Ken Ashcraft, Junfeng Yang, and Dawson Engler. 2004. Correlation Exploitation in Error Ranking. In ESEC-FSE 2004.

[b] Sarah Heckman and Laurie Williams. 2011. A systematic literature review of actionable alert identification techniques for automated static code analysis. Information and Software Technology

[c] H. Shen, J. Fang, and J. Zhao. 2011. EFindBugs: Effective Error Ranking forFindBugs. In ICST 2011

[d] Guangtai Liang, Ling Wu, Qian Wu, Qianxiang Wang, Tao Xie, and Hong Mei. 2010. Automatic Construction of an Effective Training Set for Prioritizing Static Analysis Warnings. In ASE 2010

[e] Sarah Heckman and Laurie Williams. 2009. A Model Building Process for Identifying Actionable Static Analysis Alerts. 

For specific details, check the Feature extractor code provided by Wang et al: https://github.com/wangjunjieISCAS/SAWarningIdentification


## Intersection of Findbugs Filters and warnings:

The script `get_FP.py` compares the Findbugs filter file against the warning instances that have been extracted.

The urls of the findbugs filter files are as follows:

|project | url |
|---------|----|
| tomcat |https://raw.githubusercontent.com/apache/tomcat/411e4cc9b12bb4fd5aadfbb585db9b40afc90d3d/res/findbugs/filter-false-positives.xml |
| jmeter |"https://raw.githubusercontent.com/apache/jmeter/032cc396b962c0b5ac6a31f0b756d624be34efd0/fb-excludes.xml |
| commons-lang |https://raw.githubusercontent.com/apache/commons-lang/c4ecd75ecd8b78c66cc51b49dd32989a3f1cde2e/findbugs-exclude-filter.xml |
| hadoop |https://raw.githubusercontent.com/apache/hadoop/1f46b991da9b91585608a0babd3eda39485dce09/hadoop-mapreduce-project/dev-support/findbugs-exclude.xml |
| xmlgraphics-fop |https://raw.githubusercontent.com/apache/xmlgraphics-fop/6a719897d6f98ba89aa08e2f97b2b801be066cbf/fop-core/src/tools/resources/findbugs/exclusions.xm
| undertow |https://raw.githubusercontent.com/undertow-io/undertow/ea58de4d5ef2f8c6dc156c5f9df081e6d7354a65/findbugs-exclude.xml |
| morphia |https://raw.githubusercontent.com/MorphiaOrg/morphia/a9ae14415b7fe5041fd0267859667f3eccc403d4/config/findbugs-exclude.xml |
| flink |https://raw.githubusercontent.com/apache/flink/a1644076ee0b1771777ffc9e5634e5b2ece89d00/tools/maven/spotbugs-exclude.xml |
| kafka |https://raw.githubusercontent.com/apache/kafka/a82f194b21a6af2f52e36e55e2c6adcdba942c08/gradle/findbugs-exclude.xml |
| kudu |https://raw.githubusercontent.com/apache/kudu/74b9ac67a1d3378e0fc38bd2ce827bacafde4775/java/config/spotbugs/excludeFilter.xml |
| jenkins |https://raw.githubusercontent.com/jenkinsci/jenkins/d8cae8221e5b5ef3b5276fb53879547169a02504/src/findbugs/findbugs-excludes.xml |

## Revisions

The following revisions of the projects were used in the experiments.
The same testing revision is used in all experiments, but the training revision differs.
For Table 5 (after we reimplement the Golden Features), the following training revision is used.

| Project | Training Revision | Testing Revision|
|-----|------------|---|
| ant | 995856afcb7f8168e970e39849bdfc9264f98c84 | c92f8f160a3197e8f3df74ceb588f581d08404c0   | 
| cassandra | 69337a43670f71ae1fc55e23d6a9031230423900 | 4ed2234078c4d302c256332252a8ddd6ae345484   |
| commons-lang | bc255ccf5c239666ab54e5a31720d3f482ae78eb | c4ecd75ecd8b78c66cc51b49dd32989a3f1cde2e    |
| derby | eea0d50c8d732cad9ba563ddfa786b7028eb092f | acbecbb96a5ae0a3b6bc5948b03f061dfea91662   | 
| jmeter | adca9fe1d982342e0cec8d1e410dabd0967bb852 | 032cc396b962c0b5ac6a31f0b756d624be34efd0   |
| lucene-solr | 9e82c2409d62e7be04dc4fae7c45c3712be639a2 | 43535fecb8455b3f9364f447e129ae05f79697e2   | 
| maven |  89c2524458dd76634c5e3e9b278b34bcfe6e0ff1 | 93d07bdf9967303e8ff41b8f8030c72ecf59ce1c | 
| tomcat | ad9a49cb08bf004af97cad465bba45d21d112325 | 411e4cc9b12bb4fd5aadfbb585db9b40afc90d3d  | 
| phoenix | -(we did not use phoenix in the subsequent experiments)  | 9a1012d148a1a296fda0bb1545298f07c901d982  | 
| flink | e9f660d1ff5540c7ef829f2de5bb870b787c18b7 | a1644076ee0b1771777ffc9e5634e5b2ece89d00   | 
| hadoop | 086223892ed98e26c7f90ee81ca78e93a55f639d | 1f46b991da9b91585608a0babd3eda39485dce09|
| jenkins | 6bf099d322ae5e9adb777f2b12653a60fb38ae9a | d8cae8221e5b5ef3b5276fb53879547169a02504|
| kudu | 0f3696448b3f4eba40b094192b3fb52d8b19517e | 74b9ac67a1d3378e0fc38bd2ce827bacafde4775|
| kafka | 2885bc33daaf75477bf39a92d1d1da02c0e03eaa | a82f194b21a6af2f52e36e55e2c6adcdba942c08|
| morphia | e3d64573c1f92ab17eb2b6790608e7b5d99604ff | a9ae14415b7fe5041fd0267859667f3eccc403d4|
| undertow | e037faf03f82393d1b2405520b76aaf245acf0cb | ea58de4d5ef2f8c6dc156c5f9df081e6d7354a65|
| xmlgraphics-fop | 14f86f666166e530b3588fc606fe0346e37f5c20 | 6a719897d6f98ba89aa08e2f97b2b801be066cbf|




