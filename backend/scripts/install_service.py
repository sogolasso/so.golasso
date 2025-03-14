import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

class AutomationService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SoGolassoAutomation"
    _svc_display_name_ = "Só Golasso Automation Service"
    _svc_description_ = "Runs the Só Golasso scraping and article generation automation"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.process = None

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        """Run the service"""
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PID_INFO,
                ('Service starting', '')
            )
            
            # Get absolute paths
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            venv_python = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
            automation_script = os.path.join(base_dir, 'scripts', 'automate.py')
            
            # Set up environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = base_dir
            env['PATH'] = os.path.join(base_dir, 'venv', 'Scripts') + os.pathsep + env.get('PATH', '')
            
            # Start the automation script with the virtual environment Python
            import subprocess
            self.process = subprocess.Popen(
                [venv_python, automation_script],
                cwd=base_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Wait for the stop event
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")
            
        finally:
            if self.process:
                self.process.terminate()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AutomationService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AutomationService) 