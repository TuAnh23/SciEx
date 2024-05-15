from openai import OpenAI
import json
import os
from utils import grading_prompt_prefix, load_json, write_text_file, info_from_exam_path, encode_image, process_images, \
    LLM_LIST, extract_answer, parse_grade, dump_json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="openai")
    parser.add_argument("--llm-name-full", default="gpt-3.5-turbo-0125")
    parser.add_argument("--llm-name", default='gpt35')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    additional_info_path = f"human_feedback/{exam_name}/additional_info.json"
    if not os.path.isfile(additional_info_path):
        print(f"Exam additional info not found at {additional_info_path}. Skip.")
        exit()
    additional_info = load_json(additional_info_path)

    out_dir = f"llm_grade/{exam_name}/grader_{args.llm_name}"
    os.makedirs(out_dir, exist_ok=True)

    exam = load_json(f"exams_json/{exam_name}/{exam_name}_{lang}.json")
    llm_out_dir = f"llm_out_filtered/{exam_name}"

    if args.server_url != "openai":
        client = OpenAI(base_url=args.server_url, timeout=1800)
    else:
        client = OpenAI(timeout=1800)

    for llm_id in range(len(LLM_LIST)):
        grade_out_path = f"{out_dir}/{exam_name}_{lang}_{LLM_LIST[llm_id]}_grade.json"
        if os.path.isfile(grade_out_path):
            print(f"Grade already available at {grade_out_path}. Skip.")
            continue

        grades = []
        total_failed = 0
        total_points = 0

        llm_out_path = f"{llm_out_dir}/{exam_name}_{lang}_llm{llm_id}.txt"
        with open(llm_out_path, "r") as file:
            exam_answer = file.read()

        for q in range(len(exam['Questions'])):
            question = exam['Questions'][q].copy()
            question_id = question.pop("Index")
            max_score = float(str(additional_info["Questions"][q]["MaximumPoints"]).replace(',', '.'))
            prompt = grading_prompt_prefix(lang=lang, max_score=max_score)
            question_text = json.dumps(question)
            answer_text = extract_answer(question_id, exam_answer)

            if "vision" in args.llm_name_full:
                images = process_images(exam_name, question)
                images_messages = [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encode_image(pil_image=image)}"}
                    }
                    for image in images
                ]
                text_message = {
                    "type": "text",
                    "text": f"[question]\n{question_text}\n[/question] \n"
                            f"[answer]\n{answer_text}\n[/answer] \n"
                }
                message = [text_message] + images_messages

                response = client.chat.completions.create(
                    model=args.llm_name_full,
                    seed=0,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": message}
                    ]
                )
            else:
                response = client.chat.completions.create(
                    model=args.llm_name_full,
                    seed=0,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json.dumps(question)}
                    ]
                )
            out = response.choices[0].message.content
            grade = parse_grade(out, max_score=max_score)
            grades.append({
                "Index": question_id,
                "FullOutput": out,
                "Points": grade
            })
            if grade is not None:
                total_points = total_points + grade
            else:
                total_failed = total_failed + 1

        dump_json(
            {
                "Questions": grades,
                "TotalPoints": total_points,
                "NrFailed": total_failed,
                "TotalGradeGermanScale": None
            },
            file_path=grade_out_path
        )


if __name__ == "__main__":
    main()
