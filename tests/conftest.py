import pytest
import subprocess
import os
import sys

# Define the python executable to use
PYTHON_EXECUTABLE = "/home/azureuser/projects/pyDIN/.pyDIN/bin/python3"

@pytest.fixture(scope="session")
def python_cmd():
    """Returns the path to the python interpreter."""
    if os.path.exists(PYTHON_EXECUTABLE):
        return PYTHON_EXECUTABLE
    return sys.executable

@pytest.fixture(scope="session")
def cli_cmd(python_cmd):
    """Returns a function to execute dincli commands."""
    def _run_cli(args, check=True, stream_output=True):
        cmd = [python_cmd, "-m", "dincli.main"] + args
        print(f"\nExecuting: {' '.join(cmd)}")
        if stream_output:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            stdout_chunks = []

            for line in process.stdout:
                print(line, end="")
                stdout_chunks.append(line)

            returncode = process.wait()
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=returncode,
                stdout="".join(stdout_chunks),
                stderr="",
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

        if check and result.returncode != 0:
             print(f"STDOUT: {result.stdout}")
             print(f"STDERR: {result.stderr}")
             raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result
    return _run_cli
