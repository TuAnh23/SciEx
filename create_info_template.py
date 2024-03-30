import argparse
import os

from utils import load_json, dump_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str)

    args = parser.parse_args()

    exam = load_json(args.json_path)

    questions = []
    for question in exam['Questions']:
        questions.append({
            "Index": question["Index"],
            "MaximumPoints": None,
            "AverageStudentPoints": None,
            "GoldAnswerEnglish": None,
            "GoldAnswerGerman": None,
            "DifficultyLabel": None,
        })

    out_template = {"Questions": questions,
                    "MaximumTotalPoints": None,
                    "AverageStudentTotalPoints": None,
                    "MedianStudentGradeGermanScale": None}

    exam_name = args.json_path.split('/')[-2]
    out_dir = f"human_feedback_template/{exam_name}"
    os.makedirs(out_dir, exist_ok=True)
    dump_json(out_template, f"{out_dir}/additional_info.json")


if __name__ == "__main__":
    main()
