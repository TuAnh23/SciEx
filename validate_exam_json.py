import os.path

from pydantic import BaseModel, ValidationError, model_validator, field_validator
from typing import Optional, List, Any
import argparse
from utils import load_json


def report_extra_field_static(cls, data):
    extra_keys = []
    for k in data.keys():
        if k not in cls.__fields__.keys():
            extra_keys.append(k)
    if len(extra_keys) > 0:
        print(f"Extra keys: {extra_keys}")


class Subquestion(BaseModel):
    Index: str
    Content: str
    Figures: Optional[List[str]] = []

    @model_validator(mode='before')
    @classmethod
    def report_extra_field(cls, data: Any) -> Any:
        report_extra_field_static(cls, data)
        return data

    @field_validator('Figures')
    @classmethod
    def figure_paths_must_exist(cls, v):
        for figure_path in v:
            path = f"{dir_path}/{figure_path}"
            if not os.path.isfile(path):
                raise RuntimeError(f"Figure path {path} not exists")
        return v


class Question(BaseModel):
    Index: str
    Description: str
    Figures: Optional[List[str]] = []
    Subquestions: Optional[List[Subquestion]] = []


    @model_validator(mode='before')
    @classmethod
    def report_extra_field(cls, data: Any) -> Any:
        report_extra_field_static(cls, data)
        return data

    @field_validator('Figures')
    @classmethod
    def figure_paths_must_exist(cls, v):
        for figure_path in v:
            path = f"{dir_path}/{figure_path}"
            if not os.path.isfile(path):
                raise RuntimeError(f"Figure path {path} not exists")
        return v


class Exam(BaseModel):
    Questions: List[Question]

    @model_validator(mode='before')
    @classmethod
    def report_extra_field(cls, data: Any) -> Any:
        report_extra_field_static(cls, data)
        return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str)

    args = parser.parse_args()
    print(args)

    global dir_path
    dir_path = '/'.join(args.json_path.split("/")[:-1])
    exam = load_json(args.json_path)

    try:
        # Validate JSON data against Pydantic model
        validated_data = Exam(**exam)
        print("JSON data is valid!")
    except ValidationError as e:
        print("JSON data is not valid:", e)


if __name__ == "__main__":
    main()
