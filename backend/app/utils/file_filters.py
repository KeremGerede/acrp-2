IGNORED_EXTENSIONS = {
    ".lock", ".sum", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    ".pdf", ".zip", ".tar", ".gz", ".min.js", ".min.css",
}

IGNORED_PATHS = {
    "node_modules/", ".git/", "dist/", "build/", "__pycache__/",
    ".venv/", "venv/", ".env", "vendor/",
}


def should_review_file(file_path: str) -> bool:
    lower = file_path.lower()
    for ignored in IGNORED_PATHS:
        if ignored in lower:
            return False
    for ext in IGNORED_EXTENSIONS:
        if lower.endswith(ext):
            return False
    return True


def filter_files(files: list) -> list:
    return [f for f in files if should_review_file(f.get("filename", f) if isinstance(f, dict) else f)]
