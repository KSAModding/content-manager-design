# content-manager-design

Design process and specification for a Kitten Space Agency content manager and content index.

## Where to start

- [CHARTER.md](CHARTER.md) for the scope, the (non-)goals, and how decisions are made.
- [Pre-RFC discussions](https://github.com/KSAModding/content-manager-design/discussions/categories/pre-rfc) for what is currently being argued about.
- `research/` Read this before proposing anything.
- [DECISIONS.md](DECISIONS.md) for what has been settled so far.
- [CONTRIBUTING.md](CONTRIBUTING.md) if you want to write something.

## Layout

| | |
|---|---|
| `rfcs/` | Proposals and the decisions they became. Never edited after acceptance. |
| `spec/` | The living specification, written from accepted RFCs. |
| `research/` | Research |
| `tools/` | Small scripts to keep the repository clean. |

## License

Documentation and specification text is licensed under [CC BY 4.0](LICENSE).
That means everything under `rfcs/`, `spec/`, and `research/`, plus the Markdown files at the repository root.
Attribute as "KSA Modding, content-manager-design" with a link to this repository.

Code, example metadata, schemas, and configuration is licensed under [MIT](LICENSE-MIT).
That means everything under `.github/`, `tools/`, and `examples/`, plus any file carrying an `SPDX-License-Identifier: MIT` header.

Anything not clearly covered by either is CC BY 4.0.
