"""
   Written by Beyazit Yalcinkaya as a part of the
   Automating Timed Automata Design Project conducted
   by the METU Cyber-Physical Systems Research Group.
"""

from lark import Lark
from re import sub
from sys import exit
import objects as objs
import tkinter as tk
from PIL import Image, ImageTk
import subprocess as sp

"""
Internal global variables.
"""
_TA = None
_current_template_names = []
_queries = {}
_q_file_content = ""
_output_file_name = "temp"
_display_root = None
_display_images = []

Grammar = """
   start   : init | sys | spec
   init    : TEMPLATE_NAME " can only be " LOCATION_NAME                                            -> single_loc_init
           | TEMPLATE_NAME " can be " locs " and it is initially " LOCATION_NAME                    -> multi_loc_init
   sys     : tran                                                                                   -> transition
           | "if " cond " then " tran                                                               -> conditional_transition
   spec    : "it goes to " LOCATION_NAME " in every " NUMBER                                        -> spec1
           | "the time spent in " LOCATION_NAME " cannot be more than " NUMBER                      -> spec2
           | "the time spent in " LOCATION_NAME " cannot be more than or equal to " NUMBER          -> spec3
           | LOCATION_NAME " must be reached from " LOCATION_NAME                                   -> spec4
           | LOCATION_NAME " must be reached from " LOCATION_NAME " within " NUMBER                 -> spec5
   locs    : LOCATION_NAME
           | LOCATION_NAME " " locs                                                                 -> locations
   tran    : "it can go to " locs " from " locs                                                     -> direct_transition
           | "it can send " SYNCH_NAME " and go to " locs " from " locs                             -> transition_with_synch
   cond    : tcond                                                                                  -> only_time_condition
           | scond                                                                                  -> only_synch_condition
           | scond " and " tcond                                                                    -> synch_and_time_condition
   scond   : "it receives " SYNCH_NAME                                                              -> synch_condition
   tcond   : "the time spent after " el " " LOCATION_NAME " is " constr
           | "the time spent after " el " " LOCATION_NAME " is " constr " and " tcond
   constr  : "more than " NUMBER                                                                    -> more_than
           | "more than or equal to " NUMBER                                                        -> more_than_or_equal_to
           | "less than " NUMBER                                                                    -> less_than
           | "less than or equal to " NUMBER                                                        -> less_than_or_equal_to
           | "equal to " NUMBER                                                                     -> equal_to
   el      : "entering"                                                                             -> entering
           | "leaving"                                                                              -> leaving
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
   global _current_template_names, _q_file_content
   if _q_file_content == "":
       _q_file_content = query + "\n"
   else:
       _q_file_content += query + "\n"

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
   is_entering = True if t.children[0].data == "entering" else False
   lk = t.children[1].value.capitalize()
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

def extract_transition(t):
   """
   Extracts transition info from the given tree.

   Args:
       t: A tree with transition info.
   Returns:
       lis: List of locations from which outgoing transition will be created.
       ljs: List of locations to which incoming transition will be created.
       synch: Synch signal to be sent.
   """
   lis = []
   ljs = []
   synch = ""
   if t.data == "direct_transition":
       lis = extract_locations(t.children[1])
       ljs = extract_locations(t.children[0])
   elif t.data == "transition_with_synch":
       synch = t.children[0].value + '!'
       lis = extract_locations(t.children[2])
       ljs = extract_locations(t.children[1])
   return lis, ljs, synch

def complete_template():
   """
   Completes the current TA model.
   """
   global _queries
   clock_mapping = _TA.complete_template()
   for c in _queries.keys():
       for c_n in clock_mapping[c]:
           add_query(_queries[c].replace('x', c_n))
   del _queries
   _queries = {}
   #Export each template to template name . png
   ## TODO ##
   #sp.call("java -jar uppaal/uppaal.jar --exportToEPS " + _current_template_name + " " + _output_file_name + ".xml", shell=True)
   #sp.call("echo " + _current_template_name + ".eps | xargs -n1 pstopdf", shell=True)
   #sp.call("sips -s format png " + _current_template_name + ".pdf --out " + _current_template_name + ".png", shell=True)
   #_display_root.photo.append(ImageTk.PhotoImage(Image.open(_current_template_name + ".png")))
   #_display_images.append(tk.Label(_display_root,image=_display_root.photo[-1]))
   #_display_images[-1].pack(side=tk.LEFT)

def run_instruction(t):
   """
   Runs instructions according to the parse tree.

   Args:
       t: Parse tree of a line.
   """
   global _TA, _current_template_names
   if t.data == "single_loc_init":
       if _TA:
           complete_template()
       _current_template_names.append(t.children[0].value.capitalize())
       initial_location = t.children[1].value.capitalize()
       _TA = objs.Template(_current_template_names[-1], [initial_location], initial_location)
   elif t.data == "multi_loc_init":
       if _TA:
           complete_template()
       _current_template_names.append(t.children[0].value.capitalize())
       locations = extract_locations(t.children[1])
       initial_location = t.children[2].value.capitalize()
       locations.remove(initial_location)
       locations = [initial_location] + locations
       _TA = objs.Template(_current_template_names[-1], locations, initial_location)
   elif t.data == "transition":
       t = t.children[0]
       lis, ljs, synch = extract_transition(t)
       for li in lis:
           for lj in ljs:
               _TA.create_transition(transition=(li, lj), receive_synch="", send_synch=synch);
   elif t.data == "conditional_transition":
       condition = t.children[0]
       transition = t.children[1]
       lis, ljs, send_synch = extract_transition(transition)
       created_transitions = []
       receive_synch = condition.children[0].children[0].value + "?" if condition.data == "only_synch_condition" or condition.data == "synch_and_time_condition" else ""
       for li in lis:
           for lj in ljs:
               created_transitions += _TA.create_transition(transition=(li, lj), receive_synch=receive_synch, send_synch=send_synch);

       if condition.data == "only_time_condition":
           condition = condition.children[0]
           while True:
               is_entering, lk, cond = extract_time_condition(condition)
               for created_transition in created_transitions:
                   _TA.create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
               if len(condition.children) < 4:
                   break
               condition = condition.children[3]
       elif condition.data == "only_synch_condition":
           pass
       elif condition.data == "synch_and_time_condition":
           condition = condition.children[1]
           while True:
               is_entering, lk, cond = extract_time_condition(condition)
               for created_transition in created_transitions:
                   _TA.create_clock(guard_info=(created_transition, cond), invariant_info=(), assignment_info=[("", lk)] if is_entering else [(lk, "")])
               if len(condition.children) < 4:
                   break
               condition = condition.children[3]
       else:
           print "ERROR", condition
   elif t.data == "spec1":#A[] !(!x.a and x_0 > 4) In all states it is not the case that TA is not in a and x_0 is more than 4. It goes to A in every 4.
       l = t.children[0].value.capitalize()
       cond = " <= " + t.children[1].value
       locs = filter(lambda x: x != l, _TA.get_locations())
       for lp in locs:
           if _TA.all_simple_paths(l, lp) != []:
               if _TA.all_simple_paths(lp, l) == []:
                   _TA.create_transition(transition=(lp, l), receive_synch="", send_synch="")
       clock_name = _TA.create_clock(guard_info=(), invariant_info=(locs, cond), assignment_info=[(l, "")])
       _queries[clock_name] = "A[]!(!" + _current_template_names[-1] + "." + l + " and x > " + t.children[1].value + ")"
   elif t.data == "spec2":#A[] !(x.a and x_0 > 4). The time spent in A cannot be more than 4.
       l = t.children[0].value.capitalize()
       cond = " <= " + t.children[1].value
       clock_name = _TA.create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", l)])
       _queries[clock_name] = "A[]!(" + _current_template_names[-1] + "." + l + " and x > " + t.children[1].value + ")"
   elif t.data == "spec3":#A[] !(x.a and x_0 >= 4). The time spent in A cannot be more than 4.
       l = t.children[0].value.capitalize()
       cond = " < " + t.children[1].value
       clock_name = _TA.create_clock(guard_info=(), invariant_info=([l], cond), assignment_info=[("", l)])
       _queries[clock_name] = "A[]!(" + _current_template_names[-1] + "." + l + " and x >= " + t.children[1].value + ")"
   elif t.data == "spec4":#x.a --> x.b, i.e., A[](x.a imply A<> x.b). B must be reached from A.
       li = t.children[1].capitalize()
       lj = t.children[0].capitalize()
       if _TA.all_simple_paths(li, lj) == []:
           _TA.create_transition(transition=(li, lj), receive_synch="", send_synch="")
       add_query(_current_template_names[-1] + "." + li + " --> " + _current_template_names[-1] + "." + lj)
   elif t.data == "spec5":#x.a --> (x.b and x_0 <= 4), i.e., A[](x.a imply A<> (x.b and x_0 <= 4)). B must be reached from A within 4.
       li = t.children[1].capitalize()
       lj = t.children[0].capitalize()
       clock_name = _TA.create_clock(guard_info=(), invariant_info=([li], cond), assignment_info=[("",lj)])
       if _TA.all_simple_paths(li, lj) == []:
           _TA.create_transition(transition=(li, lj), receive_synch="", send_synch="")
       _queries[clock_name] = _current_template_names[-1] + "." + li + " --> (" + _current_template_names[-1] + "." + lj + " and x <= " + t.children[2].value + ")"

def run_line(line):
   """
   Parses each line and calls run_instruction for each one of them.

   Args:
       line: An input line.
   """
   parse_tree = parser.parse(line)
   for inst in parse_tree.children:
       run_instruction(inst)

def init():
   global _TA, _current_template_names, _queries, _q_file_content, _output_file_name, _root, _display_root
   _TA = None
   _current_template_names = []
   _queries = {}
   _q_file_content = ""
   _output_file_name = "temp"

def main():
   global _display_root, _display_images
   def run():
       init()
       input_text = text_box.get("1.0","end-1c").split("\n")
       input_text = filter(lambda x: x, input_text)
       input_text = map(lambda x: str(x), input_text)
       for line in input_text:
           line = sub(' +', ' ', sub(r'([^\s\w]|_)+', '', line)).strip().lower()
           try:
               run_line(line)
           except Exception as e:
               print(e)
       if _TA:
           complete_template()
           _TA.write_to_xml(_output_file_name + ".xml")
           for i in _current_template_names:
               sp.call("rm -rf " + i + ".eps; rm -rf " + i + ".pdf; rm -rf " + i + ".png", shell=True)
               sp.call("java -jar uppaal/uppaal.jar --exportToEPS " + i + " " + _output_file_name + ".xml", shell=True)
               sp.call("echo " + i + ".eps | xargs -n1 pstopdf", shell=True)
               sp.call("sips -s format png " + i + ".pdf --out " + i + ".png", shell=True)
               sp.call("rm -rf " + i + ".eps; rm -rf " + i + ".pdf", shell=True)
               _display_root.photo.append(ImageTk.PhotoImage(Image.open(i + ".png")))
               _display_images.append(tk.Label(_display_root,image=_display_root.photo[-1]))
               _display_images[-1].pack(side=tk.LEFT)
       if _q_file_content:
           f = open(_output_file_name + ".q", "w+")
           f.write(_q_file_content)
           f.close()
   def reset():
       init()
       text_box.delete('1.0', tk.END)
       _display_root.photo = []
       for i in _display_images:
           i.pack_forget()
   _display_root = tk.Tk()
   _display_root.title("ATAC: Automated Timed Automata Construction")
   _display_root.photo = []
   text_box = tk.Text(_display_root, height=20, width=50, borderwidth=2, relief="groove", font=("Helvetica", 24))
   text_box.pack(side=tk.LEFT)
   button_commit=tk.Button(_display_root, height=1, width=10, text="Generate", command=run)
   button_commit.pack(side=tk.LEFT)
   button_reset=tk.Button(_display_root, height=1, width=10, text="Reset", command=reset)
   button_reset.pack(side=tk.LEFT)
   tk.mainloop()

main()

