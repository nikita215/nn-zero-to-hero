# AGENTS.md

## Cursor Cloud specific instructions

This is Andrej Karpathy's "Neural Networks: Zero to Hero" course — a collection of Jupyter notebooks. There are no traditional services, CI/CD, or build systems.

### Repository structure

- `lectures/micrograd/` — 2 notebooks on backpropagation and micrograd
- `lectures/makemore/` — 5 notebooks on language modeling (bigrams, MLP, BatchNorm, backprop, WaveNet)

### Running notebooks

Start JupyterLab:
```
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token="" --NotebookApp.password=""
```

Or execute notebooks programmatically:
```
jupyter nbconvert --to notebook --execute <notebook.ipynb> --ExecutePreprocessor.timeout=300
```

### Data files

The makemore notebooks require `names.txt` in `lectures/makemore/`. If missing, download it:
```
curl -fsSL https://raw.githubusercontent.com/karpathy/makemore/master/names.txt -o lectures/makemore/names.txt
```

### Known issues

- `makemore_part1_bigrams.ipynb` has a cell referencing variable `P` before it is defined in the notebook's cell order. This is a pre-existing notebook issue, not an environment problem.
- PyTorch is installed as CPU-only (`torch` from `https://download.pytorch.org/whl/cpu`). This is sufficient for all notebooks in this repo.
- System `graphviz` (apt package) must be installed alongside the Python `graphviz` package for computation graph rendering in the micrograd notebooks.
