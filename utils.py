import json
import os


def prompt_prefix(lang, scope):
    """
    :param lang: 'en' or 'de'
    :param scope: 'per_question' or 'per_exam'
    :return: prompt prefix as a string
    """
    if scope == 'per_question':
        if lang == 'en':
            prompt = "Answer the following question in English. It is very important for my career. " \
                     "You should only output in JSON format, " \
                     "where you return the corresponding question indices, subquestion indices and the answers. " \
                     "Don't output anything else other than the JSON. " \
                     "Your output should look like: " \
                     "{\"Index\": ..., \"Subquestions\": [{\"Index\": ..., \"Answer\": ...}, ...], ...}.\n" \
                     "Here is the question: "
        elif lang == 'de':
            prompt = "Beantworten Sie die folgende Frage nur auf Deutsch, " \
                     "verwenden Sie bei Fachbegriffen nur ggf. Englisch. " \
                     "Es ist sehr wichtig für meine Karriere. " \
                     "Sie sollten nur im JSON-Format ausgeben, " \
                     "wo Sie die entsprechenden Frageindizes, Unterfrageindizes und die Antworten zurückgeben. " \
                     "Geben Sie nichts anderes als JSON aus." \
                     "Ihre Ausgabe sollte so aussehen: " \
                     "{\"Index\": ..., \"Subquestions\": [{\"Index\": ..., \"Answer\": ...}, ...], ...}.\n" \
                     "Hier ist die Frage: "
        else:
            raise RuntimeError(f"No prompt for lang {lang}")
    elif scope == 'per_exam':
        if lang == 'en':
            prompt = "You are a university student. Do the following exam in English. " \
                     "You should only output in JSON format, " \
                     "where you return the corresponding question indices, subquestion indices and the answers. " \
                     "Don't output anything else other than the JSON. " \
                     "Your output should look like: " \
                     "{\"Answers\": [{\"Index\": ..., \"Subquestions\": [{\"Index\": ..., \"Answer\": ...}, ...], " \
                     "...}],...}."
        elif lang == 'de':
            prompt = "Sie sind Student. " \
                     "Führen Sie die folgende Prüfung nur auf Deutsch durch, " \
                     "verwenden Sie bei Fachbegriffen nur ggf. Englisch. " \
                     "Sie sollten nur im JSON-Format ausgeben, " \
                     "wo Sie die entsprechenden Frageindizes, Unterfrageindizes und die Antworten zurückgeben. " \
                     "Geben Sie nichts anderes als JSON aus." \
                     "Ihre Ausgabe sollte so aussehen: " \
                     "{\"Answers\": [{\"Index\": ..., \"Subquestions\": [{\"Index\": ..., \"Answer\": ...}, ...], " \
                     "...}],...}."
        else:
            raise RuntimeError(f"No prompt for lang {lang}")
    else:
        raise RuntimeError(f"No prompt for scope {scope}")
    return prompt


def load_json(file_path):
    with open(file_path, 'r') as f:
        obj = json.load(f)
    return obj


def dump_json(obj, file_path):
    with open(file_path, 'w') as f:
        json.dump(obj, f, indent=4)


def info_from_exam_path(exam_json_path):
    exam_name = exam_json_path.split('/')[-2]
    lang = exam_json_path.split('/')[-1].replace('.json', '').split('_')[-1]
    assert os.path.isfile(f"exams_json/{exam_name}/{exam_name}_{lang}.json")
    assert lang in ['en', 'de']
    return exam_name, lang


def collect_figures(question_dict):
    figure_list = []
    if 'Figures' in question_dict:
        figure_list.extend(question_dict['Figures'])
    if 'Subquestions' in question_dict:
        for subquestion_dict in question_dict['Subquestions']:
            if 'Figures' in subquestion_dict:
                figure_list.extend(subquestion_dict['Figures'])
    return figure_list
