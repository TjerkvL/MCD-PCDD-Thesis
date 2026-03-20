import random
from src.data_classes.Fill_parm_file_randomly import fill_param_file
from class_collection import *
from generate_collection_of_logs import *
from src.data_classes.class_input import InputParameters


path_detected_collection = "/output/detected"
path_actual_collection = "/output/actual"

path_actual_csv_file = "/output/actual/drift_info.csv"
path_detected_csv_file = "/output/detected/drift_info.csv"
##########################################
######## Testing (perfect case) ##########
##########################################

"""# Actual: collection of logs; Detected: Collection of logs
# Testing: Automated Evaluation
Col_act = Collection()
Col_det = Collection()
Col_act.Extract_collection_of_drifts(path_actual_collection)
Col_det.Extract_collection_of_drifts(path_detected_collection)
Automated_evaluation(Col_act, Col_det, "index_based", 100)

# Actual: csv file; Detected: Collection of logs
Col_act = Collection()
Col_act.import_drift_and_noise_info_from_flat_file_csv(path_actual_csv_file)
# print("csv",Col_act.drifts[1])

Col_det = Collection()
Col_det.Extract_collection_of_drifts(path_detected_collection)

# print(len(Col_act.drifts))
# print(len(Col_det.drifts))
# print("fold",Col_det.drifts[1])
Automated_evaluation(Col_act, Col_det, "index_based", 100)

# Actual: collection of logs; Detected: csv file
Col_act = Collection()
Col_act.import_drift_and_noise_info_from_flat_file_csv(path_actual_collection)
Col_det = Collection()
Col_det.Extract_collection_of_drifts(path_detected_csv_file)
print(Automated_evaluation(Col_act, Col_det, "index_based", 100))

# Actual: csv file; Detected: csv file

Col_act = Collection()
Col_act.import_drift_and_noise_info_from_flat_file_csv(path_actual_csv_file)
Col_det = Collection()
Col_det.Extract_collection_of_drifts(path_detected_csv_file)
print(Automated_evaluation(Col_act, Col_det, "index_based", 100))


"""

from automated_evaluation import Automated_evaluation
from class_collection import *
#Create emtpy actual collection class
Col_act = Collection()
#Create empty tool generated collection class
Col_det = Collection()
#Import the actual collection of logs from a csv file and automatically convert it to a "Collection" class
Col_act.import_drift_and_noise_info_from_flat_file_csv(path_actual_csv_file)
#Import the dected collection of logs from either the csv file or from the set of XES files
Col_det.Extract_collection_of_drifts(path_detected_csv_file)
#Run the Automated evaluation
Automated_evaluation(Col_act, Col_det, lag=100)


from automated_evaluation import Automated_evaluation
from class_collection import *

#Create emtpy actual collection class
Col_act = Collection()
#Create empty tool generated collection class
Col_det = Collection()
#Import the actual collection of logs from a xes files and automatically convert it to a "Collection" class
Col_act.Extract_collection_of_drifts(path_actual_collection)
#Import the dected collection of logs from either the csv file or from the set of XES files
Col_det.Extract_collection_of_drifts(path_detected_collection)
#Run the Automated evaluation
Automated_evaluation(Col_act, Col_det,lag= 100)




##########################################
######## Testing (noisy case) ############
##########################################


def insert_trace_index_noise(trace_index, probability_of_changing_value, percentage_of_change):
    if random.random() < probability_of_changing_value:
        if random.random() >= 0.5:
            trace_index = trace_index * (1 + percentage_of_change)
        elif random.random() < 0.5:
            trace_index = trace_index * (1 - percentage_of_change)
    return trace_index


import copy

probability_of_changing_trace = 1
percentage_of_change = 0.7

#Col_act = Collection()
#Col_act.Extract_collection_of_drifts("C:/Users/ziedk/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 actual")
#Col_act_modified = copy.copy(Col_act)


# print("Before Change",Col_act.drifts[0][0].change_info["1"]["change_trace_index"])

def modify_change_trace_index_values(col, probability_of_changing_value: float, percentage_of_change: float):
    col_modified = copy.copy(col)
    for drifts_pos in range(0, len(col.drifts)):
        for drift_pos in range(0, len(col.drifts[drifts_pos])):
            for change_info_key in list(col.drifts[drifts_pos][drift_pos].change_info.keys()):
                for change_trace_index_pos in range(0, len(
                        col.drifts[drifts_pos][drift_pos].change_info[change_info_key]["change_trace_index"])):
                    col_modified.drifts[drifts_pos][drift_pos].change_info[change_info_key]["change_trace_index"][
                        change_trace_index_pos] = insert_trace_index_noise(
                        col.drifts[drifts_pos][drift_pos].change_info[change_info_key]["change_trace_index"][
                            change_trace_index_pos], probability_of_changing_value, percentage_of_change)
    return col_modified


#print(Col_act.drifts[0][0].drift_type)


def modify_drift_type(col, probability_of_changing_type):
    col_modified = copy.copy(col)
    for drifts_pos in range(0, len(col.drifts)):
        for drift_pos in range(0, len(col.drifts[drifts_pos])):
            drift_types = ["gradual", "sudden", "recurring", "incremental"]
            if random.random() < probability_of_changing_type :
                drift_type = col_modified.drifts[drifts_pos][drift_pos].drift_type
                drift_types.remove(drift_type)
                col_modified.drifts[drifts_pos][drift_pos].drift_type = random.choice(drift_types)

    return col_modified

#print(modify_drift_type(Col_act,1).drifts[0][0])

# print("After_change", Col_act_modified.drifts[0][0].change_info["1"]["change_trace_index"])


# Testing: Automated Evaluation
# Col_act = Collection()
# Col_det = Collection()
# Col_det.Extract_collection_of_drifts(path_detected_collection)
# Automated_evaluation(Col_act_modified, Col_det, 100)


#Col_act = Collection()

#Col_act.Extract_collection_of_drifts("C:/Users/ziedk/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 actual")

#print(Col_act.drifts[0])
#print("#######################")
#del Col_act.drifts[0]
#del Col_act.drifts[0][0].change_info['1']
#print(Col_act.drifts[0])


def delete_change_points(col,probability_to_delete):
    col_modified = copy.copy(col)

    for drifts_pos in range(0, len(col.drifts)):
        to_del_indexes = []
        change_points_to_del = []
        for drift_pos in range(0, len(col.drifts[drifts_pos])):
            if col.drifts[drifts_pos][drift_pos].drift_type in ["sudden","gradual"]:
                if random.random() < probability_to_delete:
                    to_del_indexes.append(drift_pos) ## contains the position of Driftinfo glass which has a type sudden or gradual that should be deleted


            elif col.drifts[drifts_pos][drift_pos].drift_type in ["incremental", "recurring"]:
                for change_point_id in list(col.drifts[drifts_pos][drift_pos].change_info.keys()):
                    if len(col.drifts[drifts_pos][drift_pos].change_info.keys()) <= 1:
                        break

                    if random.random() < probability_to_delete:
                        del col_modified.drifts[drifts_pos][drift_pos].change_info[change_point_id]

        col_modified.drifts[drifts_pos] = [j for i, j in enumerate(col_modified.drifts[drifts_pos]) if
                                                   i not in to_del_indexes]
    return col_modified
                ## if the type if sudden or gradual than the probablity is to delete the whole drift because each drift has only one change point

    ##if the type is recurring or incremental than the probability is the probablity of deleting a single change point. The drift is deleted only when all the change points are deleted

def create_dict_with_input_parameters_rand()->dict():
    """
    Getting parameters from a specific text file placed in the folder 'Data/parameters'
    :param(str) par_file_name: The name of the file that contains the desired parameters
    :return(dict): parameters for the generation of a set of event logs
    """
    parameter_doc = open("../data_classes/param_empty", 'r')
    parameters_input = parameter_doc.read()
    parameter_doc.close()
    parameters_dict = {}
    for line in parameters_input.split('\n'):
        if line:
            par = line.split(': ')[0]
            value = line.split(': ')[1]
            if '/' in value:
                value = [datetime.strptime(v, '%Y/%m/%d %H:%M:%S') for v in value.split(',')]
            elif '-' in value:
                value = value.split('-')
            else:
                value = value.split(', ')

            try:
                value = [ast.literal_eval(v) for v in value]
            except:
                pass
            parameters_dict[par] = value

    parameters_dict['Folder_name'] = "default_name"

    return parameters_dict


def get_parameters_rand()->InputParameters:
    """
    Get the parameters to generate the logs
    :param path(str): contains the name of the default parameter file to use
    :return (InputParameters): A class instance that stores the input parameters
    """
    parameters_dict = create_dict_with_input_parameters_rand()
    #print(parameters_dict)
    parameters = InputParameters(**parameters_dict)
    return parameters

def generate_random_col_logs():
    #Fill the param_file with random values
    fill_param_file()
    #create an InputParameters class of the randomly generated parameters
    rand_parameters = get_parameters_rand()
    # Generate a collection of logs from the
    single_processing_generate_logs(rand_parameters)
    return None



def full_testing(col: Collection, probability_to_delete = 0.5, probability_of_changing_type = 0.5, probability_of_changing_value=0.5, percentage_of_change=0.50):
    val = "Yes"
    print("Do you want to modify the collection of logs ?")

    while val=="Yes":
        while val not in ["Yes","No"]:
            print("Do you want to modify the collection of logs ?")
            val = input("Error in entry print Yes or No")
        if val == "Yes":
            print("What kind of modification to the collection of logs do you want to implement ?")
            print("Type 1 for deleting change moments")
            print("Type 2 for modifying drift types")
            print("Type 3 for modify change trace index values")

            val = input("Write 1, 2 or 3")
            while val not in ["1","2","3"]:
                val = input("Error in entery Write 1, 2, or 3")
                if val == "1":
                    col = delete_change_points(col, probability_to_delete)
                if val == "2":
                    col = modify_drift_type(col, probability_of_changing_type)
                if val == "3":
                    col = modify_change_trace_index_values(col, probability_of_changing_value, percentage_of_change)
        print("Do you want to add another modification ?")
        val = input("Yes or No")
        while val not in ["Yes", "No"]:
            print("Error in entry do you want to add another modification ?")
            val = input("Yes or No")
        if val == "No":
            break
    return col


Col = Collection()

Col.Extract_collection_of_drifts("C:/Users/ziedk/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 actual")

print("before change")
print(Col.drifts)
print("++++++++++++++++++++++++")
print("after change")
print(full_testing(Col).drifts)



