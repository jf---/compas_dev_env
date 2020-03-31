# compas_env

some scripts that help to setup a `compas` development environment

- developer focussed
    - forks the repos such to be able to create pull requests conveniently
        - you need to edit the `.env` file or have a `GITHUB_TOKEN` stuffed in your environment variables
        - only when there are no changes staged
      
    - modules are installed with a developer install eg `pip install -e .` such that changes to the source are reflected in the environment
    
- complete 
    - all known modules are installed
    
- convenient
    - installs the python modules with the `Rhino` environment, in such a way that code changes are reflected

## TODO

- [ ] rebase a repo from `origin` when dealing with a forked repo
- [ ] actually install modules in Rhino's python path
    - [ ] incl `RhinoWIP` support
- [ ] conda package for [libigl](https://anaconda.org/freecad/libigl) exists on the `freecad` channel, but old and `linux` only
    
     
    

 