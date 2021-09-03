import xml.etree.ElementTree as ET
import requests
import sys 
import re

def parse_findbugs_analysis(xml_path):
    result = []

    with open(xml_path, 'rb') as xml_file:
        tree = ET.parse(xml_file)
        bug_instances = tree.findall('.//BugInstance')

        for bug_instance in bug_instances:
            class_name = bug_instance.find('.//Class').attrib['classname'] if bug_instance.find('.//Class') is not None else None
            method_name = bug_instance.find('.//Method').attrib['name']if bug_instance.find('.//Method') is not None else None
            field_name = bug_instance.find('.//Field').attrib['name'] if bug_instance.find('.//Field') is not None else None
            bug_pattern = bug_instance.attrib['type'] if 'type' in bug_instance.attrib else None
            bug_code = bug_instance.attrib['code'] if 'code' in bug_instance.attrib else None
            bug_category = bug_instance.attrib['category'] if 'category' in bug_instance.attrib else None

            sourceline = bug_instance.find('SourceLine')
            startline = -2
            endline = -2
            if sourceline is not None:
                if 'start' in sourceline.attrib: 
                    startline = sourceline.attrib['start']
                if 'end' in sourceline.attrib:    
                    endline = sourceline.attrib['end']

            result.append(((bug_pattern, bug_code, bug_category), class_name[:class_name.rindex('.')] if '.' in class_name else None, class_name, field_name, method_name, (startline, endline)))
    return result


def parse_findbugs_filter(xml_url):
    result = []

    response = requests.get(xml_url)
    try:
        tree = ET.fromstring(response.content)
    except Exception as e:
        print(e)
        print(response.content)
        raise e

    matches = tree.findall('.//Match')
    for match in matches:

        packages = match.findall(".//Package")
        classes = match.findall(".//Class")
        fields= match.findall(".//Field")
        methods= match.findall(".//Method")

        package_names = [package.attrib['name'] for package in packages]
        class_names = [clazz.attrib['name'] for clazz in classes]
        field_names = [field.attrib['name'] for field in fields]
        method_names = [method.attrib['name'] for method in methods]

        # bug patterns can be exlucded using a diferent granulairty. bug category covers all patterns in the category, while bug pattern omits a specific type
        bug_patterns = []
        bug_codes = []
        bug_categories = []
        for bug in match.findall('.//Bug'):
            bug_pattern = bug.attrib['pattern'] if 'pattern' in bug.attrib else None
            bug_code = bug.attrib['code'] if 'code' in bug.attrib else None
            bug_category = bug.attrib['category'] if 'category' in bug.attrib else None

            if bug_pattern is not None:
                if ',' not in bug_pattern:
                    bug_patterns.append(bug_pattern)
                else:
                    bug_patterns.extend(bug_pattern.split(","))
            if bug_code is not None:
                bug_codes.append(bug_code)
            if bug_category is not None:
                bug_categories.append(bug_category)

        result.append(((bug_patterns, bug_codes, bug_categories), package_names, class_names, field_names, method_names))
    return result


def get_FPs(findbugs_filter_xml_url, findbugs_analysis_xml_path):
    def match(warning_name, filtered_names):
        for filtered_name in filtered_names:
            if filtered_name.startswith('~'):
                # match the text as a regex
                regex_pattern = filtered_name[1:]
                print(warning_name)
                if re.match(regex_pattern, warning_name):
                    # print('matched ', warning_name, ' against reg', regex_pattern)
                    return True
            else:
                if warning_name == filtered_name:
                    return True

        return False


    # merge the output of parse_findbugs_filter and parse_findbugs_analysis
    # we want warnings from parse_findbugs_analysis that are matched by one filter in parse_findbugs_filter
    findbugs_warnings = parse_findbugs_analysis(findbugs_analysis_xml_path)
    annotated_FPs = parse_findbugs_filter(findbugs_filter_xml_url)
    unmatched_warnings = 0
    matched_warnings = 0

    # print('findbugs_warnings: ', len(findbugs_warnings))
    # print('annotated_FPs: ', len(annotated_FPs))

    for warning in findbugs_warnings:
        # print(warning)
        has_match = False
        for known_FP in annotated_FPs:
            match_bug_type = warning[0][0] in known_FP[0][0] or warning[0][1] in known_FP[0][1] or warning[0][2] in known_FP[0][2]
            if not match_bug_type:
                continue
            match_class_name = match(warning[2], known_FP[2]) # warning[2] in known_FP[2]

            match_field_name = (len(known_FP[2]) != 0 and match_class_name and warning[3] is not None) and match(warning[3], known_FP[3]) # warning[3] in known_FP[3]

            match_method_name = (len(known_FP[2]) != 0 and match_class_name and warning[4] is not None) and match(warning[4], known_FP[4]) # warning[4] in known_FP[4]

            match_package_name = match(warning[1], known_FP[1]) 

            filter_matches_all = len(known_FP[2]) == 0 and len(known_FP[3]) == 0 and  len(known_FP[4]) == 0  and len(known_FP[1]) == 0

            if match_class_name or match_field_name or match_method_name or filter_matches_all:
                # print([match_class_name, match_field_name, match_method_name])
                output = [warning[0][0], warning[2], warning[3], warning[4], warning[5][0], warning[5][1]] 
                cleaned = [str(thing) if thing is not None else "null" for thing in output]
                print(','.join(cleaned))
                has_match = True
                # print(warning)

        if not has_match:
            unmatched_warnings += 1
        else:
            matched_warnings += 1

    print('unmatched_warnings', unmatched_warnings, 'matched_warnings', matched_warnings)
    print(unmatched_warnings, matched_warnings)



inputs = {
    'tomcat': ["https://raw.githubusercontent.com/apache/tomcat/411e4cc9b12bb4fd5aadfbb585db9b40afc90d3d/res/findbugs/filter-false-positives.xml", "/Users/abc/Downloads/findbugs-xml-reports_original/tomcat-C.xml"],
    'jmeter': ["https://raw.githubusercontent.com/apache/jmeter/032cc396b962c0b5ac6a31f0b756d624be34efd0/fb-excludes.xml", "/Users/abc/Downloads/findbugs-xml-reports_original/jmeter-C.xml"],
    'commons-lang': ["https://raw.githubusercontent.com/apache/commons-lang/c4ecd75ecd8b78c66cc51b49dd32989a3f1cde2e/findbugs-exclude-filter.xml", "/Users/abc/Downloads/findbugs-xml-reports_original/commons-C.xml"],
    'hadoop': ["https://raw.githubusercontent.com/apache/hadoop/1f46b991da9b91585608a0babd3eda39485dce09/hadoop-mapreduce-project/dev-support/findbugs-exclude.xml", "/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/hadoop-C.xml"],
    'xmlgraphics-fop': ["https://raw.githubusercontent.com/apache/xmlgraphics-fop/6a719897d6f98ba89aa08e2f97b2b801be066cbf/fop-core/src/tools/resources/findbugs/exclusions.xml", '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/xmlgraphics-fop-C.xml'],
    'undertow': ["https://raw.githubusercontent.com/undertow-io/undertow/ea58de4d5ef2f8c6dc156c5f9df081e6d7354a65/findbugs-exclude.xml", '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/undertow-C.xml'],
    'morphia': ["https://raw.githubusercontent.com/MorphiaOrg/morphia/a9ae14415b7fe5041fd0267859667f3eccc403d4/config/findbugs-exclude.xml", '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/morphia-C.xml'],
    # 'aws-sdk': ['https://raw.githubusercontent.com/aws/aws-sdk-java-v2/58c7300cd3d32f5c91c8f9e8b4f774826153321b/build-tools/src/main/resources/software/amazon/awssdk/spotbugs-suppressions.xml', '/Users/abc/repos/SA_repos/aws-sdk-java-v2/spotbugs_analysis_results.xml'],
    'flink': ['https://raw.githubusercontent.com/apache/flink/a1644076ee0b1771777ffc9e5634e5b2ece89d00/tools/maven/spotbugs-exclude.xml', '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/flink-C.xml'],
    'zookeeper': ['https://raw.githubusercontent.com/apache/zookeeper/b752ef66876a141035a42f30aad69e3166cad746/zookeeper-server/src/test/resources/findbugsExcludeFile.xml',  '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/zookeeper-C.xml'],
    'kafka': ['https://raw.githubusercontent.com/apache/kafka/a82f194b21a6af2f52e36e55e2c6adcdba942c08/gradle/findbugs-exclude.xml', '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/kafka-C.xml'],
    'kudu': ['https://raw.githubusercontent.com/apache/kudu/74b9ac67a1d3378e0fc38bd2ce827bacafde4775/java/config/spotbugs/excludeFilter.xml', '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/kudu-C.xml'],
    'jenkins': ['https://raw.githubusercontent.com/jenkinsci/jenkins/d8cae8221e5b5ef3b5276fb53879547169a02504/src/findbugs/findbugs-excludes.xml', '/Users/abc/repos/SA_counterfactuals/confirmed_FPs_new_dataset/findbugs-xml-reports/jenkins-C.xml']
}


if sys.argv[1] not in inputs.keys():
    raise  Exception('invalid param')


target = sys.argv[1]

get_FPs(inputs[target][0], inputs[target][1])

# get_FPs("https://raw.githubusercontent.com/apache/tomcat/b3ff8357a9559e781ae6f9bcd61738cd7ccae2bf/res/findbugs/filter-false-positives.xml", "/Users/abc/repos/SA_repos/tomcat/spotbugs_analysis_results.xml")
# get_FPs("https://raw.githubusercontent.com/apache/hadoop/f7247922b7fd827489011aeff0a0d8dea7027b83/hadoop-mapreduce-project/dev-support/findbugs-exclude.xml", "/Users/abc/repos/SA_repos/hadoop/hadoop-mapreduce-project/spotbugs_analysis_results.xml")

# "https://github.com/apache/hadoop/blob/f7247922b7fd827489011aeff0a0d8dea7027b83/hadoop-mapreduce-project/dev-support/findbugs-exclude.xml"
# get_FPs("https://raw.githubusercontent.com/apache/xmlgraphics-fop/5ce5fe50a74b9e3f84cabcffee46f860c86dbd47/fop-core/src/tools/resources/findbugs/exclusions.xml", "/Users/abc/repos/SA_repos/xmlgraphics-fop/fop-core/spotbugs_analysis_results.xml")

# "https://github.com/apache/xmlgraphics-fop/blob/5ce5fe50a74b9e3f84cabcffee46f860c86dbd47/fop-core/src/tools/resources/findbugs/exclusions.xml"
# "https://raw.githubusercontent.com/apache/xmlgraphics-fop/5ce5fe50a74b9e3f84cabcffee46f860c86dbd47/fop-core/src/tools/resources/findbugs/exclusions.xml"

# "https://github.com/undertow-io/undertow/blob/43244ccfc51c4aa7bbdc8be0641d9b8b53f76959/spotbugs-exclude.xml"
# "https://raw.githubusercontent.com/undertow-io/undertow/43244ccfc51c4aa7bbdc8be0641d9b8b53f76959/spotbugs-exclude.xml"

# "https://github.com/corretto/corretto-jmc/blob/0fe8cf8af9f54073df1fe07bf32abd0adeb44190/src/configuration/spotbugs/spotbugs-exclude.xml"
# "https://raw.githubusercontent.com/corretto/corretto-jmc/0fe8cf8af9f54073df1fe07bf32abd0adeb44190/src/configuration/spotbugs/spotbugs-exclude.xml"

# "https://github.com/MorphiaOrg/morphia/blob/000f191f35cfe6ed1fa98830c62d5531ab0ea75c/config/findbugs-exclude.xml"
# "https://raw.githubusercontent.com/MorphiaOrg/morphia/000f191f35cfe6ed1fa98830c62d5531ab0ea75c/config/findbugs-exclude.xml"

# https://github.com/aws/aws-sdk-java-v2/blob/58c7300cd3d32f5c91c8f9e8b4f774826153321b/build-tools/src/main/resources/software/amazon/awssdk/spotbugs-suppressions.xml
# "https://raw.githubusercontent.com/aws/aws-sdk-java-v2/58c7300cd3d32f5c91c8f9e8b4f774826153321b/build-tools/src/main/resources/software/amazon/awssdk/spotbugs-suppressions.xml
