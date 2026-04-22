import os
import shutil
import stat
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple


class RepositoryStructureAnalyzer:
    """Clona un repositorio de GitHub e imprime una jerarquia AST basica de Java con metricas."""

    _tracked_repositories: Set[Path] = set()

    def __init__(self, clone_root: str = "cloned_repositories"):
        self.clone_root = Path(clone_root)

    def analyze_and_print(self, repository_input: str) -> None:
        """Punto de entrada usado por el controlador. No eleva excepciones esperadas de ejecucion."""
        print("\n[RepositoryStructureAnalyzer] Starting repository structure analysis...")

        try:
            clone_url, repo_folder_name = self._normalize_repository_input(repository_input)
            repository_path = self._clone_or_update_repository(clone_url, repo_folder_name)
            metrics = self._build_java_hierarchy_and_metrics(repository_path)
            self._print_summary(repository_path, metrics)
        except Exception as exc:
            print(f"[RepositoryStructureAnalyzer] Warning: {exc}")

    def clone_repository(self, repository_input: str) -> Path:
        """Clona o actualiza repositorio desde la GUI y retorna su ruta local."""
        clone_url, repo_folder_name = self._normalize_repository_input(repository_input)
        return self._clone_or_update_repository(clone_url, repo_folder_name)

    def delete_repository(self, repository_input: str) -> bool:
        """Elimina el repositorio clonado localmente para el identificador recibido.

        Retorna True si se elimino una carpeta existente, False si no existia.
        """
        _, repo_folder_name = self._normalize_repository_input(repository_input)
        target_path = (self.clone_root / repo_folder_name).resolve()
        if not target_path.exists():
            return False

        self._safe_rmtree(target_path)
        self._tracked_repositories.discard(target_path)
        return True

    @classmethod
    def cleanup_tracked_repositories(cls) -> Dict:
        """Elimina solo los repositorios usados en la sesion actual del servidor."""
        removed = []
        not_found = []
        failed = []

        for repo_path in list(cls._tracked_repositories):
            if not repo_path.exists():
                not_found.append(str(repo_path))
                cls._tracked_repositories.discard(repo_path)
                continue

            try:
                cls._safe_rmtree(repo_path)
                removed.append(str(repo_path))
                cls._tracked_repositories.discard(repo_path)
            except Exception as cleanup_error:
                failed.append({
                    "path": str(repo_path),
                    "error": str(cleanup_error),
                })

        return {
            "removed": removed,
            "not_found": not_found,
            "failed": failed,
        }

    @staticmethod
    def _safe_rmtree(target_path: Path) -> None:
        """Elimina directorios de forma robusta para Windows/OneDrive."""

        def _on_rm_error(func, path, _exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        last_error = None
        for _ in range(3):
            try:
                shutil.rmtree(target_path, onerror=_on_rm_error)
                last_error = None
                break
            except Exception as cleanup_error:
                last_error = cleanup_error
                time.sleep(0.3)

        if last_error is not None:
            raise last_error

    def _normalize_repository_input(self, repository_input: str) -> Tuple[str, str]:
        """Acepta owner/repo, URL de GitHub o clave Sonar owner_repo y retorna URL de clonado y carpeta."""
        raw_value = (repository_input or "").strip()
        if not raw_value:
            raise ValueError("Repository name is empty.")

        owner = ""
        repo = ""

        if raw_value.startswith("http://") or raw_value.startswith("https://"):
            clean_url = raw_value[:-4] if raw_value.endswith(".git") else raw_value
            parts = clean_url.rstrip("/").split("/")
            if len(parts) < 2:
                raise ValueError("Invalid repository URL format.")
            owner, repo = parts[-2], parts[-1]
        elif "/" in raw_value:
            owner, repo = raw_value.split("/", 1)
        elif "_" in raw_value:
            owner, repo = raw_value.split("_", 1)
        else:
            raise ValueError(
                "Repository format not recognized. Use owner/repo, GitHub URL, or Sonar key owner_repo."
            )

        owner = owner.strip()
        repo = repo.strip()
        if not owner or not repo:
            raise ValueError("Repository owner or name is empty after parsing.")

        clone_url = f"https://github.com/{owner}/{repo}.git"
        folder_name = f"{owner}_{repo}"
        return clone_url, folder_name

    def _clone_or_update_repository(self, clone_url: str, repo_folder_name: str) -> Path:
        if shutil.which("git") is None:
            raise RuntimeError("Git is not installed or not available in PATH.")

        self.clone_root.mkdir(parents=True, exist_ok=True)
        target_path = (self.clone_root / repo_folder_name).resolve()

        if target_path.exists():
            print(f"[RepositoryStructureAnalyzer] Repository already exists. Updating: {target_path}")
            subprocess.run(
                ["git", "-C", str(target_path), "pull", "--ff-only"],
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            print(f"[RepositoryStructureAnalyzer] Cloning repository from: {clone_url}")
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(target_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if clone_result.returncode != 0:
                raise RuntimeError(clone_result.stderr.strip() or "Could not clone repository.")

        self._tracked_repositories.add(target_path)
        return target_path

    def _build_java_hierarchy_and_metrics(self, repository_path: Path) -> Dict:
        try:
            import javalang
        except ImportError as import_error:
            raise RuntimeError(
                "The 'javalang' package is required for AST analysis. Install it with: pip install javalang"
            ) from import_error

        hierarchy: Dict[str, List[Dict]] = {}
        parse_errors: List[Dict] = []

        total_java_files = 0
        total_classes = 0
        total_methods = 0
        total_constructors = 0
        total_lines = 0

        for java_file in repository_path.rglob("*.java"):
            # Omite directorios ocultos o generados si existen.
            if any(part.startswith(".") for part in java_file.parts):
                continue

            total_java_files += 1
            relative_file = java_file.relative_to(repository_path).as_posix()

            try:
                source_code = java_file.read_text(encoding="utf-8", errors="ignore")
                total_lines += len(source_code.splitlines())

                compilation_unit = javalang.parse.parse(source_code)
                package_name = compilation_unit.package.name if compilation_unit.package else "(default)"

                file_types = []
                for _, class_node in compilation_unit.filter(javalang.tree.ClassDeclaration):
                    methods = [method.name for method in class_node.methods]
                    constructors = [ctor.name for ctor in class_node.constructors]

                    total_classes += 1
                    total_methods += len(methods)
                    total_constructors += len(constructors)

                    file_types.append(
                        {
                            "kind": "class",
                            "name": class_node.name,
                            "methods": methods,
                            "constructors": constructors,
                        }
                    )

                for _, interface_node in compilation_unit.filter(javalang.tree.InterfaceDeclaration):
                    methods = [method.name for method in interface_node.methods]
                    total_classes += 1
                    total_methods += len(methods)

                    file_types.append(
                        {
                            "kind": "interface",
                            "name": interface_node.name,
                            "methods": methods,
                            "constructors": [],
                        }
                    )

                for _, enum_node in compilation_unit.filter(javalang.tree.EnumDeclaration):
                    methods = [method.name for method in enum_node.methods]
                    total_classes += 1
                    total_methods += len(methods)

                    file_types.append(
                        {
                            "kind": "enum",
                            "name": enum_node.name,
                            "methods": methods,
                            "constructors": [],
                        }
                    )

                hierarchy[relative_file] = [
                    {
                        "package": package_name,
                        "types": file_types,
                    }
                ]

            except Exception as parse_error:
                parse_errors.append({"file": relative_file, "error": str(parse_error)})

        return {
            "repository": repository_path.as_posix(),
            "java_files": total_java_files,
            "classes": total_classes,
            "methods": total_methods,
            "constructors": total_constructors,
            "lines": total_lines,
            "hierarchy": hierarchy,
            "parse_errors": parse_errors,
        }

    def _print_summary(self, repository_path: Path, metrics: Dict) -> None:
        print("\n[RepositoryStructureAnalyzer] AST hierarchy and metrics")
        print(f"Repository path: {repository_path}")
        print(f"Java files: {metrics['java_files']}")
        print(f"Classes/Interfaces/Enums: {metrics['classes']}")
        print(f"Methods: {metrics['methods']}")
        print(f"Constructors: {metrics['constructors']}")
        print(f"Total lines (Java files): {metrics['lines']}")

        if metrics["parse_errors"]:
            print(f"Files with parse errors: {len(metrics['parse_errors'])}")

        print("\nHierarchy:")
        for relative_file, entries in metrics["hierarchy"].items():
            print(f"- File: {relative_file}")
            for entry in entries:
                print(f"  - Package: {entry['package']}")
                for type_info in entry["types"]:
                    print(f"    - {type_info['kind'].capitalize()}: {type_info['name']}")
                    if type_info["constructors"]:
                        print("      - Constructors:")
                        for constructor_name in type_info["constructors"]:
                            print(f"        - {constructor_name}")
                    if type_info["methods"]:
                        print("      - Methods:")
                        for method_name in type_info["methods"]:
                            print(f"        - {method_name}")

        if metrics["parse_errors"]:
            print("\nParse errors detail:")
            for parse_error in metrics["parse_errors"][:10]:
                print(f"- {parse_error['file']}: {parse_error['error']}")
            if len(metrics["parse_errors"]) > 10:
                print("- ...")
