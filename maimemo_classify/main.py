import argparse
import subprocess
import shutil
import os
from pathlib import Path


def force_rmtree(path):
    def onerror(func, path, exc_info):
        os.chmod(path, 0o777)
        func(path)
    shutil.rmtree(path, onerror=onerror)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()

    target_dir = Path(__file__).parent / "exported"

    update_success = False

    if args.update:
        repo_dir = Path(__file__).parent / "temp_repo"

        if repo_dir.exists():
            force_rmtree(repo_dir)

        subprocess.run(["git", "clone", "--filter=blob:none", "--sparse", "--depth=1",
                       "https://github.com/busiyiworld/maimemo-export.git", str(repo_dir)], check=True)
        subprocess.run(["git", "sparse-checkout", "set", "exported/word"], cwd=str(repo_dir), check=True)
        # subprocess.run(["git", "checkout"], cwd=str(repo_dir), check=True)

        word_src = repo_dir / "exported" / "word"
        if target_dir.exists():
            force_rmtree(target_dir)
        if word_src.exists():
            shutil.copytree(word_src, target_dir)
            update_success = True

        force_rmtree(repo_dir)

    if update_success or not args.update:
        print("占位行为执行")


if __name__ == "__main__":
    main()
