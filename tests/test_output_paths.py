"""Exercise external, explicit and legacy paths through the real CLI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class OutputPathsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'repo'
        self.work = Path(self.temp.name)/'work'
        (self.root/'pipeline').mkdir(parents=True)
        for name in ['common.py','diagnose_runtime.py','cut_media.py']:
            shutil.copy2(ROOT/'pipeline'/name,self.root/'pipeline'/name)
        (self.root/'local').mkdir()
        (self.root/'local/media.json').write_text(json.dumps(
            {'video':str(Path(self.temp.name)/'sources/original.mp4'),
             'audio':str(Path(self.temp.name)/'sources/ukrainian.webm')}), encoding='utf-8')
        self.env = os.environ.copy()
        self.env.update(DUB_WORK_DIR=str(self.work),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')

    def run_cli(self, name, *args):
        return subprocess.run([sys.executable,'-B',str(self.root/'pipeline'/name),*args],
            cwd=self.root,env=self.env,capture_output=True,text=True,encoding='utf-8',timeout=100)

    def preview(self,*args):
        return self.run_cli('cut_media.py','--id','sample','--start','00:00:00.000',
                            '--end','00:00:01.000',*args)

    def test_external_preview_creates_nothing(self):
        result=self.preview()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(str(self.work/'exports/sample.mp4'),result.stdout)
        self.assertFalse(self.work.exists())
        self.assertFalse((self.root/'media').exists())
        self.assertIn('-n ',result.stdout)

    def test_explicit_clip_directory_wins(self):
        chosen=Path(self.temp.name)/'chosen'
        result=self.preview('--output-dir',str(chosen))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(str(chosen/'sample.mp4'),result.stdout)
        self.assertFalse(chosen.exists())

    def test_legacy_clip_default_without_environment(self):
        self.env.pop('DUB_WORK_DIR')
        result=self.preview()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(str(self.root/'media/scenes/sample.mp4'),result.stdout)

    def test_persistent_config_without_session_environment(self):
        self.env.pop('DUB_WORK_DIR')
        config=self.root/'local/media.json'
        data=json.loads(config.read_text('utf-8'))
        data['work_dir']=str(self.work)
        config.write_text(json.dumps(data),encoding='utf-8')
        result=self.preview()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(str(self.work/'exports/sample.mp4'),result.stdout)
        self.assertFalse(self.work.exists())

    def test_external_diagnostic_report(self):
        result=self.run_cli('diagnose_runtime.py')
        self.assertEqual(result.returncode,0,result.stderr)
        report=self.work/'reports/runtime.json'
        self.assertIn('cpu',json.loads(report.read_text('utf-8')))
        self.assertFalse((self.root/'local/runtime.json').exists())

    def test_explicit_report_path_wins(self):
        chosen=Path(self.temp.name)/'chosen/report.json'
        result=self.run_cli('diagnose_runtime.py','--output',str(chosen))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(chosen.is_file())
        self.assertFalse(self.work.exists())

    def test_bad_workspace_fails_before_output(self):
        for value in ['relative',str(self.root/'cache')]:
            self.env['DUB_WORK_DIR']=value
            result=self.preview()
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((self.root/'cache').exists())

    def test_source_directories_are_protected(self):
        sources=Path(self.temp.name)/'sources'
        sources.mkdir()
        original=sources/'original.mp4'
        original.write_bytes(b'original media')
        for path in [sources, sources/'nested']:
            self.env['DUB_WORK_DIR']=str(path)
            self.assertNotEqual(self.preview().returncode,0)
        self.env['DUB_WORK_DIR']=str(self.work)
        self.assertNotEqual(self.preview('--output-dir',str(sources)).returncode,0)
        for path in [original,sources/'report.json']:
            result=self.run_cli('diagnose_runtime.py','--output',str(path))
            self.assertNotEqual(result.returncode,0)
        self.assertEqual(original.read_bytes(),b'original media')
        self.assertEqual(list(sources.iterdir()),[original])

    def test_explicit_outputs_cannot_write_checkout(self):
        config=self.root/'local/media.json'
        before=config.read_bytes()
        self.assertNotEqual(self.run_cli('diagnose_runtime.py','--output',str(config)).returncode,0)
        self.assertEqual(config.read_bytes(),before)
        self.assertNotEqual(self.preview('--output-dir',str(self.root/'generated')).returncode,0)
        self.assertFalse((self.root/'generated').exists())

if __name__=='__main__':
    unittest.main()
