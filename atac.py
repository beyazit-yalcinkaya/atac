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
_TAs = {}
_output_file_name = ""
_queries = ""

Grammar = """
    start      : init | tran | invrt | spec
    init       : TEMPLATE_NAME " can only be " LOCATION_NAME                                                        -> single_loc_init
               | TEMPLATE_NAME " can be " locs " and it is initially " LOCATION_NAME                                -> multi_loc_init
    tran       : TEMPLATE_NAME " can go from " locs " to " locs                                                     -> simple_tran
               | TEMPLATE_NAME " can send " SYNCH_NAME " and go from " locs " to " locs                             -> synch_tran
               | "if " sc " then " TEMPLATE_NAME " can go from " locs " to " locs                                   -> synch_cond_simple_tran
               | "if " tc " then " TEMPLATE_NAME " can go from " locs " to " locs                                   -> time_cond_simple_tran
               | "if " tc " then " TEMPLATE_NAME " can send " SYNCH_NAME " and go from " locs " to " locs           -> time_cond_synch_tran
               | "if " sc " and " tc " then " TEMPLATE_NAME " can go from " locs " to " locs                        -> synch_time_cond_simple_tran
    invrt      : "for " TEMPLATE_NAME " " ic " in " locs                                                            -> invrt
    locs       : LOCATION_NAME
               | LOCATION_NAME " " locs
    sc         : SYNCH_NAME " is received"
    tc         : "the time spent after " el " " LOCATION_NAME " is " tconstr
               | "the time spent after " el " " LOCATION_NAME " is " tconstr " and " tc
    ic         : "the time spent after " el " " LOCATION_NAME " cannot be " iconstr
               | "the time spent after " el " " LOCATION_NAME " cannot be " iconstr " and " ic
    tconstr    : "more than " NUMBER                                                                                -> more_than
               | "more than or equal to " NUMBER                                                                    -> more_than_or_equal_to
               | "less than " NUMBER                                                                                -> less_than
               | "less than or equal to " NUMBER                                                                    -> less_than_or_equal_to
               | "equal to " NUMBER                                                                                 -> equal_to
    iconstr    : "more than " NUMBER                                                                                -> more_than
               | "more than or equal to " NUMBER                                                                    -> more_than_or_equal_to
    el         : "entering"                                                                                         -> el_ent
               | "leaving"                                                                                          -> el_lea
    spec       : "for " TEMPLATE_NAME " it " path_frml " be the case that " state_frml                              -> general_spec
               | "for " TEMPLATE_NAME " it shall invariantly be the case that deadlock occurs"                      -> inv_deadlock
               | "for " TEMPLATE_NAME " it shall invariantly be the case that deadlock does not occur"              -> inv_not_deadlock
               | "for " TEMPLATE_NAME " it might possibly be the case that deadlock occurs"                         -> pot_al_deadlock
               | "for " TEMPLATE_NAME " it might possibly be the case that deadlock does not occur"                 -> pot_al_not_deadlock
               | "for " TEMPLATE_NAME " " state_frml " leads to " state_frml                                        -> leads_to
               | "for " TEMPLATE_NAME " " LOCATION_NAME " shall hold within every " NUMBER                          -> special_spec1
               | "for " TEMPLATE_NAME " " LOCATION_NAME " shall be reachable"                                       -> special_spec2
    path_frml  : "shall invariantly"                                                                                -> shall_invariantly
               | "shall eventually"                                                                                 -> shall_eventually
               | "might potentially always"                                                                         -> might_potentially_always
               | "might possibly"                                                                                   -> might_possibly
    state_frml : atom
               | atom " " op " " state_frml
    atom       : "the time spent after " el " " LOCATION_NAME " is " tconstr                                        -> time_spec
               | locs " holds"                                                                                      -> loc_spec
    op         : "and"                                                                                              -> and
               | "or"                                                                                               -> or
               | "implies"                                                                                          -> implies
    %import common.CNAME -> TEMPLATE_NAME
    %import common.CNAME -> SYNCH_NAME
    %import common.CNAME -> LOCATION_NAME
    %import common.NUMBER
"""

parser = Lark(Grammar, parser='earley')

def complete_templates():
    """
    Completes the current TA model.
    """
    global _TAs
    clock_mappings = {}
    for ta in _TAs.keys():
        clock_mappings.update(_TAs[ta].complete_template())
        _TAs[ta].write_to_xml(_output_file_name + ".xml")
    if _queries:
        f = open(_output_file_name + ".q", "w+")
        f.write(_queries)
        f.close()

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
    is_entering = True if t.children[0].data == "el_ent" else False
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
    is_entering = True if t.children[0].children[0].data == "el_ent" else False
    lk = t.children[0].children[1].capitalize()
    cond = ""
    if t.children[1].data == "more_than":
        cond = " <= " + t.children[1].children[0].value
    elif t.children[1].data == "more_than_or_equal_to":
        cond = " < " + t.children[1].children[0].value
    return is_entering, lk, cond

def extract_path_frml(t):
    """
    Extracts path formula.

    Args:
        t: A tree with path formula.
    Returns:
        path formula
    """
    if t.data == "shall_invariantly":
        return "A[]"
    elif t.data == "shall_eventually":
        return "A<>"
    elif t.data == "might_potentially_always":
        return "E[]"
    elif t.data == "might_possibly":
        return "E<>"

def extract_state_frml(t, template_name):
    """
    Extracts state formula.

    Args:
        t: A tree with state formula.
        template_name: Template name.
    Returns:
        state formula
    """
    query = ""
    while True:
        if t.children[0].data == "time_spec":
            is_entering, lk, cond = extract_time_condition(t.children[0])
            c = _TAs[template_name].create_clock(guard_info=(), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")], is_spec_clock=True)
            query += c + cond
        else:
            ls = extract_locations(t.children[0].children[0])
            query += " and ".join(map(lambda x: template_name + "." + x, ls))   
        if len(t.children) < 3:
            break
        if t.children[1].data == "and":
            query += " and "
        elif t.children[1].data == "or":
            query += " or "
        elif t.children[1].data == "implies":
            query += " imply "
        t = t.children[2]
    return query

def run_instruction(t):
    """
    Runs instructions according to the parse tree.

    Args:
        t: Parse tree of a line.
    """
    global _TAs, _current_template_name, _queries
    if t.data == "single_loc_init":
        template_name = t.children[0].value.capitalize()
        initial_location = t.children[1].value.capitalize()
        _TAs[template_name] = objs.Template(template_name, [initial_location], initial_location)
    elif t.data == "multi_loc_init":
        template_name = t.children[0].value.capitalize()
        locations = extract_locations(t.children[1])
        initial_location = t.children[2].value.capitalize()
        locations.remove(initial_location)
        locations = [initial_location] + locations
        _TAs[template_name] = objs.Template(template_name, locations, initial_location)
    elif t.data == "simple_tran":
        template_name = t.children[0].value.capitalize()
        lis, ljs = extract_locations(t.children[1]), extract_locations(t.children[2])
        for li in lis:
            for lj in ljs:
                _TAs[template_name].create_transition(transition=(li, lj), receive_synch="", send_synch="")
    elif t.data == "synch_tran":
        template_name = t.children[0].value.capitalize()
        synch, lis, ljs = t.children[1] + "!", extract_locations(t.children[2]), extract_locations(t.children[3])
        for li in lis:
            for lj in ljs:
                _TAs[template_name].create_transition(transition=(li, lj), receive_synch="", send_synch=synch)
    elif t.data == "synch_cond_simple_tran":
        template_name = t.children[1].value.capitalize()
        synch, lis, ljs = t.children[0].children[0] + "?", extract_locations(t.children[2]), extract_locations(t.children[3])
        for li in lis:
            for lj in ljs:
                _TAs[template_name].create_transition(transition=(li, lj), receive_synch=synch, send_synch="")
    elif t.data == "time_cond_simple_tran":
        template_name = t.children[1].value.capitalize()
        condition, lis, ljs = t.children[0], extract_locations(t.children[2]), extract_locations(t.children[3])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TAs[template_name].create_transition(transition=(li, lj), receive_synch="", send_synch="")
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TAs[template_name].create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "time_cond_synch_tran":
        template_name = t.children[1].value.capitalize()
        condition, synch, lis, ljs = t.children[0], t.children[2] + "!", extract_locations(t.children[3]), extract_locations(t.children[4])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TAs[template_name].create_transition(transition=(li, lj), receive_synch="", send_synch=synch)
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TAs[template_name].create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "synch_time_cond_simple_tran":
        template_name = t.children[2].value.capitalize()
        synch, condition, lis, ljs = t.children[0].children[0] + "?", t.children[1], extract_locations(t.children[3]), extract_locations(t.children[4])
        created_transitions = []
        for li in lis:
            for lj in ljs:
                created_transitions += _TAs[template_name].create_transition(transition=(li, lj), receive_synch=synch, send_synch="")
        while True:
            is_entering, lk, cond = extract_time_condition(condition)
            for created_transition in created_transitions:
                _TAs[template_name].create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
            if len(condition.children) < 4:
                break
            condition = condition.children[3]
    elif t.data == "invrt":
        template_name = t.children[0].value.capitalize()
        condition, ls = t.children[1], extract_locations(t.children[2])
        for l in ls:
            while True:
                is_entering, lk, cond = extract_invrnt_condition(condition)
                _TAs[template_name].create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", lk)] if is_entering else [(lk, "")])
                if len(condition.children) < 4:
                    break
                condition = condition.children[3]
    elif t.data == "general_spec":
        template_name = t.children[0].value.capitalize()
        path_frml = extract_path_frml(t.children[1])
        state_frml = extract_state_frml(t.children[2], template_name)
        _queries += path_frml + " " + state_frml + "\n"
    elif t.data == "inv_deadlock":
        _queries += "A[] deadlock\n"
    elif t.data == "inv_not_deadlock":
        _queries += "A[] not deadlock\n"
    elif t.data == "pot_al_deadlock":
        _queries += "E<> deadlock\n"
    elif t.data == "pot_al_not_deadlock":
        _queries += "E<> not deadlock\n"
    elif t.data == "leads_to":
        template_name = t.children[0].value.capitalize()
        state_frml1 = extract_state_frml(t.children[1], template_name)
        state_frml2 = extract_state_frml(t.children[2], template_name)
        _queries += state_frml1 + " --> " + state_frml2 + "\n"
    elif t.data == "special_spec1":
        template_name = t.children[0].value.capitalize()
        l = t.children[1].value.capitalize()
        n = t.children[2].value
        c = _TAs[template_name].create_clock(guard_info=(), invariant_info=(), assignment_info=[(l, "")], is_spec_clock=True)
        _queries += "A[] not " + template_name + "." + l + " or " + c + " <= " + n + "\n"
    elif t.data == "special_spec2":
        template_name = t.children[0].value.capitalize()
        l = t.children[1].value.capitalize()
        _queries += "E<> " + template_name + "." + l + "\n"

def run_line(line):
    """
    Parses each line and calls run_instruction for each one of them.

    Args:
        line: An input line.
    """
    parse_tree = parser.parse(line)
    for inst in parse_tree.children:
        run_instruction(inst)

def get_lines():
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
    print("########## ATAC: Assisted Timed Automata Construction ###########")
    print("#################################################################")
    print("Enter output file name: ")
    _output_file_name = raw_input()
    print("Below, you can start entering descriptions and specifications:")

def main():
    init_screen()
    get_lines()
    complete_templates()

main()
