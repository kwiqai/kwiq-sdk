import textwrap

import sys

import argparse
import yaml
from typing import Dict

from pydantic import BaseModel

from kwiq.core.flow import Flow
from kwiq.core.errors import ValidationError
from kwiq.core.utils import set_nested_value


class App(BaseModel):
    name: str

    flows: Dict[str, Flow] = {}

    def register_flow(self, flow: Flow):
        if flow.name in self.flows:
            raise ValueError(f"A flow with the name '{flow.name}' already exists.")
        self.flows[flow.name] = flow

    def run(self, flow_name: str, **kwargs) -> int:
        flow = self.flows.get(flow_name)
        if not flow:
            print(f"No flow found with the name '{flow_name}'.", file=sys.stderr)
            return 1

        print(f"Invoking flow:{flow_name} with args: {kwargs}")

        try:
            flow.execute(**kwargs)
            return 0
        except ValueError as ve:
            print(f"Error in flow execution: {str(ve)}", file=sys.stderr)
            return 1
        except ValidationError as ve:
            print(f"Error in flow execution: {str(ve)}", file=sys.stderr)
            return 1

    def main(self):
        if len(self.flows) == 0:
            print("ERROR: No flow registered")
            return

        parser = argparse.ArgumentParser(description=self.name)

        # Create subparsers for each flow
        subparsers = parser.add_subparsers(dest='flow', help='Available flows')

        for flow in self.flows.values():
            flow_parser = subparsers.add_parser(flow.name,
                                                help='Options for flow 1',
                                                formatter_class=argparse.RawTextHelpFormatter)
            flow_parser.add_argument('-c',
                                     '--config',
                                     action='store',
                                     help=textwrap.dedent(f'''Specify following in config or as x=y on commandline:
{flow.__class__.get_compact_schema()}'''),
                                     )

        args, extra_args = parser.parse_known_args()

        print("Args: ", args, extra_args)

        config = {}
        if args.__contains__('config') and args.config:
            # Load configuration from YAML
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)

        # Override YAML config with command-line overrides
        if extra_args:
            for extra in extra_args:
                key, value = extra.split('=')
                set_nested_value(config, key, value)

        # Run the specified flow, if any
        if len(self.flows) == 1:
            flow = next(iter(self.flows.values()))
            self.run(flow.name, **config)
        elif args.flow:
            self.run(args.flow, **config)
        else:
            # Handle the case for single flow or display help
            print("Specify a flow or use --help for more information.")
