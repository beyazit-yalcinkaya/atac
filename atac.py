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
    start        : init | tran | invrt | spec
    init         : CNAME " can only be " CNAME                                                 -> single_loc_init
                 | CNAME " can be " locs " and it is initially " CNAME                         -> multi_loc_init
    tran         : CNAME " can go from " locs " to " locs                                      -> simple_tran
                 | CNAME " can send " CNAME " and go from " locs " to " locs                   -> synch_tran
                 | "if " sc " then " CNAME " can go from " locs " to " locs                    -> synch_cond_simple_tran
                 | "if " tc " then " CNAME " can go from " locs " to " locs                    -> time_cond_simple_tran
                 | "if " tc " then " CNAME " can send " CNAME " and go from " locs " to " locs -> time_cond_synch_tran
                 | "if " sc " and " tc " then " CNAME " can go from " locs " to " locs         -> synch_time_cond_simple_tran
    invrt        : "for " CNAME " " ic " in " locs                                             -> invrt1
                 | "for " CNAME " the time spent in " locs " cannot be " iconstr               -> invrt2
    locs         : CNAME
                 | CNAME " " locs
    sc           : CNAME " is received"
    tc           : "the time spent after " el " " CNAME " is " tconstr
                 | "the time spent after " el " " CNAME " is " tconstr " and " tc
    ic           : "the time spent after " el " " CNAME " cannot be " iconstr
                 | "the time spent after " el " " CNAME " cannot be " iconstr " and " ic
    tconstr      : "more than " NUMBER                                                         -> more_than
                 | "more than or equal to " NUMBER                                             -> more_than_or_equal_to
                 | "less than " NUMBER                                                         -> less_than
                 | "less than or equal to " NUMBER                                             -> less_than_or_equal_to
                 | "equal to " NUMBER                                                          -> equal_to
    iconstr      : "more than " NUMBER                                                         -> more_than
                 | "more than or equal to " NUMBER                                             -> more_than_or_equal_to
    el           : "entering"                                                                  -> el_ent
                 | "leaving"                                                                   -> el_lea
    spec         : "it " path_frml " be the case that " state_frml                             -> general_spec
                 | "deadlock never occurs"                                                     -> al_not_deadlock
                 | state_frml " leads to " state_frml                                          -> leads_to
                 | "for " CNAME " " CNAME " shall hold within every " NUMBER                   -> special_spec1
    path_frml    : "shall always"                                                              -> shall_always
                 | "shall eventually"                                                          -> shall_eventually
                 | "might always"                                                              -> might_always
                 | "might eventually"                                                          -> might_eventually
    state_frml.1 : "for " CNAME " " atom
                 | "for " CNAME " " atom " " op " " state_frml
    atom.2       : "the time spent after " el " " CNAME " is " tconstr                         -> time_spec
                 | locs " does not hold"                                                       -> not_loc_spec
                 | locs " holds"                                                               -> loc_spec
    op           : "and"                                                                       -> and
                 | "or"                                                                        -> or
                 | "implies"                                                                   -> implies
    %import common.CNAME
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
    objs.write_to_xml(_output_file_name + ".xml")
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
    is_entering = True if t.children[0].data == "el_ent" else False
    lk = t.children[1].capitalize()
    cond = ""
    if t.children[2].data == "more_than":
        cond = " <= " + t.children[2].children[0].value
    elif t.children[2].data == "more_than_or_equal_to":
        cond = " < " + t.children[2].children[0].value
    return is_entering, lk, cond

def extract_path_frml(t):
    """
    Extracts path formula.

    Args:
        t: A tree with path formula.
    Returns:
        path formula
    """
    if t.data == "shall_always":
        return "A[]"
    elif t.data == "shall_eventually":
        return "A<>"
    elif t.data == "might_always":
        return "E[]"
    elif t.data == "might_eventually":
        return "E<>"

def extract_state_frml(t):
    """
    Extracts state formula.

    Args:
        t: A tree with state formula.
    Returns:
        state formula
    """
    query = ""
    while True:
        template_name = t.children[0].value.capitalize()
        if t.children[1].data == "time_spec":
            is_entering, lk, cond = extract_time_condition(t.children[1])
            c = _TAs[template_name].create_clock(guard_info=(), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")], is_spec_clock=True)
            query += c + cond
        elif t.children[1].data == "loc_spec":
            ls = extract_locations(t.children[1].children[0])
            query += " and ".join(map(lambda x: template_name + "." + x, ls))
        elif t.children[1].data == "not_loc_spec":
            ls = extract_locations(t.children[1].children[0])
            query += " and ".join(map(lambda x: "not " + template_name + "." + x, ls))
        if len(t.children) < 4:
            break
        if t.children[2].data == "and":
            query += " and "
        elif t.children[2].data == "or":
            query += " or "
        elif t.children[2].data == "implies":
            query += " imply "
        t = t.children[3]
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
    elif t.data == "invrt1":
        template_name, condition, ls = t.children[0].value.capitalize(), t.children[1], extract_locations(t.children[2])
        for l in ls:
            while True:
                is_entering, lk, cond = extract_invrnt_condition(condition)
                _TAs[template_name].create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", lk)] if is_entering else [(lk, "")])
                if len(condition.children) < 4:
                    break
                condition = condition.children[3]
    elif t.data == "invrt2":
        template_name = t.children[0].value.capitalize()
        ls = extract_locations(t.children[1])
        cond = ""
        if t.children[2].data == "more_than":
            cond += " <= " + t.children[2].children[0]
        elif t.children[2].data == "more_than_or_equal_to":
            cond += " < " + t.children[2].children[0]
        for l in ls:
            _TAs[template_name].create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", l)])
    elif t.data == "general_spec":
        path_frml = extract_path_frml(t.children[0])
        state_frml = extract_state_frml(t.children[1])
        _queries += path_frml + " " + state_frml + "\n"
    elif t.data == "al_not_deadlock":
        _queries += "A[] not deadlock\n"
    elif t.data == "leads_to":
        state_frml1 = extract_state_frml(t.children[0])
        state_frml2 = extract_state_frml(t.children[1])
        _queries += state_frml1 + " --> " + state_frml2 + "\n"
    elif t.data == "special_spec1":
        template_name = t.children[0].value.capitalize()
        l = t.children[1].value.capitalize()
        n = t.children[2].value
        c = _TAs[template_name].create_clock(guard_info=(), invariant_info=(), assignment_info=[(l, "")], is_spec_clock=True)
        _queries += "A[] not " + template_name + "." + l + " or " + c + " <= " + n + "\n"

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
            print e

def init_screen():
    """
    Initializes stdout for the file name and user input.
    """
    global _output_file_name
    print "#################################################################"
    print "########## ATAC: Automated Timed Automata Construction ##########"
    print "#################################################################"
    print "Enter output file name: "
    _output_file_name = raw_input()
    print "Below, you can start entering descriptions and specifications:"

init_screen()
get_lines()
complete_templates()

