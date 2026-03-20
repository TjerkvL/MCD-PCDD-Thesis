from src.automate_evaluation.evaluation_LP import getTP_FP
from src.automate_evaluation.evaluation_LP import calcPrecisionRecall,F1_Score
import numpy as np
from src.data_classes.class_drift import DriftInfo
import os
from class_collection import *



#Aknowledgment
"""
We would like to express our gratitude to Jan Niklas Adams, Tobias Brockhoff, Cameron Pitsch, and Wil M.P van der Aalst for their insightful work 
presented in the paper titled "An Experimental Evaluation of Process Concept Drift Detection." 
The codebase utilized in this project includes portions directly derived from their research. Their contributions have been invaluable in 
guiding the development of our own implementation and enhancing the overall quality of our work.
"""

def extract_log_ids(col_act: list(DriftInfo), col_det: list(DriftInfo))->dict(str,list(str)):
    """
    Returns a dictionary containing the log ids of the actual and detected collection of logs stored in separate lists
    :param col_act(List[DriftInfo]): A list storing all the actual drift instances
    :param col_det(List[DriftInfo]): A list storing all the detected drift instances
    :return: Dict[str,List[str]]: Two lists storing the log ids of the actual and detected collection of logs
    """

    log_ids_det_act = {}
    log_ids_det_act["actual logs"] = [DI_act[0].log_id for DI_act in col_act.drifts]
    log_ids_det_act["detected logs"] = [DI_det[0].log_id for DI_det in col_det.drifts]
    return log_ids_det_act

def extract_change_trace_index(drifts_in_log: list())->list(tuple(int,str,list(int))):  # takes a list of drift instances
    """
    Returns a list of tuples storing information about all the drift changepoints in a single log
    :param drifts_in_log(List[DriftInfo]): list of drift instances in a log
    :return: List[Tuple[int,str,List[int]]]: List of tuples, each tuple contains the id, drift type, and the change trace indexes for each changepoint
        in the log
    """
    drift_change_index = list()
    for drift_instance in drifts_in_log:  # is a list containing all the drift instances of a single log
        change_id = 1
        for trace_index_info in list(drift_instance.change_info.values()):
            drift_change_index.append((change_id, drift_instance.drift_type, trace_index_info["change_trace_index"]))
            change_id+=1
    return drift_change_index




def list_of_change_indexes (drift_change_index:list[tuple])->list(int):

    """
    Returns a list containing all the change trace indexes of a log

    :param drift_change_index(List[Tuple[int,str,List[int]]]): List of tuples, each tuple contains the id, drift type, and the change trace indexes for each changepoint
        in the log
    :return:List[int]: List of change trace indexes
    """

    list_of_change_indexes = list()
    for change_index_info in drift_change_index:
        list_of_change_indexes.extend(change_index_info[2])
    return list_of_change_indexes


def filter_list_change_indexes(change_index_infos : list(tuple(int,str,list(int))), drift_type:str)->list(int):
    """
    Returns a list containing all the change moments that match a specific drift type
    :param change_index_infos(List[Tuple[int,str,List[int]]]): List of tuples, each tuple contains the id, drift type, and the change trace indexes for each change moment
        in the log:
    :param drift_type(str): The drift_type that will be used to filter the drift_change_index_infos list
    :return:List[int]: List of change trace indexes sharing the same drift type

    """
    return [ci for ci in change_index_infos if ci[1]==drift_type]


def fill_data_frame_row(df,dict_val):
    df.loc[len(df)] = list(dict_val.values())
    return None

def fill_evaluation_row_dic(log_name,drift_type,detected_cp,actual_cp,lag,TP,FP,FN_TP,precision,recall,f1_score):
    evaluation_row = {#'collection_name': collection_name,
                      'log_name': log_name,
                      'drift_type':drift_type,
                      'detected_cp': detected_cp,
                      'actual_cp': actual_cp,
                      'lag': lag,
                      'TP': TP,
                      'FP': FP,
                      'FN_TP': FN_TP,
                      'Precision': precision,
                      'Recall': recall,
                      'F1_score': f1_score}
    return evaluation_row


def create_evaluation_report_file():
    columns = [#'collection_name',
               'log_name',
               'drift_type',
               'detected_cp',
               'actual_cp',
               'lag',
               'TP',
               'FP',
               'FN_TP',
               'Precision',
               'Recall',
               'F1_score']
    report = pd.DataFrame(columns=columns)

    return report


def get_precision(TP:int, FP:int)->float:
    """
    Returns the precision
    :param TP(int): True positive value
    :param FP(int): False positive value
    :return:Float: Return the precision or np.nan if division by 0
    """

    precision = np.where((TP + FP) > 0, np.divide(TP, TP + FP), np.nan)
    return precision

def get_recall(TP:int, FN_TP:int)->float:
    """
    Returns the precision
    :param TP(int): True positive value
    :param FN_TP(int): False negative value
    :return:Float: Return the precision or np.nan if division by 0
    """
    recall = np.where(FN_TP > 0, np.divide(TP , FN_TP), np.nan)
    return recall

def get_accuracy(TP:int, FP:int, FN_TP:int)->float:
    return TP//(TP+FP+FN_TP)



def get_f1_score(precision:float, recall:float)->float:


    """
    Returns the F1 score
    :param precision(float): Precision
    :param recall(float): Recall
    :return:Float: Return the f1 score or np.nan if division by 0
    """
    try:
        f1_score = (2*precision*recall)/(precision+recall)
        return f1_score
    except ZeroDivisionError:
        print("Calculation of F1-Score resulted in division by 0.")
        f1_score = np.NaN

    return str(f1_score)

def get_total_evaluation_results(evaluation_report: pd.DataFrame())->pd.dataFrame():
    """
    Returns and aggregated version of the evaluation report
    :param evaluation_report(pd.DataFrame): A dataframe storing the log_name, drift_type, detected_cp,actual_cp,lag,TP,FP,FN_TP,Precision,Recall,F1_score
    :return:pd.DataFrame: An aggregate version of the input dataframe with rows grouped by lag value and the drift_type
    """
    #TODO: The aggregation function should be changed
    aggregations = {
        'TP': 'sum',
        'FP': 'sum',
        'FN_TP': 'sum'}
    grouping = ['lag', 'drift_type']
    evaluation_report_agg = evaluation_report.groupby(grouping).agg(aggregations)
    evaluation_report_agg = evaluation_report_agg.assign(Precision=lambda x: get_precision(x['TP'], x['FP']))
    evaluation_report_agg = evaluation_report_agg.assign(Recall=lambda x: get_recall(x['TP'], x['FN_TP']))
    evaluation_report_agg = evaluation_report_agg.assign(F1_score=lambda x: get_f1_score(x['Precision'], x['Recall']))
    evaluation_report_agg = evaluation_report_agg.assign(Accuracy= lambda x: get_accuracy(x['TP'], x['FP'], x['FN_TP']))
    return evaluation_report_agg



def evaluate_lp_method(col_act:list(DriftInfo),col_det:list(DriftInfo),lag:int)->tuple(dict(str,dict(str,int)),dict(str,float)):
    """
    Returns data (TP,FP,FN,Precision,Recall, and F1 score) resulting of the matching process between the two collection of logs provided
    :param col_act(List[DriftInfo]): A list storing all the actual drift instances
    :param col_det(List[DriftInfo]): A list storing all the detected drift instances
    :param lag(int): The maximal distance a detected change point can have to an actual change point, whilst still counting as a true positive.
    #TODO: Should be changed later when we specify how the lag will be defined for now it's an int:
    :return:Tuple[Dict[str,Dict[str,int]],Dict[str,float]]: A tuple storing two dictionaries. The first dictionary stores the TP, FP and FN for each log id and for each drift type.
                                                        The second dictionary stores the precision, recall and f1score for each drift type.
    """
    evaluation_report = create_evaluation_report_file()
    TP_FP_dict = dict()
    Precision_Recall_f1score = dict()

    log_ids_act = extract_log_ids(col_act, col_det)["actual logs"]
    log_ids_det = extract_log_ids(col_act, col_det)["detected logs"]
    log_ids_det_left = log_ids_det.copy()
    for drift_pos in range(0,len(col_act.drifts)):  # col_act.drifts is a list of drifts each change moment in a log is stored in an instance and each instance belonging to the same log are saved in the same list
        change_index_act = extract_change_trace_index(col_act.drifts[drift_pos])
        TP_FP_dict[log_ids_act[drift_pos]]={}
        Precision_Recall_f1score[log_ids_act[drift_pos]]={}

        if log_ids_act[drift_pos] in log_ids_det:
            pos_drift_to_match = log_ids_det.index(log_ids_act[drift_pos])
            change_index_det = extract_change_trace_index(col_det.drifts[pos_drift_to_match])
            log_ids_det_left.remove(log_ids_act[drift_pos])
            act_drift_types = list(set([cindex_det[1] for cindex_det in change_index_act ]))
            for drift_type in act_drift_types:
                print(drift_type)
                change_index_det_filtered = filter_list_change_indexes(change_index_det,drift_type)
                print("change_index_det_filtered",change_index_det_filtered)
                change_index_act_filtered = filter_list_change_indexes(change_index_act,drift_type)
                print("change_index_act_filtered",change_index_act_filtered)

                TP_FP_dict[log_ids_act[drift_pos]][drift_type] = {"TP":getTP_FP(list_of_change_indexes(change_index_det_filtered),list_of_change_indexes(change_index_act_filtered),lag)[0],
                                                                  "FP":getTP_FP(list_of_change_indexes(change_index_det_filtered),list_of_change_indexes(change_index_act_filtered),lag)[1],
                                                                  "TP_FP":len(list_of_change_indexes(change_index_det_filtered))}
                Precision_Recall_f1score[log_ids_act[drift_pos]][drift_type] = {"Precision": calcPrecisionRecall(list_of_change_indexes(change_index_det_filtered), list_of_change_indexes(change_index_act_filtered), lag, zero_division=np.NaN,count_duplicate_detections = True)[0],
                                                                                "Recall":calcPrecisionRecall(list_of_change_indexes(change_index_det_filtered), list_of_change_indexes(change_index_act_filtered), lag, zero_division=np.NaN,count_duplicate_detections = True)[1],
                                                                                "F1 score":F1_Score(list_of_change_indexes(change_index_det_filtered), list_of_change_indexes(change_index_act_filtered), lag, zero_division=np.NaN)}

                evaluation_row = fill_evaluation_row_dic(col_act.drifts[drift_pos][0].log_id,
                                                             drift_type,
                                                             list_of_change_indexes(change_index_det_filtered),
                                                             list_of_change_indexes(change_index_act_filtered),
                                                             lag,
                                                             TP_FP_dict[log_ids_act[drift_pos]][drift_type]["TP"],
                                                             TP_FP_dict[log_ids_act[drift_pos]][drift_type]["FP"],
                                                             len(list_of_change_indexes(change_index_det_filtered)),
                                                             Precision_Recall_f1score[log_ids_act[drift_pos]][drift_type]["Precision"],
                                                             Precision_Recall_f1score[log_ids_act[drift_pos]][drift_type]["Recall"],
                                                             Precision_Recall_f1score[log_ids_act[drift_pos]][drift_type]["F1 score"])

                fill_data_frame_row(evaluation_report,evaluation_row)


    count = 0
    for path in os.listdir("/output/Evaluation reports"):
        # check if current path is a file
        if os.path.isfile(os.path.join("/output/Evaluation reports", path)):
            count += 1


    evaluation_report.to_csv(output_path+"/evaluation_report"+str(count)+".csv",sep = ";")
    #TODO: Implement an aggregation method
    evaluation_report_agg = get_total_evaluation_results(evaluation_report)
    evaluation_report_agg.to_csv(output_path+"/evaluation_report_agg.csv",sep = ",")

    return (TP_FP_dict, Precision_Recall_f1score)



#TODO: The lag is not defined as a proportion but as an int because we don't have access to the number of traces in the log
def Automated_evaluation (col_act, col_det, lag): #Eval type returns what type of evaluation is needed (TS or TR)
    global TP
    global FP
    global output_path
    output_path = "/output/Evaluation reports"
    TP = 0
    FP = 0
    return evaluate_lp_method(col_act,col_det,lag) #lag should be in percentage and the difference should be in seconds when taking the diff of timestamps


