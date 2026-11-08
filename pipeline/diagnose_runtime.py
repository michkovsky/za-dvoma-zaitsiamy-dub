"""Inventory resources without importing heavy ML libraries or installing anything."""
import ctypes
import argparse
import datetime
import importlib.util
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from common import ROOT, external_work_directory, protect_source_directories

def probe(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=20)
        return {'command': command, 'exit_code': result.returncode,
                'output': (result.stdout or result.stderr).strip()[:12000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'command': command, 'error': str(error)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Report JSON path; overrides DUB_WORK_DIR.')
    args = parser.parse_args()
    work = external_work_directory() if args.output is None else None
    target = args.output if args.output is not None else (
        work/'reports/runtime.json' if work else ROOT/'local/runtime.json')
    target = protect_source_directories(target, allow_checkout=args.output is None and work is None)
    if target.suffix.lower() != '.json':
        raise ValueError('Diagnostic output must be a JSON file.')
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = dict.fromkeys(['sse4_2','avx','avx2','fma','f16c'])
    cpu_name = platform.processor()
    if os.name == 'nt':
        feature = ctypes.WinDLL('kernel32', use_last_error=True).IsProcessorFeaturePresent
        feature.argtypes = [ctypes.c_uint]
        feature.restype = ctypes.c_int
        for name, number in [('sse4_2',38),('avx',39),('avx2',40)]:
            flags[name] = bool(feature(number))
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu_name = winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
    extra = None
    if importlib.util.find_spec('cpuinfo'):
        # Isolate optional CPUID probing so it cannot crash the main inventory.
        extra = probe([sys.executable, '-c',
            'import cpuinfo,json; print(json.dumps(cpuinfo.get_cpu_info().get("flags", [])))'])
        if extra.get('exit_code') == 0:
            try:
                detected = json.loads(extra['output'])
                for name in ['fma','f16c']:
                    flags[name] = name in detected
            except (ValueError, TypeError):
                pass
    memory = None
    if os.name == 'nt':
        class Memory(ctypes.Structure):
            _fields_ = [('length',ctypes.c_ulong),('load',ctypes.c_ulong)] + [
                (name,ctypes.c_ulonglong) for name in ['total','available','page_total',
                'page_available','virtual_total','virtual_available','extended']]
        status = Memory()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory = {'total_bytes':status.total,'available_bytes':status.available}
    tools = {name: probe([name,flag]) for name,flag in [
        ('ffmpeg','-version'),('ffprobe','-version'),('git','--version'),('gh','--version')]}
    gpu = probe(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.free',
                 '--format=csv,noheader,nounits'])
    report = {'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'os':platform.platform(), 'architecture':platform.machine(),
        'python':sys.version,'python_executable':sys.executable,
        'cpu':{'name':cpu_name,'logical_processors':os.cpu_count(),
               'features':flags,'optional_cpuinfo_probe':extra},
        'memory':memory,'workspace_disk':shutil.disk_usage(target.parent)._asdict(),
        'gpu_inventory':gpu,'tools':tools,
        'qualification':'Inventory only. null means unknown. Test each actual operation separately.'}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=target.parent, prefix='.runtime-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f'Saved {target}. CPU instruction availability:',flags)
    if any(value is None for value in flags.values()):
        print('Some CPU features are unknown; verify before selecting binaries that require them.')

if __name__ == '__main__':
    main()
