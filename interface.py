"""
    Written by Beyazit Yalcinkaya as a part of the
    Automating Timed Automata Design Project conducted
    by the METU Cyber-Physical Systems Research Group.
"""

import pyuppaal
import sys

"""
Internal global variables.
Current template is manipulated by the functions and when is finished it is added to the nta.
"""
_nta = None
_templates = {}

def initialize(template_name):
    """
    Initializes internal global variables.
    This function must be called before any other function.
    """
    global _nta
    if not _nta:
	    _nta = pyuppaal.NTA()
    return


def create_template(template_name, list_of_locations): # while proccessing input make initial location the first element
    """
    Creates a new template with given name and locations.

    Args:
        template_name: Name of the template.
        list_of_locations: List of location in the template.
    """
    global _nta
    n = len(list_of_locations)
    temp = [pyuppaal.Location(name=list_of_locations[i]) for i in range(0, n)]
    _templates[template_name] = pyuppaal.Template(name=pyuppaal.Label("name", template_name), locations=temp, initlocation=temp[0])
    _templates[template_name].assign_ids()
    return


def add_current_template_to_nta(template_name):
    """
    Adds current_template the the nta object.
    """
    global _nta
    try:
        assert _templates[template_name] != None
        _nta.add_template(_templates[template_name])
        if _nta.system:
            _nta.system += ", " + _templates[template_name].name.value
        else:
            _nta.system = "system " + _templates[template_name].name.value
        _templates[template_name] = None
    except AssertionError:
        pass
    return


def add_invariant(template_name, location_name, clock_name, list_of_invariants):
    """
    Adds an invariant to current_template.

    Args:
        location_name: Location Name.
        clock_name: Clock name.
        list_of_invariants: List of condition-number pairs elements.
    """
    global _nta
    temp = _templates[template_name].get_location_by_name(location_name)
    invariant_string = clock_name + list_of_invariants
    if clock_name != "" and " " + clock_name + ";" not in _nta.declaration:
        _nta.declaration += "clock " + clock_name + ";\n"
    if temp.invariant.value:
        temp.invariant.value += " && " + invariant_string
    else:
        temp.invariant.value = invariant_string
    return


def create_transition(template_name, source, target, synch=""):
    """
    Creates a new transition from given source
    to given target with given synchronisation.

    Args:
        source: Source location.
        target: Target location.
        synch: Synchronisation name.

    Returns:
        Index o the created transition in the
        current_template's transitions list.
    """
    global _nta
    if synch and " " + synch[:-1] + ";" not in _nta.declaration:
        _nta.declaration += "chan " + synch[:-1] + ";\n"
    _templates[template_name].transitions.append(pyuppaal.Transition(source=_templates[template_name].get_location_by_name(source),
                                                             target=_templates[template_name].get_location_by_name(target),
                                                             synchronisation=synch))
    return len(_templates[template_name].transitions) - 1


def add_guard(template_name, transition_id, clock_name, list_of_guards):
    """
    Adds a guard to the current_template.

    Args:
        transition_id: Transition id of the transition
                       on which the guard expression will
                       be inserted. It is the index of the
                       transition in the current_template's
                       transitions list.
        clock_name: Clock name.
        list_of_guards: List of condition-number pairs elements.
    """
    global _nta
    guard_string = [clock_name + i for i in list_of_guards]
    guard_string = " && ".join(guard_string)
    if clock_name != "" and " " + clock_name + ";" not in _nta.declaration:
        _nta.declaration += "clock " + clock_name + ";\n"
    if transition_id != -1:
	    if _templates[template_name].transitions[transition_id].guard.value:
	        _templates[template_name].transitions[transition_id].guard.value += " && " + guard_string
	    else:
	        _templates[template_name].transitions[transition_id].guard.value = guard_string


def add_assignment(template_name, transition_id, clock_name):
    """
    Adds a assignment to the current_template.

    Args:
        transition_id: Transition id of the transition
                       on which the assignment will
                       be inserted. It is the index of the
                       transition in the current_template's
                       transitions list.
        clock_name: Clock name.
    """
    global _nta
    assignment_string = clock_name + " = 0"
    if clock_name != "" and " " + clock_name + ";" not in _nta.declaration:
        _nta.declaration += "clock " + clock_name + ";\n"
    if transition_id != -1:
	    if _templates[template_name].transitions[transition_id].assignment.value:
	        _templates[template_name].transitions[transition_id].assignment.value += ", " + assignment_string
	    else:
	        _templates[template_name].transitions[transition_id].assignment.value = assignment_string


def complete(output_file_name):
    """
    Completes the model. Writes model to the xml file with given name.

    Args:
        output_file_name: Name of the output xml file.
    """
    global _nta
    _nta.system += ";\n"
    map(lambda x: x.layout(), _nta.templates)
    xml_file = open(output_file_name, "w")
    xml_file.write(_nta.to_xml())
    xml_file.close()

def create_committed_location(template_name, name):
    """
    Creates a commited location and adds to the location list.
    """
    committed_location = pyuppaal.Location(committed=True, name=name)
    _templates[template_name].locations.append(committed_location)


