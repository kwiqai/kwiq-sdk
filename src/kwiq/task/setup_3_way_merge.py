import os
from pathlib import Path

from pydantic import BaseModel

from .clean_directory import CleanDirectory
from .copy_directory import CopyDirectory
from .run_command import RunCommand
from kwiq.core.task import Task


class RepoInfo(BaseModel):
    repo_path: str
    branch: str
    sub_path: str


class MergeRepoInfos(BaseModel):
    base: RepoInfo
    local: RepoInfo
    remote: RepoInfo


def setup_git_rep(merge_dir: Path, temp_dir: Path, repo_info: RepoInfo, repo_key: str):
    # Clone specific branch to a temp folder
    temp_clone_dir = (temp_dir / f"temp_{repo_key}").resolve()
    RunCommand().execute(command=f'git clone {repo_info.repo_path} {temp_clone_dir}')
    os.chdir(temp_clone_dir)
    RunCommand().execute(command=f'git checkout {repo_info.branch}')
    os.chdir(merge_dir)

    # If not base branch, create a new branch
    if repo_key != 'base':
        RunCommand().execute(command='git checkout base')
        RunCommand().execute(command=f'git checkout -b {repo_key}')

    CleanDirectory().execute(directory=merge_dir, filter=lambda i: i == ".git")

    # Copy the specific folder to the main repo directory
    src_dir = (temp_clone_dir / repo_info.sub_path).resolve()
    CopyDirectory().execute(src_directory=src_dir, dest_directory=merge_dir, filter=lambda i: i == ".git")

    # Git add and commit
    RunCommand().execute(command='git add .')
    RunCommand().execute(command=f'git commit -m "{repo_key} version"')

    # Clean up temporary clone
    # shutil.rmtree(temp_clone_dir)


def setup_git_repos(merge_dir: Path, temp_dir: Path, repo_infos: MergeRepoInfos):
    os.makedirs(merge_dir, exist_ok=True)
    os.chdir(merge_dir)
    RunCommand().execute(command='git init')
    RunCommand().execute(command='git commit --allow-empty -m "Initial empty commit"')
    RunCommand().execute(command='git branch -M base')

    os.makedirs(temp_dir, exist_ok=True)

    setup_git_rep(merge_dir, temp_dir, repo_infos.base, 'base')
    setup_git_rep(merge_dir, temp_dir, repo_infos.local, 'local')
    setup_git_rep(merge_dir, temp_dir, repo_infos.remote, 'remote')


class InputDataModel(BaseModel):
    output_dir: Path
    repo_infos: MergeRepoInfos


class SetupThreeWayMerge(Task):
    name: str = "setup-three-way-merge"

    def fn(self, data: InputDataModel):
        # Inputs
        base_dir = data.output_dir
        merge_dir = (base_dir / "merge_dir").resolve()
        temp_dir = (base_dir / "temp_dir").resolve()

        # Set up the git repository and branches
        setup_git_repos(merge_dir, temp_dir, data.repo_infos)
