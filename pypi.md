# PYPI

See https://packaging.python.org/en/latest/tutorials/packaging-projects/

install requirements

```
python -m pip install --upgrade build twine
```

build pacakge

```
python -m build
```

upload package

```
python -m twine upload --repository testpypi dist/*
```
