# LLM-Powered Legal Assistant for Indian Law

## Project Description

Developed a large language model application that provides legal guidance for Indian law, trained on comprehensive legal datasets with context-aware responses.

## Table of Contents

- [Introduction](#introduction)
- [Project Structure](#project-structure)
- [Data and Sources](#data-and-sources)
- [Features](#features)
- [Usage](#usage)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Introduction

Legal research and guidance in the Indian context are complicated by the breadth and evolution of statutes, case law, and regulations. This project leverages a large language model (LLM) fine-tuned on Indian legal corpora—statutes, case law, and commentaries—to deliver context-sensitive, accessible legal assistance especially tailored for Indian law. The assistant can answer legal queries, provide summaries, suggest next steps, and cite relevant statutes or judgments.

## Project Structure

```
├── data/
│   ├── statutes/
│   ├── case_law/
│   └── commentaries/
├── models/
│   └── indian_law_llm.bin
├── notebooks/
│   └── data_preparation_and_finetuning.ipynb
├── src/
│   ├── app.py
│   ├── preprocess.py
│   ├── inference.py
│   └── evaluation.py
├── requirements.txt
├── README.md
└── LICENSE
```

## Data and Sources

- **Statutes:** Indian Penal Code, Contract Act, IT Act, etc.
- **Judgments:** Supreme Court, various High Courts, and tribunals.
- **Legal Commentaries:** Scholarly writings and guides.
- **Sources:** Indian Kanoon, Judis, Law Ministry website, open legal datasets.

**Preprocessing:** Includes text normalization, removal of non-legal content, and annotation of metadata (e.g., court, year, citations).

## Features

- **Context-Aware Legal Q&A:** Understands and answers legal questions in Indian context.
- **Statute and Case Citation:** Suggests relevant statutes and case law for given queries.
- **Summarization:** Provides plain-language summaries of judgments and statutes.
- **Guidance:** Outlines procedural steps or likely implications for legal scenarios.
- **User Interface:** (Optional) Web app using Streamlit/FastAPI/Gradio for interacting with the model.

## Usage

### Clone the Repository

```bash
git clone https://github.com/yourusername/indian-law-llm-assistant.git
cd indian-law-llm-assistant
```

### Install Requirements

```bash
pip install -r requirements.txt
```

### Load/Run the Model

```bash
python src/app.py
```

**Sample Query:**
```
What is the punishment for theft under Indian law?
```
_Model Response:_
```
Under Section 379 of the Indian Penal Code, the punishment for theft is imprisonment of up to 3 years, or with fine, or with both.
```

## Requirements

- Python 3.8+
- Transformers (HuggingFace or similar)
- PyTorch/TensorFlow
- Gradio, Streamlit, or FastAPI (for interface)
- pandas, numpy

## How to Run

1. Prepare a legal question or upload a legal document via the interface.
2. The model parses the input and provides a context-driven response with relevant legal citations.
3. Use the summarization and citation features for efficient legal research.

## Contributing

Contributions are welcome! Please fork the repo, make your suggested changes, and submit a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Indian Kanoon and Judis for open legal data.
- OpenAI, HuggingFace, and the open-source NLP/LLM communities.
- Legal scholars who have contributed fundamental resources and commentaries.
