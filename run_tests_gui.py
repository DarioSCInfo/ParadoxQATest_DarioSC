"""Tkinter launcher for the Paradox QA tests."""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


WHITE = "#FFFFFF"
PASTEL_GREEN = "#DFF0D8"
PASTEL_RED = "#F4DADA"
PASTEL_HOVER = "#F2F5F2"


def find_project_root() -> Path:
    if getattr(sys, "frozen", False):
        app_location = Path(sys.executable).resolve()
    else:
        app_location = Path(__file__).resolve()

    for folder in (app_location.parent, *app_location.parents):
        if (
            (folder / "pyproject.toml").is_file()
            and (folder / "2-Auto Test Cases" / "1_Tests").is_dir()
        ):
            return folder

    raise FileNotFoundError("No se encontró la carpeta raíz del proyecto")


PROJECT_ROOT = find_project_root()
TEST_DIRECTORY = PROJECT_ROOT / "2-Auto Test Cases" / "1_Tests"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
SETUP_SCRIPT = PROJECT_ROOT / "setup.cmd"
PYTEST_OPTIONS = ("-v", "-s", "--headed")

TESTS = {
    "Smoke Test": "test_0SmokeTest.py",
    "Test 01": "test_AllGames_01_SearchBar.py",
    "Test 02": "test_AllGames_04_PersonalizedFilters.py",
    "Test 03": "test_Discover_02_CookieSettings.py",
    "Test 04": "test_YourCart_01_EssentialCartFunctions.py",
    "Test 05": "test_YourCart_02_SavingCart.py",
}


class TestRunnerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PARADOX store and shopping Tool")
        self.root.geometry("420x420")
        self.root.resizable(False, False)
        self.buttons: dict[str, tk.Button] = {}
        self.finished_runs: queue.Queue[
            tuple[str, tuple[str, ...], int, dict[str, str]]
        ] = queue.Queue()
        self._build_buttons()

    def _build_buttons(self) -> None:
        container = tk.Frame(self.root, padx=18, pady=18, bg=WHITE)
        container.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            container,
            text="PARADOX store and shopping Tool",
            font=("Segoe UI", 14, "bold"),
            fg="#344038",
            bg=WHITE,
        )
        title.pack(fill=tk.X, pady=(0, 8))
        tk.Frame(container, height=1, bg="#C9CEC9").pack(
            fill=tk.X,
            pady=(0, 12),
        )

        button_grid = tk.Frame(container, bg=WHITE)
        button_grid.pack(fill=tk.BOTH, expand=True)
        button_grid.columnconfigure(0, weight=1, uniform="buttons")
        button_grid.columnconfigure(1, weight=1, uniform="buttons")

        setup_button = self._make_button(
            button_grid,
            text="Setup",
            command=self._launch_setup,
        )
        setup_button.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=6,
            pady=6,
            ipady=8,
        )
        self.buttons["Setup"] = setup_button

        for index, label in enumerate(TESTS):
            button = self._make_button(
                button_grid,
                text=label,
                command=lambda test_label=label: self._launch((test_label,)),
            )
            button.grid(
                row=index // 2 + 1,
                column=index % 2,
                sticky="nsew",
                padx=6,
                pady=6,
                ipady=14,
            )
            self.buttons[label] = button

        full_test = self._make_button(
            button_grid,
            text="Full Test",
            command=lambda: self._launch((*tuple(TESTS)[1:], "Full Test")),
        )
        full_test.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=6,
            pady=6,
            ipady=14,
        )
        self.buttons["Full Test"] = full_test

        for row in range(5):
            button_grid.rowconfigure(row, weight=1, uniform="rows")

    @staticmethod
    def _make_button(
        parent: tk.Misc,
        *,
        text: str,
        command,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            fg="#344038",
            bg=WHITE,
            activebackground=PASTEL_HOVER,
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
            takefocus=True,
        )

    def _launch_setup(self) -> None:
        if not SETUP_SCRIPT.is_file():
            self._show_error(f"No se encontró el archivo de instalación:\n{SETUP_SCRIPT}")
            return

        self._set_button_color("Setup", WHITE)
        for button in self.buttons.values():
            button.configure(state=tk.DISABLED)

        command_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="ascii",
            suffix=".cmd",
            prefix="_paradox_qa_setup_",
            dir=PROJECT_ROOT,
            delete=False,
        )
        command_script = Path(command_file.name)
        status_handle = tempfile.NamedTemporaryFile(
            suffix=".txt",
            prefix="_paradox_qa_setup_status_",
            dir=PROJECT_ROOT,
            delete=False,
        )
        status_file = Path(status_handle.name)
        status_handle.close()
        status_file.unlink(missing_ok=True)
        with command_file:
            command_file.write("@echo off\r\n")
            command_file.write(f'cd /d "{PROJECT_ROOT}"\r\n')
            command_file.write(f'call "{SETUP_SCRIPT}"\r\n')
            command_file.write('set "SETUP_EXIT=%ERRORLEVEL%"\r\n')
            command_file.write(f'echo %SETUP_EXIT% > "{status_file}"\r\n')
            command_file.write("echo.\r\n")
            command_file.write(
                "echo Setup finalizado. Codigo de salida: %SETUP_EXIT%\r\n"
            )
            command_file.write("echo Pulsa una tecla para cerrar esta consola.\r\n")
            command_file.write("pause\r\n")
            command_file.write("exit /b %SETUP_EXIT%\r\n")

        try:
            process = subprocess.Popen(
                ["cmd.exe", "/d", "/c", str(command_script)],
                cwd=PROJECT_ROOT,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except OSError as error:
            command_script.unlink(missing_ok=True)
            status_file.unlink(missing_ok=True)
            for button in self.buttons.values():
                button.configure(state=tk.NORMAL)
            self._show_error(f"No se pudo iniciar el setup:\n{error}")
            return

        threading.Thread(
            target=self._wait_for_setup,
            args=(process, command_script, status_file),
            daemon=True,
        ).start()
        self.root.after(250, self._check_finished_runs)

    def _wait_for_setup(
        self,
        process: subprocess.Popen[bytes],
        command_script: Path,
        status_file: Path,
    ) -> None:
        try:
            while process.poll() is None and (
                not status_file.is_file() or status_file.stat().st_size == 0
            ):
                threading.Event().wait(0.1)
            try:
                return_code = int(status_file.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                return_code = process.poll()
                if return_code is None:
                    return_code = process.wait()
            self.finished_runs.put(("setup", ("Setup",), return_code, {}))
            process.wait()
        finally:
            command_script.unlink(missing_ok=True)
            status_file.unlink(missing_ok=True)

    def _launch(self, test_labels: tuple[str, ...]) -> None:
        if not VENV_PYTHON.is_file():
            self._show_error(
                "No se encontró el Python del entorno virtual:\n"
                f"{VENV_PYTHON}"
            )
            return

        selected_tests = tuple(label for label in test_labels if label in TESTS)
        test_paths = [
            str((TEST_DIRECTORY / TESTS[label]).resolve())
            for label in selected_tests
        ]
        missing = [path for path in test_paths if not Path(path).is_file()]
        if missing:
            self._show_error(
                "No se encontraron estos archivos de prueba:\n\n"
                + "\n".join(missing)
            )
            return

        python_script, command_script, results_file = self._create_runner_files(
            test_paths
        )

        for label in test_labels:
            self._set_button_color(label, WHITE)
        for button in self.buttons.values():
            button.configure(state=tk.DISABLED)

        try:
            process = subprocess.Popen(
                ["cmd.exe", "/d", "/c", str(command_script)],
                cwd=PROJECT_ROOT,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except OSError as error:
            python_script.unlink(missing_ok=True)
            command_script.unlink(missing_ok=True)
            results_file.unlink(missing_ok=True)
            for button in self.buttons.values():
                button.configure(state=tk.NORMAL)
            self._show_error(f"No se pudo abrir CMD:\n{error}")
            return

        threading.Thread(
            target=self._wait_for_console,
            args=(
                process,
                test_labels,
                python_script,
                command_script,
                results_file,
            ),
            daemon=True,
        ).start()
        self.root.after(250, self._check_finished_runs)

    @staticmethod
    def _create_runner_files(
        test_paths: list[str],
    ) -> tuple[Path, Path, Path]:
        python_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".py",
            prefix="_paradox_qa_",
            dir=PROJECT_ROOT,
            delete=False,
        )
        python_script = Path(python_file.name)
        pytest_arguments = [
            *PYTEST_OPTIONS,
            *(Path(path).name for path in test_paths),
        ]

        results_handle = tempfile.NamedTemporaryFile(
            suffix=".json",
            prefix="_paradox_qa_results_",
            dir=PROJECT_ROOT,
            delete=False,
        )
        results_file = Path(results_handle.name)
        results_handle.close()
        results_file.unlink(missing_ok=True)

        python_source = f'''import json
import os
from pathlib import Path
import pytest

class TestResultPlugin:
    def __init__(self):
        self.statuses = {{}}

    def pytest_runtest_logreport(self, report):
        filename = Path(report.location[0]).name
        if report.outcome == "failed":
            self.statuses[filename] = "failed"
        elif report.when == "call" and self.statuses.get(filename) != "failed":
            self.statuses[filename] = "passed"

os.chdir({str(TEST_DIRECTORY)!r})
plugin = TestResultPlugin()
exit_code = pytest.main({pytest_arguments!r}, plugins=[plugin])
result_path = Path({str(results_file)!r})
temporary_result_path = Path(str(result_path) + ".tmp")
temporary_result_path.write_text(json.dumps({{
    "exit_code": exit_code,
    "statuses": plugin.statuses,
}}), encoding="utf-8")
temporary_result_path.replace(result_path)
raise SystemExit(exit_code)
'''
        with python_file:
            python_file.write(python_source)

        command_script = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="ascii",
            suffix=".cmd",
            prefix="_paradox_qa_",
            dir=PROJECT_ROOT,
            delete=False,
        )
        cmd_path = Path(command_script.name)
        with command_script:
            command_script.write("@echo off\r\n")
            command_script.write(f'cd /d "{PROJECT_ROOT}"\r\n')
            command_script.write("echo Ejecutando pruebas con pytest...\r\n")
            command_script.write(
                f'"{VENV_PYTHON}" "{python_script}"\r\n'
            )
            command_script.write('set "TEST_EXIT=%ERRORLEVEL%"\r\n')
            command_script.write("echo.\r\n")
            command_script.write(
                "echo Pytest finalizado. Codigo de salida: %TEST_EXIT%\r\n"
            )
            command_script.write("echo Pulsa una tecla para cerrar esta consola.\r\n")
            command_script.write("pause\r\n")
            command_script.write("exit /b %TEST_EXIT%\r\n")

        return python_script, cmd_path, results_file

    def _wait_for_console(
        self,
        process: subprocess.Popen[bytes],
        test_labels: tuple[str, ...],
        python_script: Path,
        command_script: Path,
        results_file: Path,
    ) -> None:
        try:
            while process.poll() is None and not results_file.is_file():
                threading.Event().wait(0.1)
            try:
                result_data = json.loads(results_file.read_text(encoding="utf-8"))
                return_code = int(result_data["exit_code"])
                results = result_data["statuses"]
            except (OSError, json.JSONDecodeError):
                return_code = process.poll()
                if return_code is None:
                    return_code = process.wait()
                results = {}
            except (KeyError, TypeError, ValueError):
                return_code = process.poll()
                if return_code is None:
                    return_code = process.wait()
                results = {}
            self.finished_runs.put(("tests", test_labels, return_code, results))
            process.wait()
        finally:
            python_script.unlink(missing_ok=True)
            command_script.unlink(missing_ok=True)
            results_file.unlink(missing_ok=True)

    def _check_finished_runs(self) -> None:
        try:
            run_kind, test_labels, return_code, results = (
                self.finished_runs.get_nowait()
            )
        except queue.Empty:
            self.root.after(250, self._check_finished_runs)
            return

        if run_kind == "setup":
            self._set_button_color(
                "Setup",
                PASTEL_GREEN if return_code == 0 else PASTEL_RED,
            )
            for button in self.buttons.values():
                button.configure(state=tk.NORMAL)
            return

        for label in test_labels:
            if label == "Full Test":
                continue

            outcome = results.get(TESTS[label])
            if outcome is None:
                outcome = "passed" if return_code == 0 else "failed"

            self._set_button_color(
                label,
                PASTEL_GREEN if outcome == "passed" else PASTEL_RED,
            )

        if "Full Test" in test_labels:
            self._set_button_color(
                "Full Test",
                PASTEL_GREEN if return_code == 0 else PASTEL_RED,
            )

        for button in self.buttons.values():
            button.configure(state=tk.NORMAL)

    def _set_button_color(self, label: str, color: str) -> None:
        self.buttons[label].configure(bg=color, activebackground=color)

    def _show_error(self, message: str) -> None:
        messagebox.showerror("No se pudo iniciar la prueba", message)


def main() -> None:
    root = tk.Tk()
    TestRunnerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
