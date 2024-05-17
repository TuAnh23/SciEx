import json
import os
from utils import grading_prompt_prefix, load_json, info_from_exam_path, encode_image, process_images, \
    LLM_LIST, extract_answer, parse_grade, dump_json, map_index_to_llm, map_llm_to_index, load_text_file, remove_key
import argparse
import random
from llm_clients import OpenAIClient, ClaudeClient, HFTextGenClient, HFLlava


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-type", choices=['openai', 'claude', 'hf_text_gen', 'hf_llava'])
    parser.add_argument("--server-url", default="openai")
    parser.add_argument("--llm-name-full", default="gpt-3.5-turbo-0125")
    parser.add_argument("--llm-name", default='gpt35')
    parser.add_argument("--nr-shots", default=0, type=int)
    parser.add_argument("--shot-type", default="same_question", type=str, choices=['same_question', 'same_exam', 'diff_exam'])
    parser.add_argument("--with-ref", default='no', choices=['yes', 'no'], type=str)
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    random.seed(0)

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    additional_info_path = f"human_feedback/{exam_name}/additional_info.json"
    if not os.path.isfile(additional_info_path):
        print(f"Exam additional info not found at {additional_info_path}. Skip.")
        exit()
    additional_info = load_json(additional_info_path)

    if args.server_type == 'openai':
        llm_client = OpenAIClient(model=args.llm_name_full, server_url=args.server_url, seed=0)
    elif args.server_type == 'claude':
        llm_client = ClaudeClient(model=args.llm_name_full)
    elif args.server_type == 'hf_text_gen':
        llm_client = HFTextGenClient(model=args.llm_name_full, server_url=args.server_url)
    elif args.server_type == 'hf_llava':
        llm_client = HFLlava(model=args.llm_name_full, device='cuda')
    else:
        raise RuntimeError(f"server_type {args.server_type} not implemented.")

    out_dir = f"llm_grade/{exam_name}/grader_{args.llm_name}/{args.nr_shots}_shot"
    if args.nr_shots > 0:
        out_dir = f"{out_dir}/{args.shot_type}_shot"
    os.makedirs(out_dir, exist_ok=True)

    exam = load_json(f"exams_json/{exam_name}/{exam_name}_{lang}.json")
    llm_out_dir = f"llm_out_filtered"

    for llm_id in range(len(LLM_LIST)):
        if args.nr_shots == 0:
            shot_llms, shot_exam_name = None, None
        else:
            shot_llms = [x for x in range(len(LLM_LIST)) if x != llm_id]
            shot_llms = random.sample(shot_llms, k=args.nr_shots)
            shot_llms = [map_index_to_llm(x) for x in shot_llms]

            if args.shot_type in ['same_question', 'same_exam']:
                shot_exam_name = exam_name
            else:
                if lang == 'en':
                    shot_exam_name = "HCI_SS23" if exam_name != "HCI_SS23" else "DLNN-WS2223"
                elif lang == 'de':
                    shot_exam_name = "dbs_exam_ipd-boehm_2023" if exam_name != "dbs_exam_ipd-boehm_2023" else "TGI2324"
                else:
                    raise RuntimeError(f"lang {lang} not valid.")

        shot_exam = load_json(f"exams_json/{shot_exam_name}/{shot_exam_name}_{lang}.json") if args.nr_shots != 0 else None
        shot_additional_info = load_json(f"human_feedback/{shot_exam_name}/additional_info.json") if args.nr_shots != 0 else None
        shot_llm_answers = [
            load_text_file(f"{llm_out_dir}/{shot_exam_name}/{shot_exam_name}_{lang}_{map_llm_to_index(x)}.txt", single_str=True)
            for x in shot_llms
        ] if args.nr_shots != 0 else None
        shot_human_grades = [
            load_json(f"human_feedback/{shot_exam_name}/grades/{shot_exam_name}_{lang}_{map_llm_to_index(shot_llm)}_grade.json")
            for shot_llm in shot_llms
        ] if args.nr_shots != 0 else None

        grade_out_path = f"{out_dir}/{exam_name}_{lang}_{LLM_LIST[llm_id]}_grade.json"

        if os.path.isfile(grade_out_path):
            print(f"Grade already available at {grade_out_path}. Skip.")
            continue

        grades = []
        total_failed = 0
        total_points = 0

        llm_out_path = f"{llm_out_dir}/{exam_name}/{exam_name}_{lang}_llm{llm_id}.txt"
        exam_answer = load_text_file(llm_out_path, single_str=True)

        for q in range(len(exam['Questions'])):
            question = exam['Questions'][q].copy()
            question_id = question.pop("Index")

            if args.nr_shots == 0:
                shot_questions = None
                shots = []
            else:
                if args.shot_type == "same_question":
                    shot_questions_id = [q] * args.nr_shots
                    shot_questions = [question_id] * args.nr_shots
                elif args.shot_type == "same_exam":
                    other_questions_id = [i for i in range(len(shot_exam['Questions'])) if i != q]
                    shot_questions_id = random.sample(other_questions_id, k=args.nr_shots)
                    shot_questions = [shot_exam["Questions"][i]["Index"] for i in shot_questions_id]
                else:
                    other_questions_id = [i for i in range(len(shot_exam['Questions']))]
                    shot_questions_id = random.sample(other_questions_id, k=args.nr_shots)
                    shot_questions = [shot_exam["Questions"][i]["Index"] for i in shot_questions_id]

                # Put all info of the shots to a list of dict.
                # Each shot should contain the question, the llm output, and the grade
                shots = [{
                    "Question": json.dumps(remove_key(shot_exam['Questions'][shot_questions_id[i]], "Index")),
                    "Answer": extract_answer(shot_exam['Questions'][shot_questions_id[i]]['Index'], shot_llm_answers[i]),
                    "MaxScore": float(str(shot_additional_info["Questions"][shot_questions_id[i]]["MaximumPoints"]).replace(',', '.')),
                    "GoldGrade": shot_human_grades[i]['Questions'][shot_questions_id[i]]['Points']
                } for i in range(args.nr_shots)]

            max_score = float(str(additional_info["Questions"][q]["MaximumPoints"]).replace(',', '.'))
            prompt = grading_prompt_prefix(lang=lang, shots=shots)
            question_text = json.dumps(question)
            answer_text = extract_answer(question_id, exam_answer)
            input_body = f"[question]\n{question_text}\n[/question] \n" \
                         f"[answer]\n{answer_text}\n[/answer] \n" \
                         f"[max_score] {max_score} [/max_score] \n"

            out = llm_client.send_request(
                prompt,
                input_body=input_body,
                images=process_images(exam_name, question),
                max_tokens=500
            )

            grade = parse_grade(out, max_score=max_score)
            grades.append({
                "Index": question_id,
                "PromptInput": f"{prompt}\n{input_body}",
                "ShotLLMs": shot_llms,
                "ShotExam": shot_exam_name,
                "ShotQuestion": shot_questions,
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
