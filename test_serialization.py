import pandas as pd
import json
import numpy as np

df = pd.DataFrame({
    "A": [1, 2, 3],
    "B": ["x", "y", "z"]
})

desc = df.describe(include="all").to_dict()
print("Dictionary from describe:", desc)

try:
    json_output = json.dumps(desc)
    print("JSON dump success:", json_output)
except Exception as e:
    print("JSON dump failed:", e)

# FastAPI uses standard json or similar. Does it allow NaN?
# Standard json allows NaN, but it prints "NaN", which is INVALID standard JSON.
# However, many browsers/JS engines do NOT accept it.
# But FastAPI might error out if it tries to coerce it.
