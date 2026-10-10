import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FORK_URL = "https://github.com/jameel-learner/FashionStudio.git"


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class ForkRemoteTests(unittest.TestCase):
    def test_origin_points_to_my_fork(self) -> None:
        self.assertEqual(git("remote", "get-url", "origin"), FORK_URL)

    def test_current_branch_tracks_my_fork(self) -> None:
        upstream = git(
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
        )
        self.assertTrue(
            upstream.startswith("origin/"),
            f"Expected current branch to track origin, got {upstream!r}",
        )


if __name__ == "__main__":
    unittest.main()
