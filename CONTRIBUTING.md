# Contributing

```bash
git clone https://github.com/Ehsas317/source-hunter.git
cd source-hunter
pip install -r requirements.txt
make test    # 13 offline unit tests (no key needed)
source-hunter "your claim" --output trace.json
```

Rules:

- Verdict names live in `sourcehunter/states.py` and are mirrored in `extension/lib/parse.js` — change both, with tests in `tests/test_states.py` and a JS note.
- Never claim a verdict without the Fetch evidence link behind it.
- Don't commit API keys or `__pycache__/`.
