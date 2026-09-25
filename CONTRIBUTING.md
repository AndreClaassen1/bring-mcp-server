# Contributing

Thanks for your interest in this project.

## Issues

Bug reports and ideas are welcome as issues. Please include what you did, what you expected and what happened instead (without credentials or other personal data).

This is a personal project maintained in spare time. There is no guaranteed support, response time or roadmap, and the unofficial Bring! API can break things at any moment.

## Pull requests

Small, focused pull requests are easiest to review. Please run the tests before submitting:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

## Developer Certificate of Origin (DCO)

Every commit in a contribution must be signed off:

```bash
git commit -s -m "Your message"
```

This adds a `Signed-off-by: Your Name <your.email@example.com>` line to the commit message. With it, you certify that you wrote the change or otherwise have the right to submit it under the project's license (MIT), as described in the Developer Certificate of Origin: https://developercertificate.org

Commits without a sign-off cannot be merged. To add a missing sign-off to your last commit, run `git commit --amend -s`.
