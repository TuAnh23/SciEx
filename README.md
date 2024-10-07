# SciEx: Benchmarking Large Language Models on Scientific Exams with Human Expert Grading and Automatic Grading

This repository contains the script to create SciEx and perform automatic evaluation with LLM graders.

The SciEx dataset can be found [here](https://huggingface.co/datasets/tuanh23/SciEx).

Our paper, containing details about the dataset and analysis, can be found [here](https://arxiv.org/pdf/2406.10421).

# Leaderboard

| No. | LLM     | Solve-Exam Performance* (Expert graded)  | Solve-Exam Performance* (GPT-4V graded) | Grade-Exam Performance** |
|-----|---------|:----------------------------------------:|:---------------------------------------:|--------------------------|
| 1   | o1-mini |                     -                    |                   58.3                  |           0.887          |
| 2   | Claude  |                   59.4                   |                   57.7                  |             -            |
| 3   | GPT-4V  |                   58.2                   |                   56.2                  |           0.948          |
| 4   | Mixtral |                   41.1                   |                   38.2                  |             -            |
| 5   | Qwen    |                   35.4                   |                   42.0                  |             -            |
| 6   | GPT-3.5 |                   32.8                   |                   38.0                  |             -            |
| 7   | Mistral |                   25.9                   |                   24.6                  |             -            |
| 8   | Llava   |                   21.5                   |                   24.2                  |             -            |

*: Solve-exam performance is measured by the average grade percentage across exams.

**: Grade-exam performance is measured by the Pearson correlation between the grades provided by the LLMs and grades provided by the experts.

The LLMs are sorted first by the expert grade, then by the automatic grade (currently using GPT-4V).