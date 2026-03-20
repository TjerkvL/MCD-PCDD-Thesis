CDLG: Concept Drift Log Generator
====

About
---
This repository contains the prototype of the CDLG tool described in the paper: 
[_CDLG: A Tool for the Generation of Event Logs with Concept Drifts_](https://ceur-ws.org/Vol-3216/paper_241.pdf) 
by Justus Grimm, Alexander Kraus, and Han van der Aa, BPM Demonstration & Resources Track, 2022.

The primary contact for questions or comments regarding CDLG is Alexander Kraus: alexander[dot]kraus[at]uni-mannheim[dot]de 

Project Status: Version 2.0
---
Current Version 2.0 is an upgrade of the initial prototype, Version 1.0, outlined in the [paper](https://ceur-ws.org/Vol-3216/paper_241.pdf). 
To access the original tool, refer to the commit tagged "Version_1" on January 25, 2023. 
The documentation for Version 1.0 is stored in the [documentation](documentation) folder (video, tutorial, etc.), though it may not fully align with the current version.
Version 1.0 has also a [python package](https://gitlab.uni-mannheim.de/processanalytics/cdlg-package), which you can use in your project.

Tool objective and scope
---
The tool aims to quickly and automatically generate collections of event logs with known concept drifts.
It supports:
* Automated generation of event logs  with concept drifts
* Generation of multiple concept drifts per log
* Four drift types: sudden, gradual, incremental, and recurring
* Concept drifts in the control-flow perspectives of a process
* Automated and controlled (only in terminal mode through the import of block-structured models, like BPMN, Petri nets, Process trees) generation of process versions
* Random and controlled (only in terminal mode) evolution of changes in the control-flow process perspective
* Noise insertion
* Creation of the gold standard as a standalone file containing comprehensive information about the drift.
* Automated evaluation of the concept drift detection accuracy (if the tool's class is used to store detected drift information)

Usage
---
The tool provides two operation modes:
1. **Automated generation** of a collection of event logs with concept drifts using a parameter file
   * Specify the parameters in the text files stored in _src/input_parameters/default_ (if needed)
   * Run <code>python _generate_collection_of_logs.py_</code>
2. **Manual generation** of event logs with drifts via terminal (provides more flexibility but takes longer)
   * Run <code>python _generate_log_via_terminal.py_</code>

**Note:** The manual generation mode is not fully tested and might lead to bugs or errors. 

### Input ###

1. **Automated generation**. The input file contains following parameters that can be specified:

   * Process_tree_complexity [simple, middle, complex]: Defines the complexity of generated process models using [_PTandLogGenerator_](https://ceur-ws.org/Vol-1789/bpm-demo-2016-paper5.pdf), a generator for artificial event data (part of PM4PY library) 
   * Process_tree_evolution_proportion [float in (0.0, 1.0)]: Quantifies the extent to which a process change modifies the process tree.
   * Number_event_logs [positive integer]: Specifies how many event logs should be generated
   * Number_traces_per_process_model_version [positive integer]: Determines how many trace per process version should be generated
   * Number_traces_for_gradual_change [positive integer]: Defines the duration of a gradual transition from one process version to another in terms of the number of traces
   * Change_type [sudden, gradual]: Specifies how process changes should happen (drifts consist of process changes and each process changes can happen graudally or suddenly). 
   * Drift_types [sudden, gradual, incremental, recurring]: Defines drift types that will be randomly used
   * Number_drifts_per_log [positive integer]: Sets the number of drifts per log 
   * Noise [Boolean]: If True, noise is inserted using procedure presented [here](https://www.sciencedirect.com/science/article/pii/S030643792100065X?via%3Dihub) that randomly inserts, removes, and swaps events in a fraction of the traces in an event log
   * Noisy_trace_prob [float in (0.0, 1.0)]: Sets the probability to modify a trace 
   * Noisy_event_prob [float in (0.0, 1.0)]: Sets the probability to do another change within the trace
   * Trace_exp_arrival_sec [integer]: Defines the trace exponential inter-arrival rate in seconds
   * Task_exp_duration_sec [integer]: Defines the activity duration in seconds using exponential distribution 
   * Gradual_drift_type [linear, exponential]: Specifies the mechanism for a gradual transformation from one process version to another
   * Incremental_drift_number: [positive integer]: Defines how many process changes constitute an incremental drift
   * Recurring_drift_number [positive integer]: Defines how many process changes constitute a recurring drift

**Note:** Users have the flexibility to input multiple values for each parameter. In these cases, the tool will randomly select one from the provided options. For strings, ensure separation by a comma and space (", "), while for numbers, use a hyphen ("-").For example:
* Process_tree_complexity: simple, middle, complex 
* Number_traces_per_process_model_version: 1000-2000

2. **Manual generation**. After running the corresponding script, the terminal guides through relevant questions. 


### Output ###
All generated event logs in XES format are saved with a corresponding sub-folder in _output_.
A _gold_standard.csv_ file is automatecally created and stored in the folder with the generated collection


Installation
---
**The project requires python >= 3.9 and graphviz**

Install python [here](https://www.python.org/downloads/) and graphviz [here](https://graphviz.org/download/).

0. Optional: create a virtual environment 
1. Install the packages in requirements.txt: <code>pip install -r requirements.txt</code>

**Note:** The exact versions of the packages must be installed, as the versions of the dependencies have changed.
Otherwise, errors may occur.


Evaluation
---
The initial Version 1.0 was evaluated using the Visual Drift Detection ([VDD](https://github.com/yesanton/Process-Drift-Visualization-With-Declare)) technique.
The generated event logs by CDLG, which were used for the evaluation, are stored in the folder _'documentation/evaluation'_.

 

Reference
---
* [PM4Py](https://pm4py.fit.fraunhofer.de)
* [PTandLogGenerator](https://ceur-ws.org/Vol-1789/bpm-demo-2016-paper5.pdf)


License
---
Copyright (C) 2024 Alexander Kraus
This project is licensed under the GNU General Public License v3.0.
See the LICENSE file for details.