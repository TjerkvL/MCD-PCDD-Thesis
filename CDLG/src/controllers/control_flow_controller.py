import copy
from random import randint
from copy import deepcopy
import numpy as nmp

from src.controllers.input_controller import input_int, input_ac, input_type_cf, input_ops, input_yes_no, input_cft_ac, \
    input_cft_op, input_cft_tf, input_ra_ch, input_per_not_null, input_percentage
from src.controllers.process_tree_controller import swap_two_existing_activities, visualise_tree, \
    delete_activity, replace_operator, add_activity_with_operator, delete_part_tree, \
    replace_activity, swap_tree_fragments, randomize_tree_one, add_activity, swap_operator, \
    randomize_tree_two, randomize_tree_three, get_required_ac, randomize_tree_more, move_tree_fragment, \
    delete_silents, count_real_acs, get_unique_list


def change_tree_on_control_flow(tree):
    """ Changing the process tree to the desired evolved model

    :param tree: process tree
    :return: changed tree version
    """
    deleted_acs = []
    added_acs = []
    moved_acs = []
    drift_tree = copy.deepcopy(tree)
    ran = input_ra_ch('Controlled or random evolution of the process tree version [controlled, random]: ')
    if ran == 'random':
        evolution_stage = input_per_not_null("Proportion of the activities in the process tree to be affected by random evolution (0 < x < 1): ")
        return evolve_tree_randomly_terminal(drift_tree, evolution_stage)
    else:
        print("\n--- INFORMATION FOR THE EVOLUTION ---\n"
              "The following main operators are available for the evolution of the process tree versions:\n"
              "\t- change_activity: all procedures to change activities [add_ac, swap_acs, delete_ac, replace_ac]\n"
              "\t- change_operator: all procedures to change operators [replace_op, swap_ops]\n"
              "\t- change_tree_fragment: all procedures to change a tree fragment [add_fragment, delete_fragment, swap_fragments, move_fragment]\n"
              "\t- delete_silent_ac: delete an undesired silent activity\n"
              "The first process tree version opened as a picture provides orientation for evolution.\n"
              "To achieve the desired version, multiple evolutions may need to be performed.\n"
              "Please note that if the input is not correct, the tree version will not change (depth starts with 0 at the parent node).\n"
              "Moreover, a node with a 'xor loop' operator can only have at least two and at most three children.\n"
              "The following activities are contained in the tree: " + str(tree._get_leaves()) + "\n")
        visualise_tree(tree)
        continue_evolve = 'yes'
        i = 0
        drift_tree = copy.deepcopy(tree)
        while continue_evolve == 'yes':
            i = i + 1
            control_flow_type = input_type_cf(
                "Operator for the " + str(
                    i) + ". intermediate evolution of the process tree version [change_activity, change_operator, change_tree_fragment, delete_silent_ac]: ")
            drift_tree, deleted_ac, added_ac, moved_ac = control_flow_change(drift_tree, control_flow_type)
            deleted_acs.extend(deleted_ac)
            added_acs.extend(added_ac)
            moved_acs.extend(moved_ac)
            visualise_tree(drift_tree)
            continue_evolve = input_yes_no(
                "Do you want to continue with the evolution of the version [yes, no]: ")
        return drift_tree, deleted_acs, added_acs, moved_acs


def change_tree_on_control_flow_incremental(tree, round_ev):
    """ Changing the process tree to the desired evolved model for incremental drift

    :param round_ev: number of evolved model
    :param tree: process tree
    :return: changed tree version
    """
    continue_evolve = 'yes'
    drift_tree = copy.deepcopy(tree)
    i = 0
    deleted_acs = []
    added_acs = []
    moved_acs = []
    while continue_evolve == 'yes':
        i = i + 1
        control_flow_type = input_type_cf(
            "Operator for the " + str(i) + ". intermediate evolution of the " + str(
                round_ev) + ". evolving model version [change_activity, change_operator, change_tree_fragment, delete_silent_ac]: ")
        drift_tree, deleted_ac, added_ac, moved_ac = control_flow_change(drift_tree, control_flow_type)
        deleted_acs.extend(deleted_ac)
        added_acs.extend(added_ac)
        moved_acs.extend(moved_ac)
        visualise_tree(drift_tree)
        continue_evolve = input_yes_no("Do you want to continue with the evolution of the " + str(
            round_ev) + ". evolving model version [yes, no]: ")
    return drift_tree, deleted_acs, added_acs, moved_acs


def change_tree_on_control_flow_incremental_random(tree, round_ev):
    """ Changing the process tree to a random evolved model for incremental drift

    :param round_ev: number of evolved model
    :param tree: process tree
    :return: changed tree
    """
    drift_tree = copy.deepcopy(tree)
    evolution_stage = input_percentage(
        'Proportion of the activities in the ' + str(round_ev) + '. evolving model version to be affected by random evolution (0 < x < 1): ')
    return evolve_tree_randomly_terminal(drift_tree, evolution_stage)


def control_flow_change(drift_tree, control_flow_type):
    """ Changing the process tree depending on the set control flow type

    :param drift_tree: process tree to be changed
    :param control_flow_type: way of change
    :return: changed tree version
    """
    deleted_acs = []
    added_acs = []
    moved_acs = []
    if control_flow_type == 'change_activity':
        cft_ac_type = input_cft_ac(
            "Procedure for changing activity/ies in the process tree version [add_ac, swap_acs, delete_ac, replace_ac]: ")
        if cft_ac_type == 'swap_acs':
            act_one = input_ac("First activity to be swapped " + str(drift_tree._get_leaves()) + ": ",
                               drift_tree._get_leaves())
            act_two = input_ac("Second activity to be swapped " + str(drift_tree._get_leaves()) + ": ",
                               drift_tree._get_leaves())
            drift_tree, ch_acs = swap_two_existing_activities(drift_tree, act_one.strip(), act_two.strip())
            if len(ch_acs) == 2:
                moved_acs.extend(get_unique_list(ch_acs))
        elif cft_ac_type == 'delete_ac':
            act = input_ac("Activity to be deleted " + str(drift_tree._get_leaves()) + ": ",
                                drift_tree._get_leaves())
            drift_tree, ch_ac = delete_activity(drift_tree, act.strip())
            deleted_acs.append(ch_ac)
        elif cft_ac_type == 'replace_ac':
            act_one = input_ac("Existing activity to be replaced " + str(drift_tree._get_leaves()) + ": ",
                               drift_tree._get_leaves())
            act_two = input("New activity (a): ")
            drift_tree, ch_acs = replace_activity(drift_tree, act_one, act_two)
            if ch_acs[0]._get_label() is not None:
                deleted_acs.append(ch_acs[0])
            added_acs.append(ch_acs[1])
        elif cft_ac_type == 'add_ac':
            act = input("New activity to be added (a): ")
            depth = input_int("Depth of the operator node, where the activity will be added (int): ")
            drift_tree, ch_ac = add_activity(drift_tree, act, depth)
            added_acs.append(ch_ac)
    elif control_flow_type == 'change_operator':
        cft_op_type = input_cft_op("Procedure for changing operator/s in the process tree version [replace_op, swap_ops]: ")
        if cft_op_type == 'replace_op':
            old_operator = input_ops("Existing operator to be replaced [xor, seq, or, xor loop, and]: ")
            depth_node = input_int("Depth of the node with the operator to be changed (int): ")
            drift_tree, ch_acs = replace_operator(drift_tree, depth_node, old_operator)
            moved_acs.extend(ch_acs)
            moved_acs = get_unique_list(moved_acs)
        elif cft_op_type == 'swap_ops':
            operator_first = input_ops("First operator to be swapped [xor, seq, or, xor loop, and]: ")
            depth_first = input_int("Depth of the node with the first operator to be swapped (int): ")
            ac_one = get_required_ac(drift_tree, depth_first, operator_first, 'first')
            operator_second = input_ops("Second operator to be swapped [xor, seq, or, xor loop, and]: ")
            depth_second = input_int("Depth of the node with the second operator to be swapped (int): ")
            ac_two = get_required_ac(drift_tree, depth_second, operator_second, 'second')
            drift_tree, ch_acs_one = swap_operator(drift_tree, depth_first, operator_second, operator_first, ac_one)
            drift_tree, ch_acs_two = swap_operator(drift_tree, depth_second, operator_first, operator_second, ac_two)
            moved_acs.extend(ch_acs_one)
            moved_acs.extend(ch_acs_two)
            moved_acs = get_unique_list(moved_acs)
    elif control_flow_type == 'change_tree_fragment':
        cft_tf_type = input_cft_tf(
            "Procedure for changing fragment/s of the process tree version [add_fragment, delete_fragment, swap_fragments, move_fragment]: ")
        if cft_tf_type == 'add_fragment':
            activity_added = input("Activity to be added (a): ")
            operator_added = input_ops("Operator to be added [xor, seq, or, xor loop, and]: ")
            direction = 'right'
            if operator_added == 'seq' or operator_added == 'xor loop':
                direction = input(
                    "Activity to be added left or right on operator " + operator_added + " [left, right]: ")
            depth = input_int(
                "Depth (as parent x = 0) of the node where the operator and the activity to be inserted (int): ")
            drift_tree, ac, ch_acs = add_activity_with_operator(drift_tree, activity_added, operator_added, depth, direction)
            added_acs.append(ac)
            moved_acs.extend(get_unique_list(ch_acs))
        elif cft_tf_type == "delete_fragment":
            depth = input_int(
                "Depth (as parent x = 0) of the node with the start operator of the subtree to be deleted (int): ")
            operator_deleted = input_ops("Start operator of subtree to be deleted [xor, seq, or, xor loop, and]: ")
            drift_tree, ch_acs = delete_part_tree(drift_tree, depth, operator_deleted)
            deleted_acs.extend(get_unique_list(ch_acs))
        elif cft_tf_type == "swap_fragments":
            drift_tree, ch_acs = swap_tree_fragments(drift_tree)
            moved_acs.extend(get_unique_list(ch_acs))
        elif cft_tf_type == "move_fragment":
            operator_start = input_ops("Start operator of tree fragment to be moved [xor, seq, or, xor loop, and]: ")
            operator_depth = input_int("Depth of the first node of the tree fragment to be moved (int): ")
            drift_tree, ch_acs = move_tree_fragment(drift_tree, operator_start, operator_depth)
            moved_acs.extend(get_unique_list(ch_acs))
    else:
        operator = input_ops(
            "Operator, which is the parent of the silent activity to be deleted [xor, xor loop, seq, or, and]: ")
        depth = input_int(
            "Depth of the operator node, which is the parent of the silent activity to be deleted (int): ")
        drift_tree = delete_silents(drift_tree, operator, depth)
    return drift_tree, deleted_acs, added_acs, moved_acs


def evolve_tree_randomly_terminal(drift_tree, evolution_stage):
    """ Random change of the process tree for the terminal

    :param drift_tree: tree to be changed
    :param evolution_stage: percentage of activities to be affected by the change
    :return: randomly evolved process tree version
    """
    acs = count_real_acs(drift_tree._get_leaves())
    changed_acs = []
    added_acs = []
    deleted_acs = []
    moved_acs = []
    rounds = int(round(acs * evolution_stage + 0.001))
    if rounds == 0:
        rounds = int(nmp.ceil(acs * evolution_stage))
    i = 0
    count = 1
    happen = ""
    while i < rounds:
        happen_be = ""
        ran = randint(1, rounds - i)
        if i == 1:
            ran = randint(1, rounds - i)
        if ran == 1:
            happen_be, worked, count = randomize_tree_one(drift_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_one(drift_tree, happen_be, changed_acs, count)
        elif ran == 2:
            happen_be, worked, count = randomize_tree_two(drift_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_two(drift_tree, happen_be, changed_acs, count)
        elif ran == 3:
            happen_be, worked, count = randomize_tree_three(drift_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(drift_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(drift_tree, happen_be, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_three(drift_tree, happen_be, ran, changed_acs, count)
        else:
            happen_be, worked, count = randomize_tree_more(drift_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(drift_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(drift_tree, happen_be, changed_acs, count)
                elif ran == 3:
                    happen_be, worked, count = randomize_tree_three(drift_tree, happen_be, ran, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_more(drift_tree, happen_be, ran, changed_acs, count)
        happen_spl = happen_be.split(";")
        last = len(happen_spl)
        happen = happen + happen_spl[last - 2] + "; "
        i = i + ran
        happen_ac = happen.split(';')
        if happen_ac[len(happen_ac)-2].strip() == "activity replaced":
            deleted_acs.append(changed_acs[len(changed_acs)-2])
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity deleted":
            deleted_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "tree fragment deleted":
            deleted_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
        elif happen_ac[len(happen_ac)-2].strip() == "activity added":
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity and operator added":
            added_acs.append(changed_acs[len(changed_acs)-1])
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)-1])
        else:
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
    print("\nControl-flow changes: " + happen)
    print("Activities affected by the changes:" + str(changed_acs) + "\n")
    return drift_tree, deleted_acs, added_acs, moved_acs


def evolve_tree_randomly(previous_process_tree, evolution_stage):
    """ Random change of the process tree

    :param new_process_tree: tree to be changed
    :param evolution_stage: percentage of activities to be affected by the change
    :return: randomly evolved process tree version
    """
    new_process_tree = deepcopy(previous_process_tree)
    acs = count_real_acs(new_process_tree._get_leaves())
    changed_acs = []
    added_acs = []
    deleted_acs = []
    moved_acs = []
    rounds = int(round(acs * evolution_stage + 0.001))
    if rounds == 0:
        rounds = int(nmp.ceil(acs * evolution_stage))
    i = 0
    count = 1
    happen = ""
    while i < rounds:
        happen_be = ""
        ran = randint(1, rounds - i)
        if i == 1:
            ran = randint(1, rounds - i)
        if ran == 1:
            happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
        elif ran == 2:
            happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
        elif ran == 3:
            happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
        else:
            happen_be, worked, count = randomize_tree_more(new_process_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
                elif ran == 3:
                    happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_more(new_process_tree, happen_be, ran, changed_acs, count)
        happen_spl = happen_be.split(";")
        last = len(happen_spl)
        happen = happen + happen_spl[last - 2] + "; "
        i = i + ran
        happen_ac = happen.split(';')
        if happen_ac[len(happen_ac)-2].strip() == "activity replaced":
            deleted_acs.append(changed_acs[len(changed_acs)-2])
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity deleted":
            deleted_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "tree fragment deleted":
            deleted_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
        elif happen_ac[len(happen_ac)-2].strip() == "activity added":
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity and operator added":
            added_acs.append(changed_acs[len(changed_acs)-1])
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)-1])
        else:
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
    return new_process_tree, deleted_acs, added_acs, moved_acs
