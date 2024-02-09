from pathlib import Path

import shutil

import subprocess

import tempfile

from typing import Any, Optional

from kwiq.core.task import Task


class JsonFormatter(Task):
    name: str = "json-formatter"

    def fn(self, input_file_path: Path, output_file_path: Optional[Path]) -> Any:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            try:
                # Run jq and redirect output to the temporary file
                with open(temp_file.name, 'w') as output:
                    subprocess.run(['jq', '.'], stdin=open(input_file_path, 'r'), stdout=output, check=True)

                if output_file_path is None:
                    # Move the temporary file to replace the original file
                    shutil.move(temp_file.name, input_file_path)
                    print(f"JSON file [{input_file_path}] is formatted inline successfully.")
                else:
                    shutil.move(temp_file.name, output_file_path)
                    print(f"JSON file [{input_file_path}] is formatted successfully "
                          f"and output is written to: {output_file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error formatting JSON file [{input_file_path}]: {e}")
