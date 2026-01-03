# Chula license
Automate bot to borrow chula license

## Dependencies
- [uv](https://docs.astral.sh/uv/)

## Set up
1. Install dependencies

```bash
uv sync
```

## manually run a script

```bash
Usage: python main.py <license> [<license> ...]

License:
  foxit | zoom | adobe

Example:
  python main.py foxit zoom
```

## or use cronjob (linux)
1. open crontab editor

```bash
crontab -e
```

2. Add this line

```
0 * * * * cd <path-to-project> && .venv/bin/python3 main.py <license> [<license> ...] >> log 2>&1
```
