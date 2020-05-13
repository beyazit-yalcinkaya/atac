"""
    Written by Beyazit Yalcinkaya as a part of the
    Automating Timed Automata Design Project conducted
    by the METU Cyber-Physical Systems Research Group.
"""

import sys
import interface
import networkx as nx

def write_to_xml(output_file_name):
    """
    Writes all TA template to the given xml file in xml format.

    Args:
        output_file_name: Name of the xml file.
    """
    interface.complete(output_file_name)

class Template(object):
    """
    TA template that is described by the input.
    """
    def __init__(self, name, locations, initial_location, ta=nx.MultiDiGraph(), clocks=[], clock_count=0): # locations[0] is the initial location.
        """
        Initializes the object. Initially only name, locations, and initial location must be provided.

        Args:
            name: String. It is name of the template.
            locations: List of strings. Names of all locations.
            ta: Multi digraph represented with networkx's MultiDiGraph. It is the graphical structure of the TA template.
            clocks: List of clock objects. Clocks used in the TA.
            clock_count: Integer. Number of clocks.
        """
        interface.initialize(name)  
        interface.create_template(name, locations)
        self.name = name
        self.locations = locations + ["LOCATION_ZERO"]
        self.ta = ta
        self.ta.add_nodes_from(locations)
        self.clocks = clocks if clocks else []
        self.clock_count = clock_count
        self.initial_location = initial_location
        self.committed_location_count = 0
        self.ta.add_edge("LOCATION_ZERO", initial_location, -1)

    def get_locations(self):
        """
        Returns:
            List of locations.
        """
        return self.locations
        #return list(self.ta.nodes())

    def get_transitions(self):
        """
        Returns:
            List of transitions.
        """
        return list(self.ta.edges(keys=True))

    def create_transition(self, transition, receive_synch="", send_synch=""):
        """
        Creates given transition.
        If source == "", then create transition from all l to target.
        If target == "", then create transition from source to all l.
        If both receive_synch and send_synch are given, then creates
        an intermediate committed location. Constraints on clocks and
        receive_synch are added to the transition between given source
        and the committed location and receive_synch is added to the
        transition between committed location and given target.

        Args:
            transition: Pair s.t. (source, target).
            receive_synch: synch signal to receive with "?".
            send_synch: synch signal to send with "!".
        Returns:
            transition_list: List of created transitions.
        """
        transition_list = []
        if receive_synch and send_synch:
            committed_location = self.create_committed_location()
            if transition[0] and transition[1]:
                t_id1 = interface.create_transition(self.name, transition[0], committed_location, receive_synch)
                t_id2 = interface.create_transition(self.name, committed_location, transition[1], send_synch)
                self.ta.add_edge(transition[0], committed_location, t_id1)
                self.ta.add_edge(committed_location, transition[1], t_id2)
                transition_list.append((transition[0], committed_location, t_id1))
                transition_list.append((committed_location, transition[1], t_id2))
            elif transition[0]:
                for l in self.locations:
                    t_id1 = interface.create_transition(self.name, transition[0], committed_location, receive_synch)
                    t_id2 = interface.create_transition(self.name, committed_location, l, send_synch)
                    self.ta.add_edge(transition[0], committed_location, t_id1)
                    self.ta.add_edge(committed_location, l, t_id2)
                    transition_list.append((transition[0], committed_location, t_id1))
                    transition_list.append((committed_location, l, t_id2))
            elif transition[1]:
                for l in self.locations:
                    t_id1 = interface.create_transition(self.name, committed_location, transition[1], receive_synch)
                    t_id2 = interface.create_transition(self.name, l, committed_location, send_synch)
                    self.ta.add_edge(l, committed_location, t_id1)
                    self.ta.add_edge(committed_location, transition[1], t_id2)
                    transition_list.append((l, committed_location, t_id1))
                    transition_list.append((committed_location, transition[1], t_id2))
            else:
                for l_s in self.locations:
                    for l_t in self.locations:
                        t_id1 = interface.create_transition(self.name, l_s, committed_location, receive_synch)
                        t_id2 = interface.create_transition(self.name, committed_location, l_t, send_synch)
                        self.ta.add_edge(l_s, committed_location, t_id1)
                        self.ta.add_edge(committed_location, l_t, t_id2)
                        transition_list.append((l_s, committed_location, t_id1))
                        transition_list.append((committed_location, l_t, t_id2))
        else:
            if transition[0] and transition[1]:
                t_id = interface.create_transition(self.name, transition[0], transition[1], receive_synch if receive_synch else send_synch)
                self.ta.add_edge(transition[0], transition[1], t_id)
                transition_list.append((transition[0], transition[1], t_id))
            elif transition[0]:
                for l in self.locations:
                    t_id = interface.create_transition(self.name, transition[0], l, receive_synch if receive_synch else send_synch)
                    self.ta.add_edge(transition[0], l, t_id)
                    transition_list.append((transition[0], l, t_id))
            elif transition[1]:
                for l in self.locations:
                    t_id = interface.create_transition(self.name, l, transition[1], receive_synch if receive_synch else send_synch)
                    self.ta.add_edge(l, transition[1], t_id)
                    transition_list.append((l, transition[1], t_id))
            else:
                for l_s in self.locations:
                    for l_t in self.locations:
                        t_id = interface.create_transition(self.name, l_s, l_t, receive_synch if receive_synch else send_synch)
                        self.ta.add_edge(l_s, l_t, t_id)
                        transition_list.append((l_s, l_t, t_id))
        return transition_list

    def find_transitions(self, transition):
        """
        Finds corresponding transitions for given source
        target pair amoung created transitions.

        Args:
            transition: (source location, target location)

        Ret:
            result: Matching list of transitions.
        """
        transitions = self.get_transitions()
        result = []
        if transition[0] and transition[1]:
            for t in transitions:
                if transition[0] == t[0] and transition[1] == t[1]:
                    result.append(t)
                elif transition[0] == t[0] and "C" in t[1]:
                    for tt in transitions:
                        if t[1] == tt[0] and transition[1] == tt[1]:
                            result.append(t)
        elif transition[0]:
            result = filter(lambda x: x[0] == transition[0], transitions)
        elif transition[1]:
            for t in transitions:
                if "C" not in t[0] and transition[1] == t[1]:
                    result.append(t)
        else:
            result = filter(lambda x: "C" not in x[0], transitions)
        return result

    def create_clock(self, guard_info=(), invariant_info=(), assignment_info=[], is_spec_clock=False):
        """
        Creates a new clock with given guard, invariant, and assignment info.

        Args:
            guard_info: ((source, target, t_id), " < c").
                        First element of the pair is the transitions on which the given
                        guard on the clocks will appear as a guard and the second element
                        of the pair is the constraint string.
            invariant_info: ([l1, ...], " > c").
                            First element of the pair is the location in which the given
                            invariant will appear and the second element is the constraint string.                           
            assignment_info: [(source, target)].
                             Transition on which the created clock will be reset.
        """
        clock = Clock(name=self.get_clock_name(), is_spec_clock=is_spec_clock)
        assignment_info.append(("LOCATION_ZERO", self.initial_location))
        if guard_info:
            clock.add_guard(guard_info[0], guard_info[1])
        if invariant_info:
            for l in invariant_info[0]:
                clock.add_invariant(l, invariant_info[1])
        for t in assignment_info:
            clock.add_assignment(t)
        self.add_clock(clock)
        return clock.name

    def add_clock(self, clock_obj):
        """
        Adds given clock objecy to the list of clocks.

        Args:
            clock_obj: The clock object that will be added to the list of clocks.
        """
        if clock_obj not in self.clocks:
            self.clocks.append(clock_obj)

    def finalize_transitions(self):
        """
        Maps abstract transitions of assignments to real transitions.
        """
        for c in self.clocks:
            new_assignment_list = []
            for tt in c.assignments:
                transitions = self.find_transitions(tt)
                for t in transitions:
                    new_assignment_list.append(t)
            del c.assignments
            c.assignments = new_assignment_list

    def complete_template(self):
        """
        Runs the clock reduction algortihm and makes necessary adjustments
        to comlete the TA tempalate.

        Ret:
            clock_mapping: Final clock mapping after clock reduction.
        """
        clock_mapping = {}
        for c in self.clocks:
            clock_mapping[c.name] = [c.name]
        self.finalize_transitions()
        spec_clocks = filter(lambda x: x.is_spec_clock, self.clocks)
        not_spec_clocks = filter(lambda x: not x.is_spec_clock, self.clocks)
        self.clocks = not_spec_clocks
        self.remove_unnecessary_resets()
        if len(self.clocks) > 1:
            self.reduce_clocks(clock_mapping)
        self.clocks += spec_clocks
        for c in self.clocks:
            c.assignments = list(set(c.assignments))
            for t in c.guards.keys():
                interface.add_guard(self.name, t[2], c.name, c.guards[t])
            for l in c.invariants.keys():
                interface.add_invariant(self.name, l, c.name, c.invariants[l])
            for t in c.assignments:
                interface.add_assignment(self.name, t[2], c.name)
        interface.add_current_template_to_nta(self.name)
        for c in clock_mapping.keys():
            clock_mapping[c] = list(set(clock_mapping[c]))
        return clock_mapping

    def create_committed_location(self):
        """
        Creates a committed location and adds to the locations list.

        Ret:
            committed_location_name: Name of the creates committed location.

        """
        committed_location_name = "C" + str(self.committed_location_count)
        interface.create_committed_location(self.name, committed_location_name)
        self.committed_location_count += 1
        self.locations.append(committed_location_name)
        return committed_location_name

    def get_clock_name(self):
        """
        Gives an unused clock name.

        Returns:
            Next available clock name.
        """
        temp = "x_" + str(self.clock_count)
        self.clock_count += 1
        return temp

    def reduce_clocks(self, clock_mapping):
        """
        Reduces number of clocks according to the reduction algorithm.

        Args:
            clock_mapping: Mappings of the clocks for reduction.
        """
        self.split(clock_mapping)
        dependency_graph = self.generate_dependency_graph()
        coloring = nx.coloring.greedy_color(dependency_graph, strategy=nx.coloring.strategy_largest_first)
        for i in range(max(coloring.values()) + 1):
            partition = []
            for j in coloring.keys():
                if i == coloring[j]:
                    partition.append(j)
            self.merge_clocks(partition, clock_mapping)

    def remove_unnecessary_resets(self):
        """
        Removes unnecessary resets, i.e., resets from which no constraint is reachable
        without passing trough another reset of the clock or there is no path in between.
        """
        for c in self.clocks:
            new_assignment_list = []
            control_locations = [t[0] for t in c.guards.keys()] + c.invariants.keys()
            for t_r in c.assignments:
                necessary = False
                reachable_control_locations = filter(lambda x: self.all_simple_paths(t_r[1], x) != [] or t_r[1] == x, control_locations)
                for l_c in reachable_control_locations:
                    necessary = self.is_reachable_without_resets(c, t_r[1], l_c)
                    if necessary:
                        break
                if necessary:
                    new_assignment_list.append(t_r)
            c.assignments = list(new_assignment_list)

    def is_reachable_without_resets(self, c, source, target):
        """
        Checks if there is path between two locations on which the given
        reset locations are not passed.
        """
        if source == target:
            return True
        all_simple_paths = self.all_simple_paths(source, target)
        not_necessary = True
        for path in all_simple_paths:
            n = len(path)
            for i in range(n - 1):
                not_necessary = (filter(lambda x: x[0] == path[i] and x[1] == path[i + 1], c.assignments) != [])
                if not_necessary:
                    break
            if not not_necessary:
                return True
        return False

    def split(self, clock_mapping):
        """
        Splits clocks of the TA template.

        Args:
            clock_mapping: Mappings of the clocks for reduction.
        """
        new_clock_list = []
        for c in self.clocks:
            if len(c.assignments) > 1:
                new_clock_list.append(c)
                continue
            temp = []
            t_r = c.assignments[0]
            for t_c in c.guards.keys():
                if self.is_reachable_without_resets(c, t_r[1], t_c[0]):
                    temp.append(Clock(name=self.get_clock_name(), guards={t_c: c.guards[t_c]} , assignments=[t_r]))
            for l in c.invariants.keys():
                if self.is_reachable_without_resets(c, t_r[1], l):
                    temp.append(Clock(name=self.get_clock_name(), invariants={l: c.invariants[l]} , assignments=[t_r]))
            for i in range(len(temp)):
                f = False
                for j in range(i + 1, len(temp)):
                    if self.is_dependent(temp[i], temp[j]):
                        temp = [c]
                        f = True
                        break
                if f:
                    break
            if not temp:
                temp = [c]
            clock_mapping[c.name] = map(lambda x: x.name, temp)
            new_clock_list.extend(temp)
        self.clocks = sorted(new_clock_list, key=lambda x: x.name)
        return

    def generate_dependency_graph(self):
        """
        Generates dependency graph.
        """
        dependency_graph = nx.Graph()
        dependency_graph.add_nodes_from(self.clocks)
        for c_1 in self.clocks:
            for c_2 in self.clocks:
                if self.is_dependent(c_1, c_2):
                    dependency_graph.add_edge(c_1, c_2)
        return dependency_graph

    def is_dependent(self, clock_1, clock_2):
        """
        Checks if given clocks are dependent.

        Args:
            clock_1: First clock.
            clock_2: Second clock.
        """
        scope_1 = []
        scope_2 = []
        reset_locations_1 = [t[1] for t in clock_1.assignments]
        reset_locations_2 = [t[1] for t in clock_2.assignments]
        control_locations_1 = [t[0] for t in clock_1.guards.keys()] + clock_1.invariants.keys()
        control_locations_2 = [t[0] for t in clock_2.guards.keys()] + clock_2.invariants.keys()
        for t_r in clock_1.assignments:
            for l_c in control_locations_1:
                scope_1.extend(self.compute_scope(clock_1, t_r[1], l_c))
        for t_r in clock_2.assignments:
            for l_c in control_locations_2:
                scope_2.extend(self.compute_scope(clock_2, t_r[1], l_c))
        for path in scope_1:
            if bool(set(path[1:]) & set(reset_locations_2)):
                return True
        for path in scope_2:
            if bool(set(path[1:]) & set(reset_locations_1)):
                return True
        return False

    def compute_scope(self, c, source, target):
        """
        Computes scope of a clocks between given locations using given reset locations.

        Args:
            source: Starting location of the scope.
            target: Ending location of the scope.
            reset_locations: Reset locations of the clock under consideration.
        """
        all_simple_paths = self.all_simple_paths(source, target)
        scope = []
        not_necessary = True
        for path in all_simple_paths:
            n = len(path)
            for i in range(n - 1):
                not_necessary = (path[i], path[i + 1]) in c.assignments
                if not_necessary:
                    break
            if not not_necessary:
                scope.append(path)
        return scope
        
    def all_simple_paths(self, source, target):
        """
        Finds all simple paths between two locations.

        Returns:
            All simple paths between source and target.
        """
        temp = list(nx.all_simple_paths(self.ta, source, target))
        if source == target:
            temp.append([source])
        return temp

    def merge_clocks(self, partition, clock_mapping):
        """
        Merges given set of clocks into one. Pick the first clock from the list.

        Args:
            partition: Partititon of the set of clocks obtained from graph coloring.
        """
        guards = {}
        invariants = {}
        assignments = []
        for c in partition:
            assignments.extend(c.assignments)
            for i in c.guards.keys():
                if i in guards.keys():
                    guards[i].extend(c.guards[i])
                else:
                    guards[i] = c.guards[i]
            for i in c.invariants.keys():
                if i in invariants.keys():
                    invariants[i].extend(c.invariants[i])
                else:
                    invariants[i] = c.invariants[i]
            self.clocks.remove(c)
        new_clock = Clock(partition[0].name, guards=guards, invariants=invariants, assignments=assignments)
        self.clocks.append(new_clock)
        temp = []
        partition_names = map(lambda x: x.name, partition)
        for c in clock_mapping.keys():
            for c_s in clock_mapping[c]:
                if (c_s in partition_names) and (new_clock.name not in clock_mapping[c]):
                    temp.append(new_clock.name)
                else:
                    temp.append(c_s)
            clock_mapping[c] = temp

    def print_clocks(self):
        """
        Prints clocks. Used for debugging.
        """
        for c in self.clocks:
            print "Name: ", c.name
            print "Guards: ", c.guards
            print "Invariants: ", c.invariants
            print "Assignments: ", c.assignments

    def print_dependency_graph(self):
        """
        Prints dependency graph. Used for debugging.
        """
        print map(lambda x: x.name, self.clocks)
        for x in self.clocks:
            for y in self.clocks:
                if self.is_dependent(x, y):
                    print x.name + "-" + y.name

    def is_reachable(self, l1, l2):
        """
        Checks if l2 is reachable from l1.
        """
        if self.all_simple_paths(l1, l2):
            return True
        return False

    def locations_along_paths(self, l1, l2):
        """
        Returns all the locations appearing on the path from l1 to l2.
        """
        all_simple_paths = self.all_simple_paths(l1, l2)
        locations = []
        for l in all_simple_paths:
            locations.extend(l)
        return list(set(locations))



class Clock(object):
    """
    Clock object definition. Used by the Template object.
    """
    def __init__(self, name="", guards={}, invariants={}, assignments=[], is_spec_clock=False):
        """
        Initializes the object.

        Args:
            name: String. Name of the clock.
            guards: Dictionary. [(s, t, t_id) : condition_list].
            invariants: Dictionary. [l : condition_list].
            assignments: List. [(s, t, t_id)].
        """
        self.name = name
        self.guards = guards if guards else {} # [(s, t, t_id) : condition_list]
        self.invariants = invariants if invariants else {} # [l : condition_list]
        self.assignments = assignments if assignments else [] # [(s, t, t_id)]
        self.is_spec_clock = is_spec_clock

    def add_guard(self, transition, condition):
        """
        Adds given guard info to the clock.

        Args:
            transition: Transition on which the guard will appear.
                        Key of the guards dictionary.
            condition: Condition. Value of the guards dictionary.
        """
        if transition in self.guards.keys():
            self.guards[transition] += [condition]
        else:
            self.guards[transition] = [condition]

    def add_invariant(self, location, condition):
        """
        Adds given invariant info to the clock.

        Args:
            location: Location in which the invariant will appear.
                      Key of the invariants dictionary.
            condition: Condition. Value of the invariants dictionary.
        """
        if location in self.invariants.keys():
            self.invariants[location].append(condition)
        else:
            self.invariants[location] = condition

    def add_assignment(self, transition):
        """
        Adds given assignment info to the clock.

        Args:
            transition: Transition on which the clocks will be reset.
        """
        if transition not in self.assignments:
            self.assignments.append(transition)


