import os.path
import streamlit as st
from utils import load_json, map_llm_to_index, dump_json, load_images
from glob import glob


def main():
    st.title('LLM exam grading')
    st.write('You can fill in the additional information by choosing the `additional_information` option on the '
             'left side bar. You can grade each LLM outputs by choosing `llm_<index>` on the left side bar. '
             'Your input is automatically saved after you press `Enter` on each text box.')
    exam_name = st.text_input(label="Enter your exam name", placeholder="dummy_exam_march_2024")
    password = st.text_input(label="Enter your password", type='password')
    if exam_name:
        if os.path.isdir(f"exams_json/{exam_name}") and password == f"{exam_name}_k!k!T":
            report_progress(exam_name)
            lang = []
            if os.path.isfile(f"exams_json/{exam_name}/{exam_name}_en.json"):
                lang.append('en')
            if os.path.isfile(f"exams_json/{exam_name}/{exam_name}_de.json"):
                lang.append('de')
            st.write(f"You exam is available in these languages: {lang}")

            exam_lang = st.selectbox("Choose language", lang)

            if exam_name and exam_lang:
                exam_path = f"exams_json/{exam_name}/{exam_name}_{exam_lang}.json"

                if os.path.isfile(exam_path):
                    exam_json = load_json(exam_path)

                    llm_names = ['llava', 'mistral', 'mixtral', 'qwen', 'claude', 'gpt35', 'gpt4v']
                    selected_llm = st.sidebar.selectbox(
                        "Select to fill in additional information, or select an LLM to grade:",
                        ['additional_information'] + [map_llm_to_index(llm) for llm in llm_names]
                    )

                    if selected_llm.startswith('llm'):
                        answer_txt = f"llm_out_filtered/{exam_name}/{exam_name}_{exam_lang}_{selected_llm}.txt"
                        grade_json = f"human_feedback_streamlit/{exam_name}/grades/{exam_name}_{exam_lang}_{selected_llm}_grade.json"
                        with open(answer_txt, "r") as file:
                            answer = file.read()

                    info_json = f"human_feedback_streamlit/{exam_name}/additional_info.json"

                    input_key = 0
                    for question in exam_json['Questions']:
                        st.header(f"Question {question['Index']}:")
                        if 'Description' in question:
                            st_write_lines(question['Description'])
                        if 'Figures' in question:
                            for figure in question['Figures']:
                                display_image(f"exams_json/{exam_name}/{figure}")
                        if 'Subquestions' in question:
                            for subquestion in question['Subquestions']:
                                st.subheader(f"Subquestion {subquestion['Index']}:")
                                st_write_lines(subquestion['Content'])
                                if 'Figures' in subquestion:
                                    for figure in subquestion['Figures']:
                                        display_image(f"exams_json/{exam_name}/{figure}")

                        if selected_llm.startswith('llm'):
                            st.header(f"Answer to Question {question['Index']}:")
                            st_write_lines(extract_answer(question['Index'], answer))

                            max_points = find_question(load_json(info_json)['Questions'], question['Index'])['MaximumPoints']
                            if max_points is None:
                                st.warning('Please first fill in the maximum points for each question by choosing '
                                           '`additional_information` tab in the side bar on the left.')
                                points = st.text_input(
                                    label="Points", placeholder="0.0", key=input_key,
                                    value=prefil_per_question(key='Points', question_id=question['Index'], json_file=grade_json)
                                )
                                input_key = input_key+1
                            else:
                                points = st.text_input(
                                    label=f"Points out of {max_points}", placeholder="0.0", key=input_key,
                                    value=prefil_per_question(key='Points', question_id=question['Index'], json_file=grade_json)
                                )
                                input_key = input_key + 1
                            update_per_question(key='Points', value=points, question_id=question['Index'], json_file=grade_json)

                        else:
                            max_points = st.text_input(
                                label="Maximum Points", placeholder="100.0", key=input_key,
                                value=prefil_per_question(key='MaximumPoints', question_id=question['Index'], json_file=info_json)
                            )
                            input_key = input_key + 1
                            update_per_question(key='MaximumPoints', value=max_points, question_id=question['Index'], json_file=info_json)

                            average_student_points = st.text_input(
                                label="Average Student Points", placeholder="0.0", key=input_key,
                                value=prefil_per_question(key='AverageStudentPoints', question_id=question['Index'], json_file=info_json)
                            )
                            input_key = input_key + 1
                            update_per_question(key='AverageStudentPoints', value=average_student_points, question_id=question['Index'], json_file=info_json)

                            gold_en = st.text_input(
                                label="Gold Answer English", placeholder="Correct English answer", key=input_key,
                                value=prefil_per_question(key='GoldAnswerEnglish', question_id=question['Index'], json_file=info_json)
                            )
                            input_key = input_key + 1
                            update_per_question(key='GoldAnswerEnglish', value=gold_en, question_id=question['Index'], json_file=info_json)

                            gold_de = st.text_input(
                                label="Gold Answer German", placeholder="Correct German answer", key=input_key,
                                value=prefil_per_question(key='GoldAnswerGerman', question_id=question['Index'], json_file=info_json)
                            )
                            input_key = input_key + 1
                            update_per_question(key='GoldAnswerGerman', value=gold_de, question_id=question['Index'], json_file=info_json)

                            diff_label = st.text_input(
                                label="Difficulty Label", placeholder="easy/medium/hard", key=input_key,
                                value=prefil_per_question(key='DifficultyLabel', question_id=question['Index'], json_file=info_json)
                            )
                            input_key = input_key + 1
                            if diff_label.lower() not in ["easy", "medium", "hard"]:
                                st.warning("Difficulty label should be easy/medium/hard.")
                            update_per_question(key='DifficultyLabel', value=diff_label.lower(), question_id=question['Index'], json_file=info_json)

                    st.header(f"Exam total")
                    if selected_llm.startswith('llm'):
                        total_points = st.text_input(
                            label="Total Points", placeholder="0.0", key=input_key,
                            value=prefil_per_exam(key='TotalPoints', json_file=grade_json)
                        )
                        input_key = input_key + 1
                        update_per_exam(key='TotalPoints', value=total_points, json_file=grade_json)

                        total_grade_german_scale = st.text_input(
                            label="Total Grade German Scale", placeholder="4.0", key=input_key,
                            value=prefil_per_exam(key='TotalGradeGermanScale', json_file=grade_json)
                        )
                        input_key = input_key + 1
                        update_per_exam(key='TotalGradeGermanScale', value=total_grade_german_scale, json_file=grade_json)
                    else:
                        maximum_total_points = st.text_input(
                            label="Maximum Total Points", placeholder="100.0", key=input_key,
                            value=prefil_per_exam(key='MaximumTotalPoints', json_file=info_json)
                        )
                        input_key = input_key + 1
                        update_per_exam(key='MaximumTotalPoints', value=maximum_total_points, json_file=info_json)

                        avg_student_total_points = st.text_input(
                            label="Average Student Total Points", placeholder="0.0", key=input_key,
                            value=prefil_per_exam(key='AverageStudentTotalPoints', json_file=info_json)
                        )
                        input_key = input_key + 1
                        update_per_exam(key='AverageStudentTotalPoints', value=avg_student_total_points, json_file=info_json)

                        median_student_grade_german = st.text_input(
                            label="Median Student Grade German Scale", placeholder="4.0", key=input_key,
                            value=prefil_per_exam(key='MedianStudentGradeGermanScale', json_file=info_json)
                        )
                        input_key = input_key + 1
                        update_per_exam(key='MedianStudentGradeGermanScale', value=median_student_grade_german, json_file=info_json)

        elif not os.path.isdir(f"exams_json/{exam_name}"):
            st.warning(f"Exam {exam_name} not found. Please enter again.")
        else:
            st.warning(f"Wrong password. Please enter again.")


def report_progress(exam_name):
    if does_contain_none(f"human_feedback_streamlit/{exam_name}/additional_info.json"):
        st.warning("You have not finished filling in the additional information.")
    else:
        st.success("You have finished filling in the additional information!")
    unfinished_grading = []
    for file in glob(f"human_feedback_streamlit/{exam_name}/grades/*grade.json"):
        if does_contain_none(file):
            lang = file.split('/')[-1].split('_')[-3]
            llm = file.split('/')[-1].split('_')[-2]
            unfinished_grading.append(f"{llm}-{lang}")
    if len(unfinished_grading) > 0:
        st.warning(f"You have {len(unfinished_grading)} unfinished exams: {unfinished_grading}")
    else:
        st.success("You have finished grading!")


def does_contain_none(json_file):
    json_data = load_json(json_file)
    for k, v in json_data.items():
        if v is None:
            return True
    for question in json_data['Questions']:
        for k, v in question.items():
            if v is None:
                return True
    return False


def display_image(path):
    images, _ = load_images([path])
    for image in images:
        st.image(image, use_column_width="auto")


def prefil_per_question(key, question_id, json_file):
    out = load_json(json_file)
    value = find_question(out['Questions'], question_id)[key]
    return value if value is not None else ''


def prefil_per_exam(key, json_file):
    value = load_json(json_file)[key]
    return value if value is not None else ''


def update_per_question(key, value, question_id, json_file):
    if value:
        out = load_json(json_file)
        find_question(out['Questions'], question_id)[key] = value
        dump_json(out, json_file)


def update_per_exam(key, value, json_file):
    if value:
        out = load_json(json_file)
        out[key] = value
        dump_json(out, json_file)


def find_question(questions, question_id):
    for question in questions:
        if question['Index'] == question_id:
            return question
    return None


def extract_answer(question_id, answer):
    start_marker = f"Answer to Question {question_id}"
    end_marker = "****************************************************************************************\n" \
                 "****************************************************************************************"

    start_index = answer.find(start_marker)
    if start_index == -1:
        raise RuntimeError(f"Problem with extracting answer for question {question_id}")

    end_index = answer.find(end_marker, start_index)
    if end_index == -1:
        raise RuntimeError(f"Problem with extracting answer for question {question_id}")

    return answer[start_index + len(start_marker):end_index]


def st_write_lines(txt):
    lines = txt.split('\n')
    for line in lines:
        if line:
            st.write(line)


if __name__ == "__main__":
    main()
