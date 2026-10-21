"""Create the same fresh task layout for each project; no inference or publishing."""
import argparse
from uir_common.paths import PROJECTS, create_task

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=sorted(PROJECTS))
    parser.add_argument("task")
    args = parser.parse_args()
    print(create_task(args.project, args.task))
