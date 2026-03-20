import re
import datetime
from pm4py.objects.process_tree.importer import importer as ptml_importer
import pm4py
from pm4py.objects.conversion.bpmn import converter as bpmn_converter
from pm4py.objects.conversion.wf_net import converter as wf_net_converter
from pm4py.objects.petri_net.importer import importer as pnml_importer


def input_int(str_in, default = 10):
    int_one = input(str_in)
    if int_one == "":
        print('Set to default:', default)
        return default
    while re.fullmatch('[0-9]+', int_one) is None:
        print('Wrong input! It has to be an integer.')
        int_one = input(str_in)
    return int(int_one)


def input_int_max(str_in, min_in):
    int_one = input(str_in)
    while re.fullmatch('[0-9]+', int_one) is None or int(int_one) <= min_in:
        print('Wrong input! It has to be an integer larger than the minimum of the activities duration.')
        int_one = input(str_in)
    return int(int_one)


def input_int_odd(str_in):
    int_one = input(str_in)
    if int_one == "":
        print('Default: 3')
        return 3
    while re.fullmatch('[0-9]*[13579]', int_one) is None:
        print('Wrong input! It has to be an odd integer.')
        int_one = input(str_in)
    return int(int_one)


def input_int_even(str_in):
    int_one = input(str_in)
    if int_one == "":
        print('Default: 4')
        return 4
    while re.fullmatch('[0-9]*[02468]', int_one) is None:
        print('Wrong input! It has to be an even integer.')
        int_one = input(str_in)
    return int(int_one)


def input_season(start_point, end_point):
    if start_point == 0:
        number_of_seasonal_changes = input_int_even(
            "Number of seasonal changes (boundary changes excluded) of the model versions, which needs to be an even number (int): ")
    elif end_point == 1:
        number_of_seasonal_changes = input_int("Number of seasonal changes of the model versions (int): ")
    else:
        number_of_seasonal_changes = input_int_odd(
            "Number of seasonal changes (boundary changes excluded) of the model versions, which needs to be an odd number (int): ")
    return number_of_seasonal_changes


def input_int_hun(str_in):
    int_one = input(str_in)
    if int_one == "":
        print('Default: 1000')
        return 1000
    while re.fullmatch('[0-9]+', int_one) is None or int(int_one) < 100:
        print('Wrong input! It has to be an integer larger than 99.')
        int_one = input(str_in)
    return int(int_one)


def input_drift(str_in):
    drift_type = input(str_in)
    if drift_type == "":
        print('Default: sudden')
        return 'sudden'
    while drift_type != "sudden" and drift_type != "gradual" and drift_type != "recurring" and drift_type != "incremental":
        print("Wrong input! It has to be 'sudden', 'gradual', 'recurring' or 'incremental'.")
        drift_type = input(str_in)
    return drift_type


def input_percentage(str_in, default = 0.5):
    per_one = input(str_in)
    if per_one == "":
        print('Set to default:', default)
        return default
    while re.fullmatch('0|0\.[0-9]+|1', per_one) is None:
        print('Wrong input! It must be a floating point number between 0 and 1.')
        per_one = input(str_in)
    return float(per_one)


def input_percentage_end(str_in, start):
    per_one = input(str_in)
    if per_one == "":
        per_one = start + (1-start)*0.8
        print('Default: '+str(per_one))
        return float(per_one)
    while re.fullmatch('0|0\.[0-9]+|1', per_one) is None or float(per_one) <= start:
        print('Wrong input! It must be a floating point number between 0 and 1 and greater than ' + str(start)+'.')
        per_one = input(str_in)
    return float(per_one)


def input_per_half(str_in):
    per_one = input(str_in)
    if per_one == "":
        print('Default: 0.25')
        return 0.25
    while re.fullmatch('0\.[0-4][0-9]*', per_one) is None:
        print('Wrong input! It must be a floating point number between 0 and 0.5.')
        per_one = input(str_in)
    return float(per_one)


def input_per_not_null(str_in):
    per_one = input(str_in)
    if per_one == "":
        print('Default: 0.5')
        return 0.5
    while re.fullmatch('0\.[0-9]*', per_one) is None:
        print('Wrong input! It must be a floating point number between 0 and 1.')
        per_one = input(str_in)
    return float(per_one)


def input_date(str_in):
    dat_one = input(str_in)
    if dat_one == "":
        dat_one = '98/3/8 8:0:0'
        print('Default: 98/3/8 8:0:0')
    while re.fullmatch(
            '[0-9][0-9]/(([1-2]?[0-9])|(3[0-1]))/((0?[0-9])|(1[0-2])) (([0-9])|(1[0-9])|(2[0-3])):([0-9]|([1-5][0-9])):([0-9]|([1-5][0-9]))',
            dat_one) is None:
        print("Wrong input! It has to be in this format y/d/m H:M:S like '20/23/8 8:0:0'")
        dat_one = input(str_in)
    return datetime.datetime.strptime(dat_one, '%y/%d/%m %H:%M:%S')


def input_typ_gradual(str_in):
    grad_one = input(str_in)
    if grad_one == "":
        grad_one = 'linear'
        print('Default: linear')
    while grad_one != "linear" and grad_one != "exponential":
        print("Wrong input! It has to be 'linear' or 'exponential'.")
        grad_one = input(str_in)
    return grad_one


def input_type_cf(str_in):
    str_cf = input(str_in)
    while str_cf != 'change_activity' and str_cf != 'change_operator' and str_cf != 'change_tree_fragment' and str_cf != 'delete_silent_ac':
        print("Wrong input! It has to be 'change_activity', 'change_operator', 'change_tree_fragment' and 'delete_silent_ac'")
        str_cf = input(str_in)
    return str_cf


def input_parameters():
    mode = input_int("MODE: most frequent number of visible activities (default 20): ", default = 20)
    min_in = input_int("MIN: minimum number of visible activities (default 10): ", default = 10)
    while min_in > mode:
        print("Wrong input! MIN has to be smaller than MODE (" + str(mode) + ").")
        min_in = input_int("MIN: minimum number of visible activities (default 10): ", default = 10)
    max_in = input_int("MAX: maximum number of visible activities (default 30): ", default = 30)
    while max_in < mode:
        print("Wrong input! MAX has to be bigger than MODE (" + str(mode) + ").")
        max_in = input_int("MAX: maximum number of visible activities (default 30): ", default = 30)
    parameters = {'mode': mode,
                  'min': min_in,
                  'max': max_in,
                  'sequence': input_percentage(
                      "SEQUENCE: probability to add a sequence operator to tree (default 0.25): ", default=0.25),
                  'choice': input_percentage("CHOICE: probability to add a choice operator to tree (default 0.25): ", default=0.25),
                  'parallel': input_percentage(
                      "PARALLEL: probability to add a parallel operator to tree (default 0.25): ", default=0.25),
                  'loop': input_percentage("LOOP: probability to add a loop operator to tree (default 0.25): ", default=0.25),
                  'or': input_percentage("OR: probability to add an or operator to tree (default 0.00): ", default=0.00),
                  'silent': input_percentage(
                      "SILENT: probability to add silent activity to a choice or loop operator (default 0.25): ", default=0.25),
                  'duplicate': input_percentage("DUPLICATE: probability to duplicate an activity label (default 0.00): ", default=0.00),
                  'lt_dependency': input_percentage(
                      "LT_DEPENDENCY: probability to add a random dependency to the tree (default 0.00): ", default=0.00),
                  'infrequent': input_percentage(
                      "INFREQUENT: probability to make a choice have infrequent paths (default 0.25): ", default=0.25),
                  'no_models': input_int("NO_MODELS: number of trees to generate from model population (default 10): ", default = 10),
                  'unfold': input_int(
                      "UNFOLD: whether or not to unfold loops in order to include choices underneath in dependencies: 0=False, 1=True\n"
                      "\t if lt_dependency <= 0: this should always be 0 (False)\n"
                      "\t if lt_dependency > 0: this can be 1 or 0 (True or False) (default 1): ", default = 1),
                  'max_repeat': input_int(
                      "MAX_REPEAT: maximum number of repetitions of a loop (only used when unfolding is True) (default 10): ", default = 10)}
    return parameters


def input_yes_no(str_in):
    str_cf = input(str_in)
    if str_cf == "":
        str_cf = 'yes'
        print('Default: yes')
    while str_cf != 'yes' and str_cf != 'no':
        print("Wrong input! It has to be 'yes' or 'no'")
        str_cf = input(str_in)
    return str_cf


def input_no_yes(str_in):
    str_cf = input(str_in)
    if str_cf == "":
        str_cf = 'no'
        print('Default: no')
    while str_cf != 'yes' and str_cf != 'no':
        print("Wrong input! It has to be 'yes' or 'no'")
        str_cf = input(str_in)
    return str_cf


def input_start(str_in):
    str_cf = input(str_in)
    if str_cf == "":
        str_cf = 'random'
        print('Default: random')
    while str_cf != 'import' and str_cf != 'random':
        print(
            "Wrong input! It has to be import or random'.")
        str_cf = input(str_in)
    return str_cf


def input_start_second(str_in):
    str_cf = input(str_in)
    if str_cf == "":
        str_cf = 'one_model'
        print('Default: one_model')
    while str_cf != 'two_models' and str_cf != 'one_model':
        print(
            "Wrong input! It has to be two_models or one_model'.")
        str_cf = input(str_in)
    return str_cf


def generate_tree_out_of_file(str_in):
    str_cf = input(str_in)
    wrong_input = True
    while wrong_input:
        if re.fullmatch('.*\.ptml', str_cf):
            wrong_input = False
            return ptml_importer.apply(str_cf)
        elif re.fullmatch('.*\.bpmn', str_cf):
            bpmn_tree = pm4py.read_bpmn(str_cf)
            net, im, fm = bpmn_converter.apply(bpmn_tree)
            wrong_input = False
            return wf_net_converter.apply(net, im, fm)
        elif re.fullmatch('.*\.pnml', str_cf):
            net, im, fm = pnml_importer.apply(str_cf)
            wrong_input = False
            return wf_net_converter.apply(net, im, fm)
        else:
            print("Wrong input! It has to be a 'ptml', 'bpmn' or 'pnml' File.")
            str_cf = input(str_in)


def input_swap_acs(str_in, activities):
    str_cf = input(str_in)
    wrong = True
    while wrong:
        if re.fullmatch('.*,.*', str_cf) is None:
            print("Wrong input! There must be a comma between the two activities, like: a,b")
            str_cf = input(str_in)
        else:
            act = str_cf.split(',')
            contains_first = False
            contains_second = False
            for leaf in activities:
                if leaf._get_label() == act[0].strip():
                    contains_first = True
                if leaf._get_label() == act[1].strip():
                    contains_second = True
            if contains_first and contains_second:
                wrong = False
                return act
            else:
                print(
                    "Wrong input! One or both activities do not exist. The following are possible: " + str(activities))
                str_cf = input(str_in)


def input_ac(str_in, activities):
    str_cf = input(str_in)
    wrong = True
    while wrong:
        contains = False
        for leaf in activities:
            if leaf._get_label() == str_cf.strip() or (leaf._get_label() is None and str_cf.strip() == "*tau*"):
                contains = True
                break
        if contains:
            wrong = False
        else:
            print("Wrong input! The activity does not exist. The following are possible: " + str(activities))
            str_cf = input(str_in)
    return str_cf


def input_ops(str_in):
    str_op = input(str_in)
    while str_op != 'or' and str_op != 'xor' and str_op != 'xor loop' and str_op != 'and' and str_op != 'seq':
        print("Wrong input! The following operators are allowed only: or, xor, xor loop, and, seq.")
        str_op = input(str_in)
    return str_op


def input_comp(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'middle'
        print('Default: middle')
    while str_op != 'simple' and str_op != 'middle' and str_op != 'complex':
        print("Wrong input! The following operators are allowed only: simple, middle and complex.")
        str_op = input(str_in)
    return str_op


def input_no(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'random_model'
        print('Default: random_model')
    while str_op != 'changed_model' and str_op != 'random_model':
        print("Wrong input! Only the following types of noise exist: changed_model and random_model.")
        str_op = input(str_in)
    return str_op


def input_cft_ac(str_in):
    str_op = input(str_in)
    while str_op != 'swap_acs' and str_op != 'delete_ac' and str_op != 'replace_ac' and str_op != 'add_ac':
        print("Wrong input! Only the following operators exist: swap_acs, delete_ac, replace_ac and add_ac.")
        str_op = input(str_in)
    return str_op


def input_cft_op(str_in):
    str_op = input(str_in)
    while str_op != 'replace_op' and str_op != 'swap_ops':
        print("Wrong input! Only the following operators exist: replace_op and swap_ops.")
        str_op = input(str_in)
    return str_op


def input_cft_tf(str_in):
    str_op = input(str_in)
    while str_op != 'add_fragment' and str_op != 'delete_fragment' and str_op != 'swap_fragments' and str_op != 'move_fragment':
        print(
            "Wrong input! Only the following operators exist: add_fragment, delete_fragment, swap_fragments and move_fragment.")
        str_op = input(str_in)
    return str_op


def input_ra_ch(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'random'
        print('Default: random')
    while str_op != 'random' and str_op != 'controlled':
        print("Wrong input! Only the following noise types exist: random and controlled.")
        str_op = input(str_in)
    return str_op


def input_tree(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'evolved_version'
        print('Default: evolved_version')
    while str_op != 'initial_version' and str_op != 'evolved_version':
        print("Wrong input! Only the following is allowed: 'initial_version' and 'evolved_version'.")
        str_op = input(str_in)
    return str_op


def input_tree_one(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'last_version'
        print('Default: last_version')
    while str_op != 'first_version' and str_op != 'last_version':
        print("Wrong input! Only the following is allowed: 'first_version' and 'last_version'.")
        str_op = input(str_in)
    return str_op


def input_end(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'end'
        print('Default: end')
    while str_op != 'end' and str_op != 'into':
        print("Wrong input! Only the following is allowed: 'end' and 'into'.")
        str_op = input(str_in)
    return str_op


def input_im(str_in):
    str_op = input(str_in)
    if str_op == "":
        str_op = 'random'
        print('Default: random')
    while str_op != 'evolve' and str_op != 'import' and str_op != 'random':
        print("Wrong input! Only the following is allowed: 'evolve', 'random' and 'import'.")
        str_op = input(str_in)
    return str_op
