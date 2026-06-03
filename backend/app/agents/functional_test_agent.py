import logging
import subprocess
import shlex
from typing import Optional
from sqlalchemy.orm import Session
from app.tools.functional_test_report_tool import parse_exit_code_result, summarize_with_llm
from app.services.agent_step_service import log_step

logger = logging.getLogger(__name__)

TEST_TIMEOUT = 300  # 5 minutes


def run_functional_tests(
    db: Session,
    tenant_id: int,
    integration_id: int,
    functional_test_run_id: int,
    test_command: str,
    working_directory: Optional[str] = None,
) -> dict:
    log_step(db, tenant_id, "FunctionalTestAgent", "functional_test_runner", "start_test", "running",
             integration_id=integration_id, functional_test_run_id=functional_test_run_id,
             input_summary=f"command={test_command[:100]}, cwd={working_directory}")

    try:
        cmd = shlex.split(test_command)
        proc = subprocess.run(
            cmd,
            cwd=working_directory or ".",
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        log_step(db, tenant_id, "FunctionalTestAgent", "functional_test_runner", "start_test", "failed",
                 integration_id=integration_id, functional_test_run_id=functional_test_run_id,
                 error_message="Test timed out after 5 minutes")
        return {
            "result": "failed",
            "total_tests": 0, "passed_tests": 0, "failed_tests": 0,
            "summary": "Tests timed out after 5 minutes.",
            "raw_output": "TIMEOUT",
        }
    except Exception as e:
        logger.error(f"FunctionalTestAgent execution error: {e}")
        log_step(db, tenant_id, "FunctionalTestAgent", "functional_test_runner", "start_test", "failed",
                 integration_id=integration_id, functional_test_run_id=functional_test_run_id,
                 error_message=str(e))
        return {
            "result": "failed",
            "total_tests": 0, "passed_tests": 0, "failed_tests": 0,
            "summary": f"Test execution error: {e}",
            "raw_output": str(e),
        }

    report = parse_exit_code_result(exit_code, stdout, stderr)
    raw_output = (stdout + "\n" + stderr).strip()

    summary = summarize_with_llm(stdout, stderr, report["result"])

    log_step(db, tenant_id, "FunctionalTestAgent", "functional_test_runner", "start_test", "completed",
             integration_id=integration_id, functional_test_run_id=functional_test_run_id,
             output_summary=f"result={report['result']}, exit_code={exit_code}, passed={report['passed_tests']}, failed={report['failed_tests']}")

    return {
        "result": report["result"],
        "total_tests": report["total_tests"],
        "passed_tests": report["passed_tests"],
        "failed_tests": report["failed_tests"],
        "summary": summary,
        "raw_output": raw_output[:10000],
    }
