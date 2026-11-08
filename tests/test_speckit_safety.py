"""Regression scenarios for real upstream feature-context behavior."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FeatureContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'.specify/scripts/python', self.root/'.specify/scripts/python',
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'.specify/templates', self.root/'.specify/templates')
        (self.root/'pipeline').mkdir()
        shutil.copy2(ROOT/'pipeline/speckit_readonly.py', self.root/'pipeline/speckit_readonly.py')
        self.feature = self.root/'specs/selected'
        self.feature.mkdir(parents=True)
        (self.feature/'spec.md').write_text('# Existing spec\nFR-012: keep this\n', encoding='utf-8')
        self.pointer = self.root/'.specify/feature.json'
        self.env = {k:v for k,v in os.environ.items() if not k.startswith('SPECIFY_')}
        self.env.update(SPECIFY_FEATURE_DIRECTORY='specs/selected', PYTHONUTF8='1')

    def run_script(self, script, *args):
        return subprocess.run([sys.executable, str(self.root/script), *args],
                              cwd=self.root, env=self.env, capture_output=True, text=True,
                              encoding='utf-8', timeout=30)

    def complete_feature(self):
        for name in ['plan.md','tasks.md']:
            (self.feature/name).write_text('# Content\n', encoding='utf-8')

    def test_upstream_reproduces_pointer_write(self):
        self.complete_feature()
        result = self.run_script('.specify/scripts/python/check_prerequisites.py','--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.pointer.read_text())['feature_directory'],'specs/selected')

    def test_readonly_does_not_create_missing_pointer(self):
        self.complete_feature()
        result = self.run_script('pipeline/speckit_readonly.py','--json',
                                 '--require-spec','--require-tasks','--include-tasks')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.pointer.exists())

    def test_readonly_preserves_different_pointer(self):
        self.complete_feature()
        original = b'{"feature_directory":"specs/other"}\n'
        self.pointer.write_bytes(original)
        result = self.run_script('pipeline/speckit_readonly.py','--json',
                                 '--require-spec','--require-tasks')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pointer.read_bytes(), original)
        self.assertEqual(Path(json.loads(result.stdout)['FEATURE_DIR']), self.feature)
        self.assertNotIn('SPECIFY_FEATURE_NO_PERSIST', self.env)

    def test_missing_required_plan_still_fails_without_writing(self):
        result = self.run_script('pipeline/speckit_readonly.py','--json','--require-spec')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('plan.md not found',result.stderr)
        self.assertFalse(self.pointer.exists())

    def test_missing_required_tasks_still_fails_without_writing(self):
        (self.feature/'plan.md').write_text('# Plan\n', encoding='utf-8')
        result = self.run_script('pipeline/speckit_readonly.py','--json','--require-tasks')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('tasks.md not found',result.stderr)
        self.assertFalse(self.pointer.exists())

    def test_checklist_paths_and_template_work_with_spec_only(self):
        original = (self.feature/'spec.md').read_bytes()
        paths = self.run_script('pipeline/speckit_readonly.py','--json','--paths-only')
        self.assertEqual(paths.returncode, 0, paths.stderr)
        self.assertTrue(Path(json.loads(paths.stdout)['FEATURE_SPEC']).is_file())
        template = self.run_script('.specify/scripts/python/resolve_template.py',
                                   'checklist-template','--json')
        self.assertEqual(template.returncode, 0, template.stderr)
        self.assertTrue(json.loads(template.stdout)['TEMPLATE_CONTENT'].strip())
        self.assertEqual((self.feature/'spec.md').read_bytes(), original)
        self.assertFalse((self.feature/'plan.md').exists())
        self.assertFalse(self.pointer.exists())

if __name__ == '__main__':
    unittest.main()
