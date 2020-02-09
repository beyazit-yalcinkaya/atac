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
_output_file_name = ""
_q_file_content = ""

Grammar = """
    start      : "it " path_frml " be the case that " state_frml -> general
               | path_frml " leads to " path_frml -> leads_to
               | "it shall go to " LOCATION_NAME " in every " NUMBER -> special_1
               | LOCATION_NAME " shall be reachable from " LOCATION_NAME -> special_2
               | LOCATION_NAME " shall be reachable from " LOCATION_NAME " within " NUMBER -> special_3
    path_frml  : "shall always" -> shall_always
               | "shall eventually" -> shall_eventually
               | "might always" -> might_always
               | "might eventually" -> might_eventually
    state_frml : "deadlock occurs"
               | tc
               | LOCATION_NAME " holds"
               | "not " state_frml
               | state_frml " and " state_frml
               | state_frml " or " state_frml
    tc         : "the time spent after " sel " " LOCATION_NAME " is " constr
               | "the time spent after " sel " " LOCATION_NAME " is " constr " and " tc
    constr     : "more than " NUMBER                                                       -> more_than
               | "more than or equal to " NUMBER                                           -> more_than_or_equal_to
               | "less than " NUMBER                                                       -> less_than
               | "less than or equal to " NUMBER                                           -> less_than_or_equal_to
               | "equal to " NUMBER                                                        -> equal_to
    sel        : "entering"                                                                -> sel_ent
               | "leaving"                                                                 -> sel_lea
    %import common.CNAME -> TEMPLATE_NAME
    %import common.CNAME -> SYNCH_NAME
    %import common.CNAME -> LOCATION_NAME
    %import common.NUMBER
"""

parser = Lark(Grammar, parser='earley')

def add_query(query):
    """
    Creates a file named same as the template name with
    .q extension containing given query content.

    Args:
        query: Given query.
    """
    global _current_template_name, _q_file_content
    if _q_file_content == "":
        _q_file_content = query + "\n"
    else:
        _q_file_content += query + "\n"

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

def run_instruction(t):
    """
    Runs instructions according to the parse tree.

    Args:
        t: Parse tree of a line.
    """
    global _TA, _current_template_name
    if t.data == "general":
        path_frml = t.children[0]
        print path_frml
    elif t.data == "leads_to":
        pass

def run_line(line):
    """
    Parses each line and calls run_instruction for each one of them.

    Args:
        line: An input line.
    """
    parse_tree = parser.parse(line)
    for inst in parse_tree.children:
        run_instruction(inst)

def get_specifications():
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
    print("Below, you can start entering specifications:")

def main():
    init_screen()
    get_specifications()
    if _q_file_content:
        f = open(_output_file_name + ".q", "w+")
        f.write(_q_file_content)
        f.close()

main()
