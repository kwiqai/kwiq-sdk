import subprocess

from kwiq.core.task import Task


class RunCommand(Task):
    name: str = "run-command"
    silent: bool = False

    def fn(self, command: str) -> str:
        print(f"Running command: {command}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        output, _ = process.communicate()
        output = output.decode().strip()
        if process.returncode != 0 and not self.silent:
            error_msg = output
            print(f'Error: {error_msg}')
            raise subprocess.CalledProcessError(process.returncode, command, error_msg)
        return output
