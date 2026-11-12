"""
Master Test Runner.
Executes both test suites (Problem 1 & Problem 2) with proper PYTHONPATH isolation.
"""
import sys
import os
import subprocess

def run_tests():
    base_env = os.environ.copy()

    print("=" * 70)
    print(" RUNNING PROBLEM 1: AGENT SOCIAL NETWORK TEST SUITE")
    print("=" * 70)
    env_p1 = base_env.copy()
    env_p1["PYTHONPATH"] = "problem1_agent_social_network"
    cmd_p1 = [sys.executable, "-m", "pytest", "problem1_agent_social_network/tests", "-v"]
    res1 = subprocess.run(cmd_p1, env=env_p1)

    print("\n" + "=" * 70)
    print(" RUNNING PROBLEM 2: LINUX HARDWARE ASSISTANT TEST SUITE")
    print("=" * 70)
    env_p2 = base_env.copy()
    env_p2["PYTHONPATH"] = "problem2_linux_hardware_assistant"
    cmd_p2 = [sys.executable, "-m", "pytest", "problem2_linux_hardware_assistant/tests", "-v"]
    res2 = subprocess.run(cmd_p2, env=env_p2)

    if res1.returncode == 0 and res2.returncode == 0:
        print("\n" + "=" * 70)
        print(" [SUCCESS] ALL 27 TESTS ACROSS BOTH PROBLEMS PASSED 100%!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more test suites failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
