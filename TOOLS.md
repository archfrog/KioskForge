# Tools.md
Various notes on how to perform certain tasks using different tools.

## uv
### Activate the Python virtual environment
```bash
.venv\Scripts\activate
```

### Install all required dependencies
```bash
uv sync
```

### Upgrade lock file to currently installed packages
```bash
uv lock --upgrade
```
