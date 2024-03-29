import os
from pathlib import Path

from .run_command import RunCommand
from kwiq.core.task import Task


def parse_and_save_output(output, merge_output_file, conflict_output_file):
    auto_merge_lines = []
    conflict_lines = []

    for line in output.split('\n'):
        if line.startswith('Auto-merging'):
            auto_merge_lines.append(line)
        elif line.startswith('CONFLICT'):
            conflict_lines.append(line)

    with open(merge_output_file, 'w+') as f:
        f.write('\n'.join(auto_merge_lines))

    with open(conflict_output_file, 'w+') as f:
        f.write('\n'.join(conflict_lines))


class ApplyThreeWayMerge(Task):
    name: str = "apply-three-way-merge"

    def fn(self, base_dir: Path):
        # Inputs
        merge_dir = (base_dir / "merge_dir").resolve()
        os.chdir(merge_dir)
        RunCommand().execute(command='git checkout local')
        merge_output_file = (base_dir / "auto_merges.txt").resolve()
        conflict_output_file = (base_dir / "conflicts.txt").resolve()

        # Run git merge
        branch_name = 'remote'
        print(f'Merging {branch_name} with local branch')
        output = RunCommand(silent=True).execute(command=f'git merge {branch_name}')
        parse_and_save_output(output, merge_output_file, conflict_output_file)
