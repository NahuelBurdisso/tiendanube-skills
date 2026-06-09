"""Run a vendored financial-analyst script as a subprocess on an input dict."""
import json, subprocess, sys, pathlib

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent

def run_script(script_name, input_obj, work_dir):
    work_dir = pathlib.Path(work_dir)
    in_path = work_dir / (script_name.replace(".py", "") + "-input.json")
    in_path.write_text(json.dumps(input_obj))
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name), str(in_path), "--format", "json"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{script_name} failed: {proc.stderr[:500]}")
    return json.loads(proc.stdout)
