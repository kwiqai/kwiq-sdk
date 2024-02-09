from pathlib import Path

from pydantic import BaseModel

from kwiq.core.app import App
from kwiq.core.flow import Flow
from kwiq.task.apply_renames import ApplyRenames


class FlowConfig(BaseModel):
    mapping_file: Path
    search_directory: Path


class TestFlow(Flow):

    def fn(self, config: FlowConfig) -> None:
        print("In TestFlow... config: ", config, config.__class__)
        ApplyRenames(flow=self).execute(mapping_csv_path=config.mapping_file,
                                        search_directory=config.search_directory)


def main():
    current_directory = Path.cwd()
    mapping_file = (current_directory / "rename_mapping.csv")
    project_directory = (current_directory / "test-data").resolve()

    config = FlowConfig(mapping_file=mapping_file, search_directory=project_directory)

    app = App(name='TestApp')

    # register a new flow...
    app.register_flow(TestFlow(name="TestFlow"))

    app.run('TestFlow', config=config)


if __name__ == '__main__':
    main()
