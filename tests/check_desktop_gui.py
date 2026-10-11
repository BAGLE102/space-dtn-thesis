"""Explicit desktop GUI smoke checks; not part of headless unittest discovery."""
import json
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments.gui import ExperimentGUI, DEFAULT_SUITE, curve_value, enable_dpi_awareness


def main():
    output = ROOT/'output/visualizations/desktop_gui_v01_20261011'
    output.mkdir(parents=True, exist_ok=True)
    enable_dpi_awareness()
    root = tk.Tk()
    app = ExperimentGUI(root, DEFAULT_SUITE)
    errors = []
    root.report_callback_exception = lambda kind,value,traceback:errors.append(str(value))
    steps = 0
    for ci,run in enumerate(app.data):
        app.case_box.current(ci)
        app.change_case()
        for bi,record in enumerate(run['records']):
            app.bundle_box.current(bi)
            app.change_bundle()
            for step,event in enumerate(app.events()):
                app.step=step
                app.draw()
                root.update()
                assert app.status.get()
                assert len(app.queue.get_children()) == len(event.get('queue_after',[]))
                steps += 1
    app.case_box.current(0)
    app.change_case()
    app.bundle_box.current(1)
    app.change_bundle()
    failure = next(i for i,e in enumerate(app.events()) if e.get('reason')=='BUFFER')
    app.step = failure
    app.draw()
    root.update()
    from PIL import ImageGrab
    def screenshot(name):
        root.lift()
        root.update()
        root.after(100)
        root.update()
        x,y = root.winfo_rootx(),root.winfo_rooty()
        ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(output/name)
    screenshot('gui_search.png')
    app.play()
    deadline = time.monotonic()+.2
    while time.monotonic()<deadline:
        root.update()
        time.sleep(.01)
    assert app.step == failure+1
    app.pause()
    app.mode_box.current(1)
    app.change_mode()
    app.time = 8
    app.draw()
    for node,expected in [('B',4),('D',4)]:
        assert sum(curve_value(c,8) for c in app.run['occupancy'].get(node,[]))==expected
    assert sum(curve_value(c,8.25) for c in app.run['occupancy'].get('D',[]))==0
    app.time=7.5
    app.draw()
    screenshot('gui_schedule.png')
    app.start_run()
    deadline=time.monotonic()+30
    while app.process and time.monotonic()<deadline:
        root.update()
        time.sleep(.02)
    assert app.process is None, 'Worker did not finish'
    assert len(app.data)==1 and app.data[0]['records'][1]['arrival']=='12'
    assert (app.output/'report'/'replay_check.json').exists()
    assert app.output.resolve().is_relative_to((ROOT/'output/experiments/gui_runs').resolve())
    archive = ROOT/'.codex-ppt-build/gui_smoke_runs'/app.output.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    app.output.rename(archive)
    worker_output=str(archive.relative_to(ROOT))
    # Exercise cancellation on a dedicated owned child, not a user's process.
    with tempfile.TemporaryDirectory() as tmp:
        app.output=Path(tmp)
        app.log=(Path(tmp)/'child.log').open('w')
        app.process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],
            stdout=app.log,stderr=app.log,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        app.cancel_run()
        assert (Path(tmp)/'gui_cancelled.json').exists()
    assert not errors, errors
    report=dict(cases=9,queries=18,steps_checked=steps,tk_callback_errors=errors,
        playback_checked=True,worker_run_checked=True,cancellation_checked=True,
        buffer_event_peak_checked=True,worker_output=worker_output)
    (output/'gui_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report))
    app.close()


if __name__=='__main__':
    main()
