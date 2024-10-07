import argparse
import os
from utils import LLM_LIST

from utils import load_json, dump_json, map_llm_to_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str)

    args = parser.parse_args()

    exam = load_json(args.json_path)

    questions = []
    for question in exam['Questions']:
        questions.append({
            "Index": question["Index"],
            "Points": None
        })

    out_template = {"Questions": questions, "TotalPoints": None, "TotalGradeGermanScale": None}

    exam_name = args.json_path.split('/')[-2]
    out_dir = f"human_feedback_template/{exam_name}/grades"
    os.makedirs(out_dir, exist_ok=True)

    for llm in LLM_LIST:
        filename = args.json_path.split('/')[-1].replace('.json', f'_{map_llm_to_index(llm)}_grade.json')
        dump_json(out_template, f"{out_dir}/{filename}")


if __name__ == "__main__":
    main()
