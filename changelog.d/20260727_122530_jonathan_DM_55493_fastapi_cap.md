### Other changes

- Constrained FastAPI to `<0.140`. FastAPI 0.140 made `Dependant` a slots dataclass, which breaks FastStream's FastAPI plugin (it monkey-patches attributes onto that instance). Tracked upstream as [ag2ai/faststream#2959](https://github.com/ag2ai/faststream/issues/2959); the cap can be lifted once that is fixed.
