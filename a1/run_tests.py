# run_tests.py
import subprocess

OUTPUT_FILE = "results.txt"

with open(OUTPUT_FILE, "w") as out:
    for i in range(1, 11):
        test_file = f"Test{i}.py"
        out.write(f"\n=== {test_file} ===\n")
        out.flush()
        for run in range(10):
            result = subprocess.run(
                ["python", test_file],
                stdout=out,
                stderr=out,
                text=True
            )
            out.write("\n")
            out.flush()


