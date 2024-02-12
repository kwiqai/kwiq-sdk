import json

import argparse

from pathlib import Path

from pydantic import BaseModel
from typing import Type, Optional, Iterator

import jmespath

from kwiq.iterator.commons import IteratorResult


class JsonIterator(BaseModel):
    file_path: Path
    json_path: str = '*'
    data_model: Optional[Type[BaseModel]] = None

    def __iter__(self) -> Iterator[IteratorResult]:
        with open(self.file_path, mode='r') as infile:
            content = json.load(infile)
            result = jmespath.search(self.json_path, content)
            if result is None:
                yield None

            if isinstance(result, dict):
                for key, value in result.items():
                    yield key, self.cast_to_basemodel(value)
            elif isinstance(result, (list, set)):
                for value in result:
                    yield self.cast_to_basemodel(value)
            else:
                yield self.cast_to_basemodel(result)

    def cast_to_basemodel(self, value):
        if self.data_model is None:
            return value
        else:
            return self.data_model(**value)


def test():
    parser = argparse.ArgumentParser(description="Test JSON Iterator")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("json_path", help="Path to the output file")

    args = parser.parse_args()

    print("Input file:", args.input_file)
    print("Json path:", args.json_path)

    # jmespath.exceptions.LexerError
    result = JsonIterator(file_path=args.input_file, json_path=args.json_path)
    for index, value in enumerate(result):
        print(index, value)


if __name__ == '__main__':
    test()
