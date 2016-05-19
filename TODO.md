
* sort out unit <-> conversion in OD3.py
* move all into source with:

    ./plugins
      fusion.py
    compile.py

* refactor to accomodate
  - manual transformation config and / or named parameter file exports
  - detect and handle `.obj` and / or  `.stl`

* configure using defaults / env vars and where possible using a strategy pattern / composition of utilities, inc:
  - the final output of `filesystem` and `request`
  - logging on or off
  - snapshot / copy the working folder
  - etc.

* make the fusion plugin look nice
* tidy up the repo

* post up as v2 demo
