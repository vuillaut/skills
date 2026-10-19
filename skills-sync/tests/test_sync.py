"""Integration tests: python3 -m unittest discover -s tests -v   (run from the skill folder)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import sync_skill as ss  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.org",
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.org",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, env={**os.environ, **GIT_ENV}).stdout


def skill_md(name, desc="Does a thing. Use it when asked about things.", extra=""):
    return f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n{extra}\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.remote = self.tmp / "remote.git"
        seed = self.tmp / "seed"
        sh("git", "init", "-q", "--bare", "-b", "main", str(self.remote))
        sh("git", "init", "-q", "-b", "main", str(seed))
        (seed / "README.md").write_text("# My Agents Skills")
        (seed / "grilling").mkdir()
        (seed / "grilling" / "SKILL.md").write_text(skill_md("grilling"))
        sh("git", "add", "-A", cwd=seed)
        sh("git", "commit", "-qm", "init", cwd=seed)
        sh("git", "remote", "add", "origin", str(self.remote), cwd=seed)
        sh("git", "push", "-q", "-u", "origin", "main", cwd=seed)
        self.seed = seed
        self.use_machine("A")

    def use_machine(self, label):
        """Each 'machine' has its own state dir, config, skills dir and clone."""
        self.m = self.tmp / label
        self.skills = self.m / "skills"
        self.skills.mkdir(parents=True, exist_ok=True)
        cfgp = self.m / "cfg.json"
        if not cfgp.exists():
            cfgp.write_text(json.dumps({"repo_url": str(self.remote), "source_dirs": [str(self.skills)]}))
        os.environ.update({**GIT_ENV, "SKILLS_SYNC_HOME": str(self.m / "state"), "SKILLS_SYNC_CONFIG": str(cfgp)})
        self.cfgp = cfgp

    def set_cfg(self, **kw):
        c = json.loads(self.cfgp.read_text())
        c.update(kw)
        self.cfgp.write_text(json.dumps(c))

    def mk(self, name, body=None, files=None):
        d = self.skills / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(body or skill_md(name))
        for rel, content in (files or {}).items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(content)
        return d

    def sync(self, *names, **kw):
        return ss.run_sync(ss.resolve_targets(list(names), ss.load_config()), ss.load_config(), **kw)

    def remote_files(self, ref="main"):
        return set(sh("git", "--git-dir", str(self.remote), "ls-tree", "-r", "--name-only", ref).split())

    def remote_log(self):
        return sh("git", "--git-dir", str(self.remote), "log", "--format=%s", "main").splitlines()

    def statuses(self, rep):
        return {n: s for n, s, _ in rep.items}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestDecide(unittest.TestCase):
    def test_truth_table(self):
        d = ss.decide
        self.assertEqual(d("L", None, None, True, False), "ADD")
        self.assertEqual(d("L", "L", "x", True, False), "SAME")
        self.assertEqual(d("L2", "R", "R", True, False), "UPDATE")        # only local changed
        self.assertEqual(d("B", "R2", "B", True, False), "REPO_AHEAD")    # only repo changed
        self.assertEqual(d("L2", "R2", "B", True, False), "DIVERGED")
        self.assertEqual(d("L2", "R2", "B", True, True), "UPDATE")        # force-local
        self.assertEqual(d("L", "R", None, True, False), "UPDATE")        # no baseline, explicit
        self.assertEqual(d("L", "R", None, False, False), "REVIEW")       # no baseline, automatic


class TestBasics(Base):
    def test_add_update_unchanged_flow(self):
        self.mk("foo", files={"scripts/run.sh": "echo hi\n"})
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "ADDED")
        self.assertEqual(rep.exit_code, 0)
        self.assertIn("foo/SKILL.md", self.remote_files())
        self.assertIn("foo/scripts/run.sh", self.remote_files())
        self.assertEqual(self.remote_log()[0], "feat(foo): add skill")
        self.assertIn("pushed", rep.push_status)

        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "UNCHANGED")

        (self.skills / "foo" / "SKILL.md").write_text(skill_md("foo", extra="more"))
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "UPDATED")
        self.assertEqual(self.remote_log()[0], "chore(foo): update skill")

    def test_file_deleted_inside_skill_propagates(self):
        self.mk("foo", files={"a.txt": "a", "b.txt": "b"})
        self.sync("foo")
        (self.skills / "foo" / "b.txt").unlink()
        self.sync("foo")
        self.assertNotIn("foo/b.txt", self.remote_files())
        self.assertIn("foo/a.txt", self.remote_files())

    def test_deleting_a_skill_locally_never_deletes_in_repo(self):
        self.mk("foo")
        self.sync("foo")
        shutil.rmtree(self.skills / "foo")
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "ERROR")
        self.assertIn("foo/SKILL.md", self.remote_files())

    def test_ignored_files_not_copied(self):
        self.mk("foo", files={"__pycache__/x.pyc": "x", ".DS_Store": "x", "foo-workspace/o.txt": "x", "keep.txt": "k"})
        self.sync("foo")
        files = self.remote_files()
        self.assertIn("foo/keep.txt", files)
        self.assertFalse([f for f in files if "pycache" in f or "DS_Store" in f or "workspace" in f])

    def test_exec_bit_preserved(self):
        d = self.mk("foo", files={"scripts/x.sh": "#!/bin/sh\n"})
        os.chmod(d / "scripts/x.sh", 0o755)
        self.sync("foo")
        out = sh("git", "--git-dir", str(self.remote), "ls-tree", "-r", "main", "foo/scripts/x.sh")
        self.assertTrue(out.startswith("100755"))

    def test_dry_run_changes_nothing(self):
        self.mk("foo")
        before = self.remote_log()
        rep = self.sync("foo", dry_run=True)
        self.assertEqual(self.statuses(rep)["foo"], "WOULD-ADDED")
        self.assertEqual(self.remote_log(), before)
        self.assertFalse((self.m / "state" / "repo" / "foo").exists())

    def test_exclude_skills(self):
        self.mk("secretsauce")
        self.set_cfg(exclude_skills=["secretsauce"])
        rep = self.sync("secretsauce")
        self.assertEqual(self.statuses(rep)["secretsauce"], "SKIPPED")
        self.assertNotIn("secretsauce/SKILL.md", self.remote_files())

    def test_unknown_config_key_is_rejected(self):
        self.set_cfg(exclude_skill=["x"])
        with self.assertRaises(ss.SyncError):
            ss.load_config()

    def test_path_resolution_from_hook_paths(self):
        cfg = ss.load_config()
        self.mk("foo", files={"scripts/a.py": ""})
        self.assertEqual(ss.skill_name_for_path(str(self.skills / "foo/scripts/a.py"), cfg)[0], "foo")
        self.assertIsNone(ss.skill_name_for_path("/tmp/elsewhere/file.py", cfg))
        self.assertEqual(ss.find_skill(str(self.skills / "foo" / "SKILL.md"), cfg)[0], "foo")
        self.assertEqual(ss.find_skill("foo", cfg)[1], self.skills / "foo")

    def test_path_traversal_name_rejected(self):
        errs, _, _ = ss.validate_skill("..", self.tmp)
        self.assertTrue(errs)

    def test_readme_index_opt_in(self):
        self.set_cfg(readme_index=True)
        self.mk("foo", body=skill_md("foo", desc="Foo does | pipes. Second sentence."))
        self.sync("foo")
        readme = sh("git", "--git-dir", str(self.remote), "show", "main:README.md")
        self.assertIn("# My Agents Skills", readme)
        self.assertIn("[`foo`](foo/SKILL.md) | Foo does \\| pipes.", readme)
        self.assertIn("[`grilling`]", readme)
        self.assertEqual(self.remote_log()[0], "docs: refresh skills index")
        self.mk("bar")
        self.sync("bar")
        readme = sh("git", "--git-dir", str(self.remote), "show", "main:README.md")
        self.assertEqual(readme.count("skills-index:start"), 1)
        self.assertIn("[`bar`]", readme)


class TestValidation(Base):
    def test_missing_skill_md(self):
        (self.skills / "foo").mkdir()
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "ERROR")

    def test_missing_description_and_frontmatter(self):
        self.mk("bar", body="---\nname: bar\n---\nbody\n")
        self.assertEqual(self.statuses(self.sync("bar"))["bar"], "ERROR")
        self.mk("baz", body="no frontmatter\n")
        self.assertEqual(self.statuses(self.sync("baz"))["baz"], "ERROR")

    def test_name_differing_from_folder_is_only_a_warning(self):
        self.mk("pptx-slide", body=skill_md("academic-pptx"))        # real-world case from the user's repo
        rep = self.sync("pptx-slide")
        self.assertEqual(self.statuses(rep)["pptx-slide"], "ADDED")
        self.assertTrue(any("differs from folder" in d for d in rep.details))

    def test_folded_multiline_description(self):
        self.mk("foo", body="---\nname: foo\ndescription: >\n  Line one\n  line two.\n---\nx\n")
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "ADDED")

    def test_missing_name_is_only_a_warning(self):
        self.mk("foo", body="---\ndescription: ok\n---\nx\n")
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "ADDED")
        self.assertTrue(any("no `name`" in d for d in rep.details))


class TestSecretScan(Base):
    TOKEN = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"

    def test_token_blocks_and_is_never_echoed(self):
        self.mk("foo", files={"notes.md": f"use {self.TOKEN} here\n"})
        before = self.remote_log()
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "BLOCKED")
        self.assertEqual(rep.exit_code, 2)
        self.assertNotIn(self.TOKEN, rep.render())
        self.assertIn("notes.md:1", rep.render())
        self.assertEqual(self.remote_log(), before)
        self.assertFalse((self.m / "state" / "repo" / "foo").exists())

    def test_ignore_findings_override(self):
        self.mk("foo", files={"notes.md": f"{self.TOKEN}\n"})
        rep = self.sync("foo", ignore_findings=True)
        self.assertEqual(self.statuses(rep)["foo"], "ADDED")

    def test_various_patterns(self):
        cases = {
            "-----BEGIN OPENSSH PRIVATE KEY-----": "private key",
            "AKIAABCDEFGHIJKLMNOP": "AWS access key",
            'api_key = "abcd1234efgh5678"': "hard-coded secret",
            "client_secret: 'Zm9vYmFyYmF6cXV4'": "hard-coded secret",
            "git clone https://bob:hunter2pw@github.com/x/y": "URL with embedded credentials",
            "sk-ant-api03-abcdefghijklmnopqrstuvwxyz": "Anthropic API key",
        }
        for text, label in cases.items():
            with self.subTest(label=label):
                (self.tmp / "s").mkdir(exist_ok=True)
                f = self.tmp / "s" / "f.md"
                f.write_text(text + "\n")
                labels = [x[3] for x in ss.scan(self.tmp / "s", ss.load_config(), ss.snapshot(self.tmp / "s"))]
                self.assertIn(label, labels)

    def test_no_false_positives_on_normal_docs(self):
        ok = ['password: "<your-password-here>"', 'token = "${GITHUB_TOKEN}"', "api_key = os.environ['KEY']",
              'secret: "xxxxxxxxxxxxxxxxxxxx"', "See https://github.com/vuillaut/skills for details",
              "ssh git@github.com:vuillaut/skills.git", 'password = "changeme-please-now"']
        (self.tmp / "s").mkdir(exist_ok=True)
        (self.tmp / "s" / "f.md").write_text("\n".join(ok) + "\n")
        blocking = [x for x in ss.scan(self.tmp / "s", ss.load_config(), ss.snapshot(self.tmp / "s")) if x[0] == "block"]
        self.assertEqual(blocking, [])

    def test_sensitive_filenames(self):
        self.mk("foo", files={".env": "A=1", "x.pem": "k"})
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "BLOCKED")
        self.mk("bar", files={".env.example": "A=<value>"})
        self.assertEqual(self.statuses(self.sync("bar"))["bar"], "ADDED")

    def test_large_file_blocked(self):
        self.set_cfg(max_file_mb=1)
        d = self.mk("foo")
        (d / "big.bin").write_bytes(b"\x00" * (2 * 1024 * 1024))
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "BLOCKED")

    def test_extra_deny_patterns_and_home_path_warning(self):
        self.set_cfg(extra_deny_patterns=[r"intranet\.corp"])
        self.mk("foo", files={"a.md": "see http://intranet.corp/wiki\n"})
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "BLOCKED")
        self.mk("bar", files={"a.md": "cd /home/alice/work\n"})
        rep = self.sync("bar")
        self.assertEqual(self.statuses(rep)["bar"], "ADDED")
        self.assertTrue(any("home path" in d for d in rep.details))

    def test_symlink_is_warning_not_followed(self):
        outside = self.tmp / "outside.txt"
        outside.write_text("TOP SECRET CONTENT")
        d = self.mk("foo")
        os.symlink(outside, d / "link.txt")
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "ADDED")
        out = sh("git", "--git-dir", str(self.remote), "show", "main:foo/link.txt")
        self.assertNotIn("TOP SECRET", out)


class TestTwoMachines(Base):
    def test_repo_ahead_is_not_overwritten_and_pull_works(self):
        self.mk("foo", files={"v.txt": "1"})
        self.sync("foo")                                    # machine A baseline
        # machine B updates foo in the repo
        sh("git", "clone", "-q", str(self.remote), str(self.tmp / "B"))
        (self.tmp / "B" / "foo" / "v.txt").write_text("2-from-B")
        sh("git", "commit", "-qam", "B edit", cwd=self.tmp / "B")
        sh("git", "push", "-q", cwd=self.tmp / "B")
        # machine A runs a sync with its stale-but-unchanged local copy
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "REPO_AHEAD")
        self.assertEqual(rep.exit_code, 2)
        self.assertEqual((self.skills / "foo" / "v.txt").read_text(), "1")
        self.assertEqual(sh("git", "--git-dir", str(self.remote), "show", "main:foo/v.txt"), "2-from-B")
        rep = ss.run_pull(ss.resolve_targets(["foo"], ss.load_config()), ss.load_config())
        self.assertEqual(self.statuses(rep)["foo"], "PULLED")
        self.assertEqual((self.skills / "foo" / "v.txt").read_text(), "2-from-B")
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "UNCHANGED")

    def test_diverged_then_force_local(self):
        self.mk("foo", files={"v.txt": "1"})
        self.sync("foo")
        sh("git", "clone", "-q", str(self.remote), str(self.tmp / "B"))
        (self.tmp / "B" / "foo" / "v.txt").write_text("B")
        sh("git", "commit", "-qam", "B edit", cwd=self.tmp / "B")
        sh("git", "push", "-q", cwd=self.tmp / "B")
        (self.skills / "foo" / "v.txt").write_text("A")
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "DIVERGED")
        self.assertEqual(sh("git", "--git-dir", str(self.remote), "show", "main:foo/v.txt"), "B")
        rep = self.sync("foo", force_local=True)
        self.assertEqual(self.statuses(rep)["foo"], "UPDATED")
        self.assertEqual(sh("git", "--git-dir", str(self.remote), "show", "main:foo/v.txt"), "A")

    def test_pull_refuses_to_clobber_unsynced_local_changes(self):
        self.mk("foo", files={"v.txt": "1"})
        self.sync("foo")
        (self.skills / "foo" / "v.txt").write_text("local-edit")
        rep = ss.run_pull(ss.resolve_targets(["foo"], ss.load_config()), ss.load_config())
        self.assertEqual(self.statuses(rep)["foo"], "DIVERGED")
        self.assertEqual((self.skills / "foo" / "v.txt").read_text(), "local-edit")

    def test_existing_remote_skill_without_baseline(self):
        # fresh machine with a different 'grilling' than the repo
        self.mk("grilling", body=skill_md("grilling", extra="local variant"))
        rep = self.sync("grilling", explicit=False)
        self.assertEqual(self.statuses(rep)["grilling"], "REVIEW")           # automatic: never guess
        self.assertNotIn("local variant", sh("git", "--git-dir", str(self.remote), "show", "main:grilling/SKILL.md"))
        rep = self.sync("grilling", explicit=True)                           # explicit: local wins
        self.assertEqual(self.statuses(rep)["grilling"], "UPDATED")

    def test_concurrent_remote_commit_between_fetch_and_push_is_retried(self):
        self.mk("foo")
        self.sync("foo")
        self.mk("bar")
        orig_push = ss.push
        state = {"n": 0}

        def racing_push(repo):
            if state["n"] == 0:
                state["n"] = 1
                sh("git", "clone", "-q", str(self.remote), str(self.tmp / "B"))
                (self.tmp / "B" / "other.txt").write_text("x")
                sh("git", "add", "-A", cwd=self.tmp / "B")
                sh("git", "commit", "-qm", "race", cwd=self.tmp / "B")
                sh("git", "push", "-q", cwd=self.tmp / "B")
            return orig_push(repo)
        ss.push = racing_push
        try:
            rep = self.sync("bar")
        finally:
            ss.push = orig_push
        self.assertIn("pushed", rep.push_status, rep.render())
        self.assertIn("bar/SKILL.md", self.remote_files())
        self.assertIn("other.txt", self.remote_files())


class TestFailureModes(Base):
    def test_offline_commits_locally_then_recovers(self):
        self.mk("foo")
        self.sync("foo", dry_run=True)                       # forces clone creation
        self.sync("foo", no_push=True)                       # commit locally, no push
        self.assertNotIn("foo/SKILL.md", self.remote_files())
        # break the remote
        os.rename(self.remote, self.tmp / "remote.gone")
        self.mk("bar")
        rep = self.sync("bar")
        self.assertEqual(rep.exit_code, 3, rep.render())
        self.assertTrue(rep.push_status.startswith("failed"))
        os.rename(self.tmp / "remote.gone", self.remote)
        rep = self.sync("bar")                               # nothing new locally, but pending commits get pushed
        self.assertIn("pushed", rep.push_status, rep.render())
        self.assertTrue({"foo/SKILL.md", "bar/SKILL.md"} <= self.remote_files())

    def test_commit_failure_rolls_back_clone(self):
        self.mk("foo")
        self.sync("foo", dry_run=True)
        repo = self.m / "state" / "repo"
        hook = repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho nope >&2\nexit 1\n")
        os.chmod(hook, 0o755)
        rep = self.sync("foo")
        self.assertEqual(self.statuses(rep)["foo"], "ERROR")
        self.assertEqual(sh("git", "status", "--porcelain", cwd=repo).strip(), "")
        self.assertFalse((repo / "foo").exists())
        hook.unlink()
        self.assertEqual(self.statuses(self.sync("foo"))["foo"], "ADDED")   # recovers on next run

    def test_dirty_clone_is_refused_not_destroyed(self):
        self.mk("foo")
        self.sync("foo", dry_run=True)
        repo = self.m / "state" / "repo"
        (repo / "manual-note.txt").write_text("keep me")
        rep = self.sync("foo")
        self.assertEqual(rep.exit_code, 1)
        self.assertTrue((repo / "manual-note.txt").exists())

    def test_wrong_remote_in_config(self):
        self.mk("foo")
        self.sync("foo", dry_run=True)
        self.set_cfg(repo_url="https://github.com/someone-else/skills.git")
        self.assertEqual(self.sync("foo").exit_code, 1)

    def test_credentials_are_redacted(self):
        self.assertNotIn("hunter2", ss.redact("fatal: unable to access 'https://bob:hunter2@github.com/x/y/'"))

    def test_url_normalisation(self):
        n = ss.norm_url
        self.assertEqual(n("https://github.com/vuillaut/skills.git"), n("git@github.com:vuillaut/skills"))
        self.assertNotEqual(n("https://github.com/a/skills"), n("https://github.com/b/skills"))


class TestHook(Base):
    def run_hook(self, payload):
        p = subprocess.run([sys.executable, str(SCRIPTS / "hook.py")], input=json.dumps(payload),
                           capture_output=True, text=True, env=os.environ.copy())
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_post_tool_use_marks_then_stop_syncs_once(self):
        self.mk("foo")
        out = self.run_hook({"hook_event_name": "PostToolUse", "tool_name": "Write", "cwd": str(self.tmp),
                             "tool_input": {"file_path": str(self.skills / "foo" / "SKILL.md")}})
        self.assertEqual(out, "")
        self.assertTrue((self.m / "state" / "dirty" / "foo").exists())
        out = self.run_hook({"hook_event_name": "Stop", "cwd": str(self.tmp), "stop_hook_active": False})
        msg = json.loads(out)["systemMessage"]
        self.assertIn("ADDED", msg)
        self.assertIn("foo/SKILL.md", self.remote_files())
        self.assertFalse((self.m / "state" / "dirty" / "foo").exists())
        self.assertEqual(self.run_hook({"hook_event_name": "Stop", "cwd": str(self.tmp)}), "")   # silent when idle

    def test_unrelated_edits_are_ignored(self):
        self.run_hook({"hook_event_name": "PostToolUse", "cwd": str(self.tmp),
                       "tool_input": {"file_path": "/somewhere/else/main.py"}})
        self.assertFalse((self.m / "state" / "dirty").exists())

    def test_stop_catches_bash_edits_of_tracked_skills_but_not_new_untracked_ones(self):
        self.mk("foo")
        self.sync("foo")
        (self.skills / "foo" / "SKILL.md").write_text(skill_md("foo", extra="edited via sed"))   # no PostToolUse
        self.mk("brandnew")                                                                       # never announced
        out = self.run_hook({"hook_event_name": "Stop", "cwd": str(self.tmp)})
        self.assertIn("UPDATED", out)
        files = self.remote_files()
        self.assertNotIn("brandnew/SKILL.md", files)
        self.assertIn("edited via sed", sh("git", "--git-dir", str(self.remote), "show", "main:foo/SKILL.md"))

    def test_hook_reports_blocked_secret(self):
        self.mk("foo", files={"n.md": "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"})
        self.run_hook({"hook_event_name": "PostToolUse", "cwd": str(self.tmp),
                       "tool_input": {"file_path": str(self.skills / "foo" / "n.md")}})
        out = self.run_hook({"hook_event_name": "Stop", "cwd": str(self.tmp)})
        self.assertIn("BLOCKED", json.loads(out)["systemMessage"])
        self.assertNotIn("ghp_", out)

    def test_hook_never_crashes_on_garbage(self):
        p = subprocess.run([sys.executable, str(SCRIPTS / "hook.py")], input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


class TestCLI(Base):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "sync_skill.py"), *args], capture_output=True, text=True,
                              env=os.environ.copy(), cwd=self.tmp)

    def test_cli_add_status_exit_codes(self):
        self.mk("foo")
        p = self.cli("--status")
        self.assertIn("NEW", p.stdout)
        p = self.cli("foo")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ADDED", p.stdout)
        self.assertIn("PUSHED", p.stdout)
        self.assertIn("IN-SYNC", self.cli("--status").stdout)
        (self.skills / "foo" / "SKILL.md").write_text(skill_md("foo", extra="x"))
        self.assertIn("MODIFIED", self.cli("--status").stdout)
        self.assertEqual(self.cli("--all-tracked").returncode, 0)
        self.assertIn("REPO-ONLY", self.cli("--status").stdout)               # 'grilling' exists only in the repo
        self.assertEqual(self.cli("nonexistent").returncode, 1)

    def test_parallel_runs_are_serialised(self):
        self.mk("a")
        self.mk("b")
        procs = [subprocess.Popen([sys.executable, str(SCRIPTS / "sync_skill.py"), n], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=os.environ.copy()) for n in ("a", "b")]
        outs = [p.communicate()[0] for p in procs]
        self.assertEqual([p.returncode for p in procs], [0, 0], outs)
        self.assertTrue({"a/SKILL.md", "b/SKILL.md"} <= self.remote_files())


if __name__ == "__main__":
    unittest.main()
