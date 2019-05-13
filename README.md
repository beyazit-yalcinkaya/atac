# ATAC: A Tool for Automating Timed Automata Construction

*ATAC (Automated Timed Automata Construction)* is a tool for automatic construction of *Timed Automata (TA)* models from descriptions and specifications given in structured natural language. The tool accepts a set of English sentences which are sufficient to model a TA model. The semantic meanings of these sentences are extracted and then mapped to the related TA concepts by the tool. The final model is given to the user as an XML file along with a query file (if any specification is implied by the input) both of which can be read by the UPPAAL, a tool for modeling, designing, simulating, and verifying TA models.

ATAC is implemented as a single-threaded Python program. For efficiency, we used three external Python modules that you also need to install before using ATAC: [NetworkX](https://networkx.github.io/), [Lark](https://lark-parser.readthedocs.io/en/latest/), and [Pyuppaal](https://github.com/bencaldwell/pyuppaal).

The usage of ATAC is very simple!

	1. Install necessary Python Modules.
	2. Download ATAC.
	3. Go to the terminal and type "python atac.py".
	4. Enter the output file name.
	4. Describe the TA model in your head following the input language rules of the tool. Notice that you need to enter one sentence in each line, that is press enter after each sentence.
	5. Press enter after the last sentece.
	6. You have your TA model as an XML file in the same directory!
	7. If you enter any sentence implying a specification, then you also have a query file with ".q" extension in the same directory!


ATAC accepts sentences from a formal grammar. Each input sentence has to follow this grammar as well as the general ordering of the sentences. Below, we give the grammar.

* __template__ := A TA model name.
* __location__ := A location name.
* __synch__ := A signal name.
* __N__ := A natural number.
* &phi;<sub>TA</sub> ::= &phi;<sub>init</sub> &phi;<sub>main</sub>
* &phi;<sub>main</sub> ::= &phi;<sub>sys</sub> &phi;<sub>main</sub> | &phi;<sub>spec</sub> &phi;<sub>main</sub> | &epsilon;
* &phi;<sub>init</sub> ::= __template__ *can only be* __location__ | __template__ *can be* &phi;<sub>locs</sub> *and it is initially* __location__
* &phi;<sub>sys</sub> ::= &phi;<sub>tran</sub> | *if* &phi;<sub>cond</sub> *then* &phi;<sub>tran</sub>
* &phi;<sub>spec</sub> ::= *it goes to* __location__ *in every* __N__ | *the time spent in* __location__ *cannot be more than* __N__ | *the time spent in* __location__ *cannot be more than or equal to* __N__ ∣ __location__ *must be reached from* &phi;<sub>locs</sub> ∣ __location__ *must be reached from* &phi;<sub>spec</sub> *within* __N__
* &phi;<sub>locs</sub> ::= __location__ | __location__ &phi;<sub>locs</sub>
* &phi;<sub>tran</sub> ::= *it can go to* &phi;<sub>locs</sub> *from* &phi;<sub>locs</sub> | *it can send* __synch__ *and go to* &phi;<sub>locs</sub> *from* &phi;<sub>locs</sub>
* &phi;<sub>cond</sub> ::= &phi;<sub>scond</sub> | &phi;<sub>tcond</sub> | &phi;<sub>scond</sub> *and* &phi;<sub>tcond</sub>
* &phi;<sub>scond</sub> ::= *it receives* __synch__
* &phi;<sub>tcond</sub> ::= *the time spent after* &phi;<sub>ent_lea</sub> __location__ *is* &phi;<sub>constr</sub> | *the time spent after* &phi;<sub>ent_lea</sub> __location__ *is* &phi;<sub>constr</sub> *and* &phi;<sub>tcond</sub>
* &phi;<sub>constr</sub> ::= *more than* __N__ | *more than or equal to* __N__ | *less than* __N__ | *less than or equal to* __N__ | *equal to* __N__
* &phi;<sub>ent_lea</sub> ::= *entering* | *leaving*

The sentences given by the rule &phi;<sub>spec</sub> indicates specifications of the TA model needs to follow. We map these sentences to queries that can be checked by the UPPAAL and give thees queries in a query file as an output. The details of the grammar as well as the mapping done by the tool can be found in the tool paper presenting ATAC.