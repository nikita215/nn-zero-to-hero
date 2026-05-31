import os
import subprocess
from pathlib import Path
from typing import Any


class RemoteWorkspace:
    def __init__(self, root: Path, command_timeout: int = 10) -> None:
        self.root = root.resolve()
        self.command_timeout = command_timeout
        if not self.root.exists():
            raise FileNotFoundError(f"workspace does not exist: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"workspace is not a directory: {self.root}")

    def resolve_inside(self, relative_path: str | None) -> Path:
        relative_path = relative_path or "."
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise PermissionError("path escapes workspace")
        return candidate

    def relative(self, path: Path) -> str:
        return str(path.relative_to(self.root)).replace("\\", "/")

    def info(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "separator": os.sep,
        }

    def list_dir(self, relative_path: str | None = ".") -> dict[str, Any]:
        path = self.resolve_inside(relative_path)
        if not path.is_dir():
            raise NotADirectoryError(f"not a directory: {relative_path}")

        entries = []
        for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            stat = child.stat()
            entries.append(
                {
                    "name": child.name,
                    "path": self.relative(child),
                    "type": "directory" if child.is_dir() else "file",
                    "size": stat.st_size,
                }
            )
        return {"path": self.relative(path) if path != self.root else ".", "entries": entries}

    def read_file(self, relative_path: str) -> dict[str, Any]:
        path = self.resolve_inside(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"not a file: {relative_path}")
        content = path.read_text(encoding="utf-8")
        return {"path": self.relative(path), "content": content}

    def write_file(self, relative_path: str, content: str) -> dict[str, Any]:
        path = self.resolve_inside(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": self.relative(path), "bytes": len(content.encode("utf-8"))}

    def search_text(self, query: str, relative_path: str | None = ".", max_results: int = 100) -> dict[str, Any]:
        start = self.resolve_inside(relative_path)
        if not start.exists():
            raise FileNotFoundError(f"path does not exist: {relative_path}")

        files = [start] if start.is_file() else self._walk_files(start)
        results = []
        for file_path in files:
            if len(results) >= max_results:
                break
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            except OSError:
                continue

            for line_number, line in enumerate(lines, start=1):
                if query in line:
                    results.append(
                        {
                            "path": self.relative(file_path),
                            "line": line_number,
                            "text": line,
                        }
                    )
                    if len(results) >= max_results:
                        break

        return {"query": query, "results": results, "truncated": len(results) >= max_results}

    def _walk_files(self, start: Path) -> list[Path]:
        ignored_dirs = {".git", "__pycache__", ".venv", "node_modules"}
        files = []
        for root, dirnames, filenames in os.walk(start):
            dirnames[:] = [name for name in dirnames if name not in ignored_dirs]
            for filename in filenames:
                files.append(Path(root) / filename)
        return files

    def exec_command(self, command: str) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
            )
            return {
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "command": command,
                "exit_code": 124,
                "stdout": exc.stdout or "",
                "stderr": f"command timed out after {self.command_timeout} seconds",
            }
