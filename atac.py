"""
    Written by Beyazit Yalcinkaya as a part of the
    Automating Timed Automata Design Project conducted
    by the METU Cyber-Physical Systems Research Group.
"""

from lark import Lark
from re import sub
import objects as objs

"""
Internal global variables.
"""
_TA = None
_current_template_name = ""
_output_file_name = ""

Grammar = """
    start  : init | tran | invrt
    init   : TEMPLATE_NAME " can only be " LOCATION_NAME                               -> single_loc_init
           | TEMPLATE_NAME " can be " locs " and it is initially " LOCATION_NAME       -> multi_loc_init
    locs   : LOCATION_NAME
           | LOCATION_NAME " " locs
    tran   : "it can go from " locs " to " locs                                        -> simple_tran
           | "it can send " SYNCH_NAME " and go from " locs " to " locs                -> synch_tran
           | "if " sc " then it can go from " locs " to " locs                         -> synch_cond_simple_tran
           | "if " tc " then it can go from " locs " to " locs                         -> time_cond_simple_tran
           | "if " tc " then it can send " SYNCH_NAME " and go from " locs " to " locs -> time_cond_synch_tran
           | "if " sc " and " tc " then it can go from " locs " to " locs              -> synch_time_cond_simple_tran
    invrt  : ic " in " locs                                                            -> invrt
    sc     : SYNCH_NAME " is received"
    tc     : "the time spent after " sel " " LOCATION_NAME " is " constr
           | "the time spent after " sel " " LOCATION_NAME " is " constr " and " tc
    ic     : "the time spent after " sel " " LOCATION_NAME " cannot be " constr
           | "the time spent after " sel " " LOCATION_NAME " cannot be " constr " and " ic
    constr : "more than " NUMBER                                                       -> more_than
           | "more than or equal to " NUMBER                                           -> more_than_or_equal_to
           | "less than " NUMBER                                                       -> less_than
           | "less than or equal to " NUMBER                                           -> less_than_or_equal_to
           | "equal to " NUMBER                                                        -> equal_to
    sel    : "entering"                                                                -> sel_ent
           | "leaving"                                                                 -> sel_lea
    %import common.CNAME -> TEMPLATE_NAME
    %import common.CNAME -> SYNCH_NAME
    %import common.CNAME -> LOCATION_NAME
    %import common.NUMBER
"""

parser = Lark(Grammar, parser='earley')

def extract_locations(t):
    """
    Extracts locations from the given tree and return a list of locations.

    Args:
        t: A tree with locations on nodes.
    Returns:
        List of locations.
    """
    if len(t.children) == 1:
        return [t.children[0].value.capitalize()]
    return [t.children[0].value.capitalize()] + extract_locations(t.children[1])

def extract_time_condition(t):
    """
    Extracts condtions based on clocks from the given tree.

    Args:
        t: A tree with timed condition.
    Returns:
        is_entering: Bool. Indicates if the clocks is reset
                     while entering lk or leaving.
        lk: Location entering/leaving which the clock is reset.
        cond: Condtion string.
    """
    is_entering = True if t.children[0].data == "sel_ent" else False
    lk = t.children[1].capitalize()
    cond = ""
    if t.children[2].data == "more_than":
        cond = " > " + t.children[2].children[0].value
    elif t.children[2].data == "more_than_or_equal_to":
        cond = " >= " + t.children[2].children[0].value
    elif t.children[2].data == "less_than":
        cond = " < " + t.children[2].children[0].value
    elif t.children[2].data == "less_than_or_equal_to":
        cond = " <= " + t.children[2].children[0].value
    elif t.children[2].data == "equal_to":
        cond = " == " + t.children[2].children[0].value
    return is_entering, lk, cond

def extract_invrnt_condition(t):
    """
    Extracts condtions for invariants based on clocks from the given tree.

    Args:
        t: A tree with timed condition.
    Returns:
        is_entering: Bool. Indicates if the clocks is reset
                     while entering lk or leaving.
        lk: Location entering/leaving which the clock is reset.
        cond: Condtion string.
    """
    is_entering = True if t.children[0].data == "sel_ent" else False
    lk = t.children[1].capitalize()
    cond = ""
    if t.children[2].data == "more_than":
        cond = " <= " + t.children[2].children[0].value
    elif t.children[2].data == "more_than_or_equal_to":
        cond = " < " + t.children[2].children[0].value
    return is_entering, lk, cond

def run_instruction(t):
    """
    Runs instructions according to the parse tree.

    Args:
        t: Parse tree of a line.
    """
    global _TA, _current_template_name
    if t.data == "single_loc_init":
        if _TA:
            _TA.complete_template()
        _current_template_name = t.children[0].value.capitalize()
        initial_location = t.children[1].value.capitalize()
        _TA = objs.Template(_current_template_name, [initial_location], initial_location)
    elif t.data == "multi_loc_init":
        if _TA:
            _TA.complete_template()
        _current_template_name = t.children[0].value.capitalize()
        locations = extract_locations(t.children[1])
        initial_location = t.children[2].value.capitalize()
        locations.remove(initial_location)
        locations = [initial_location] + locations
        _TA = objs.Template(_current_template_name, locations, initial_location)
    elif t.data == "simple_tran":
        lis, ljs = extract_locations(t.children[0]), extract_locations(t.children[1])
        for li in lis:
            for lj in ljs:
                _TA.create_transition(transition=(li, lj), receive_synch="", send_synch="")
    elif t.data == "synch_tran":
        synch, lis, ljs = t.children[0] + "!", extract_locations(t.children[1]), extract_locations(t.children[2])
        for li in lis:
            for lj in ljs:
                _TA.create_transition(transition=(li, lj), receive_synch="", send_synch=synch)
    elif t.data == "synch_cond_simple_tran":
        synch, lis, ljs = t.children[0].children[0] + "?", extract_locations(t.children[1]), extract_locations(t.children[2])
        for li in lis:
            for lj in ljs:
                _TA.create_transition(transition=(li, lj), receive_synch=synch, send_synch="")
    elif t.data == "time_cond_simple_tran":
        condition, lis, ljs = t.children[0], extract_locations(t.children[1]), extract_locations(t.children[2])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TA.create_transition(transition=(li, lj), receive_synch="", send_synch="")
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TA.create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "time_cond_synch_tran":
        condition, synch, lis, ljs = t.children[0], t.children[1] + "!", extract_locations(t.children[2]), extract_locations(t.children[3])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TA.create_transition(transition=(li, lj), receive_synch="", send_synch=synch)
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TA.create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "synch_time_cond_simple_tran":
        synch, condition, lis, ljs = t.children[0].children[0] + "?", t.children[1], extract_locations(t.children[2]), extract_locations(t.children[3])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TA.create_transition(transition=(li, lj), receive_synch=synch, send_synch="")
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TA.create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "invrt":
        condition, ls = t.children[0], extract_locations(t.children[1])
        for l in ls:
            while True:
                is_entering, lk, cond = extract_invrnt_condition(condition)
                _TA.create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", lk)] if is_entering else [(lk, "")])
                if len(condition.children) < 4:
                    break
                condition = condition.children[3]

def run_line(line):
    """
    Parses each line and calls run_instruction for each one of them.

    Args:
        line: An input line.
    """
    parse_tree = parser.parse(line)
    for inst in parse_tree.children:
        run_instruction(inst)

def get_descriptions():
    """
    Starts parsing procedure, reads each line from stdin, and call run_line for each one.
    """
    while True:
        line = raw_input()
        line = sub(' +', ' ', sub(r'([^\s\w]|_)+', '', line)).strip().lower()
        if not line:
            break
        try:
            run_line(line)
        except Exception as e:
            print(e)

def init_screen():
    """
    Initializes stdout for the file name and user input.
    """
    global _output_file_name
    print("#################################################################")
    print("########## ATAC: Assisted Timed Automata Construction ##########")
    print("#################################################################")
    print("Enter output file name: ")
    _output_file_name = raw_input()
    print("Below, you can start entering descriptions:")

def main():
    init_screen()
    get_descriptions()
    if _TA:
        _TA.complete_template()
        _TA.write_to_xml(_output_file_name + ".xml")

main()
