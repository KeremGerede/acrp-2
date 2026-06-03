import re
from typing import Optional
from app.services.llm_service import llm_service


def parse_exit_code_result(exit_code: int, stdout: str, stderr: str) -> dict:
    """Build a basic report from subprocess output."""
    result = "success" if exit_code == 0 else "failed"

    # Try to parse pytest-style summary
    total = passed = failed = 0
    summary_match = re.search(r"(\d+) passed", stdout + stderr)
    failed_match = re.search(r"(\d+) failed", stdout + stderr)
    error_match = re.search(r"(\d+) error", stdout + stderr)
    collected_match = re.search(r"collected (\d+) item", stdout + stderr)

    if summary_match:
        passed = int(summary_match.group(1))
    if failed_match:
        failed += int(failed_match.group(1))
    if error_match:
        failed += int(error_match.group(1))
    if collected_match:
        total = int(collected_match.group(1))
    if total == 0:
        total = passed + failed

    return {
        "result": result,
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "exit_code": exit_code,
    }


def summarize_with_llm(stdout: str, stderr: str, result: str) -> Optional[str]:
    try:
        prompt = f"""You are a QA engineer. Summarize the following test output in 2-3 sentences.
Focus on what failed and why if applicable.

Test result: {result}
Output:
{stdout[-3000:]}
{stderr[-1000:] if stderr else ""}

Return only the summary text, no JSON."""
        return llm_service.generate(prompt)
    except Exception:
        return f"Tests {result}. Exit code indicates {'pass' if result == 'success' else 'failure'}."
