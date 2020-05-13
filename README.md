# ATAC: A Tool for Automating Timed Automata Construction

*ATAC (Automated Timed Automata Construction)* is a tool for automatic construction of *Timed Automata (TA)* models from descriptions and specifications given in structured natural language. The tool accepts a set of English sentences which are sufficient to model a TA model. The semantic meanings of these sentences are extracted and then mapped to the related TA concepts by the tool. The final model is given to the user as an XML file along with a query file (if any specification is implied by the input) both of which can be read by the UPPAAL, a tool for modeling, designing, simulating, and verifying TA models.

ATAC is implemented as a single-threaded Python program. For efficiency, we used three external Python modules that you also need to install before using ATAC: [NetworkX](https://networkx.github.io/), [Lark](https://lark-parser.readthedocs.io/en/latest/), and [Pyuppaal](https://github.com/bencaldwell/pyuppaal).

The usage of ATAC is very simple!

	1. Install necessary Python Modules.
	2. Download ATAC.
	3. Go to the terminal and type "python2 atac.py".
	4. Enter the output file name.
	4. Describe the TA model in your head following the input language rules of the tool. Notice that you need to enter one sentence in each line, that is press enter after each sentence.
	5. Press enter after the last sentece.
	6. You have your TA model as an XML file in the same directory!
	7. If you enter any sentence implying a specification, then you also have a query file with ".q" extension in the same directory!


ATAC accepts sentences from a formal grammar. Each input description sentence shall follow the description grammar and each input specification sentence shall follow the specification grammar. Below, we give both grammars along with the helper rules.

Notice that we define followings for names,

* __A__ := A TA model name;
* __L__ := A location name;
* __S__ := A signal name;
* __N__ := A natural number.


See `grammar_rules.pdf` for rules of the grammar for input.



The details of the grammar as well as the mapping done by the tool can be found in the paper presenting ATAC.
