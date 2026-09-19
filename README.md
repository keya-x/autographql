# AutoGraphQL

[![EMNLP 2026 Industry Track](https://img.shields.io/badge/EMNLP%202026-Industry%20Track-blue.svg)](#)

AutoGraphQL is a systematic, schema-driven framework for synthesizing GraphQL query datasets directly from GraphQL SDL schemas. It supports a broad range of GraphQL constructs, including fragments, inline fragments, directives, filters, pagination, aliases, and mutations, enabling the automated creation of diverse, executable datasets for fine-tuning LLMs and adapting them to domain or enterprise-specific schemas.

Official implementation of our paper accepted at the **EMNLP 2026 Industry Track**.

**[Paper](docs/autographql.pdf) | [Leaderboard](https://nl2graphql-bench.github.io/)**

## At a Glance

- **17,621** NL2GraphQL instances
- **173** GraphQL schemas
- **7** query categories
- Schema-disjoint training, public-test, and hidden-test splits
- Automated schema and execution validation
- Support for complex GraphQL constructs
- Web interface for query generation and dataset creation

## Framework

AutoGraphQL takes a GraphQL SDL schema as input and systematically generates diverse GraphQL queries while enforcing schema validity and execution correctness. Generated queries can subsequently be paired with natural-language descriptions to construct NL2GraphQL datasets and evaluate language models.

<p align="center">
  <img src="docs/figures/toolkit.png" alt="AutoGraphQL framework overview" width="900"/>
</p>

<p align="center">
  <em>Figure 1. Overview of the AutoGraphQL framework.</em>
</p>

The framework consists of the following main stages:

1. **Schema Processing**: parses and analyzes the input GraphQL SDL schema.
2. **Query Generation**: synthesizes queries across multiple GraphQL constructs and query categories.
3. **Validation**: checks generated queries for schema validity and executable correctness.
4. **Deduplication**: removes structurally redundant queries.
5. **Dataset Construction**: organizes validated queries into datasets for downstream NL2GraphQL research.

## Repository Structure

```
autographql/
├── src/                    # Core GraphQL parsing and query generation
├── schemas/                # GraphQL schemas used for generation
├── scripts/                # Command-line generation scripts
├── datasets/               # Train and test datasets
├── docs/
│   ├── autographql.pdf     # Paper
│   └── figures/
│       └── toolkit.png     # Framework overview
└── website/
```

## Running Locally

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn website.backend.main:app --reload --port 8000
```

### Frontend

```bash
cd website/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### CLI

```bash
source venv/bin/activate
python scripts/generate_queries.py --schema academic --category all --count 5
```

## Datasets

See `datasets/README.md` for download and placement instructions.

## Citation

Please cite the repo if you think our work is helpful to you.

```bibtex
@inproceedings{autographql2026,
  title={},
  author={},
  booktitle={},
  year={2026}
}
```

## License

MIT License
