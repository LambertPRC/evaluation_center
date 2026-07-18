"""Generate or check SQLAlchemy mappings against the MySQL database.

The database URL is built in-process so credentials never appear in process
arguments. Each database table is generated into its own module, and the
generated package is replaced only after formatting and validation.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import importlib
import keyword
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from sqlacodegen.generators import DeclarativeGenerator

from app.core.settings import DatabaseConfigurationError, Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRECTORY = PROJECT_ROOT / "app" / "db" / "generated"
GENERATOR_OPTIONS = {
    "keep_dialect_types",
    "nojoined",
    "nonativeenums",
    "nosyntheticenums",
}
GENERATED_HEADER = (
    "# Generated from the MySQL schema by scripts/db_models.py.\n"
    "# Do not edit generated files by hand; change the database and regenerate them.\n\n"
)
PACKAGE_SUPPORT_FILES = {"__init__.py", "base.py", "models.py"}
RESERVED_MODULE_STEMS = {"__init__", "base", "models"}
WINDOWS_RESERVED_STEMS = {
    "aux",
    "con",
    "nul",
    "prn",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
INVALID_MODULE_CHARACTER = re.compile(r"[^0-9A-Za-z_]")


class ModelGenerationError(RuntimeError):
    """A safe-to-display model generation or validation failure."""


class AllTablesDeclarativeGenerator(DeclarativeGenerator):
    """Include every reflected base table, including migration version tables."""

    def should_ignore_table(self, table: Table) -> bool:
        return False


@dataclass(frozen=True)
class TableDeclaration:
    table_name: str
    symbol_name: str
    node: ast.ClassDef | ast.Assign
    module_stem: str


def normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n")


def tool_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ if source is None else source)
    for name in tuple(environment):
        if name.upper().startswith("DB_"):
            del environment[name]
    return environment


def table_module_stem(table_name: str) -> str:
    """Return a deterministic, importable module stem for a database table."""
    stem = INVALID_MODULE_CHARACTER.sub("_", table_name).strip("_").lower()
    if not stem:
        raise ModelGenerationError("A table name cannot be converted to a module name")
    if stem[0].isdigit():
        stem = f"table_{stem}"
    if keyword.iskeyword(stem) or stem in RESERVED_MODULE_STEMS or stem in WINDOWS_RESERVED_STEMS:
        stem = f"table_{stem}"
    return stem


def _class_table_name(node: ast.ClassDef) -> str | None:
    for statement in node.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == "__tablename__"
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            return statement.value.value
    return None


def _table_assignment_name(node: ast.Assign) -> tuple[str, str] | None:
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    value = node.value
    if (
        not isinstance(value, ast.Call)
        or not isinstance(value.func, ast.Name)
        or value.func.id != "Table"
        or not value.args
        or not isinstance(value.args[0], ast.Constant)
        or not isinstance(value.args[0].value, str)
    ):
        return None
    return value.args[0].value, node.targets[0].id


def _find_table_declarations(tree: ast.Module) -> list[TableDeclaration]:
    unresolved: list[tuple[str, str, ast.ClassDef | ast.Assign]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if table_name := _class_table_name(node):
                unresolved.append((table_name, node.name, node))
        elif isinstance(node, ast.Assign):
            if assignment := _table_assignment_name(node):
                table_name, symbol_name = assignment
                unresolved.append((table_name, symbol_name, node))

    declarations: list[TableDeclaration] = []
    stems_by_casefold: dict[str, str] = {}
    for table_name, symbol_name, node in sorted(unresolved, key=lambda item: item[0]):
        module_stem = table_module_stem(table_name)
        collision_key = module_stem.casefold()
        if previous_table := stems_by_casefold.get(collision_key):
            raise ModelGenerationError(
                f"Tables {previous_table!r} and {table_name!r} map to the same model module"
            )
        stems_by_casefold[collision_key] = table_name
        declarations.append(TableDeclaration(table_name, symbol_name, node, module_stem))
    return declarations


def _referenced_names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _annotation_model_references(node: ast.AST, model_symbols: set[str]) -> set[str]:
    references: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.AnnAssign):
            continue
        for annotation_part in ast.walk(child.annotation):
            if not (
                isinstance(annotation_part, ast.Constant) and isinstance(annotation_part.value, str)
            ):
                continue
            for symbol in model_symbols:
                if re.search(rf"(?<!\w){re.escape(symbol)}(?!\w)", annotation_part.value):
                    references.add(symbol)
    return references


def _selected_external_imports(tree: ast.Module, referenced_names: set[str]) -> list[str]:
    imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            aliases = [
                alias
                for alias in node.names
                if (alias.asname or alias.name.split(".", maxsplit=1)[0]) in referenced_names
            ]
            if aliases:
                imports.append(ast.unparse(ast.Import(names=aliases)))
        elif isinstance(node, ast.ImportFrom):
            aliases = [
                alias for alias in node.names if (alias.asname or alias.name) in referenced_names
            ]
            if aliases:
                imports.append(
                    ast.unparse(ast.ImportFrom(module=node.module, names=aliases, level=node.level))
                )
    return imports


def _render_table_module(
    generated_source: str,
    tree: ast.Module,
    declaration: TableDeclaration,
    declarations_by_symbol: Mapping[str, TableDeclaration],
) -> str:
    referenced_names = _referenced_names(declaration.node)
    own_symbol = declaration.symbol_name
    model_symbols = set(declarations_by_symbol)
    runtime_symbols = (referenced_names & model_symbols) - {own_symbol}
    type_symbols = (
        _annotation_model_references(declaration.node, model_symbols)
        - runtime_symbols
        - {own_symbol}
    )

    imports = _selected_external_imports(tree, referenced_names - model_symbols)
    imports.append("from .base import Base")
    for symbol in sorted(runtime_symbols):
        target = declarations_by_symbol[symbol]
        imports.append(f"from .{target.module_stem} import {symbol}")

    if type_symbols:
        imports.append("from typing import TYPE_CHECKING")
        imports.append("")
        imports.append("if TYPE_CHECKING:")
        for symbol in sorted(type_symbols):
            target = declarations_by_symbol[symbol]
            imports.append(f"    from .{target.module_stem} import {symbol}")

    declaration_source = ast.get_source_segment(generated_source, declaration.node)
    if declaration_source is None:
        declaration_source = ast.unparse(declaration.node)
    return GENERATED_HEADER + "\n".join(imports) + "\n\n\n" + declaration_source + "\n"


def _render_exports(declarations: Sequence[TableDeclaration]) -> tuple[str, str]:
    imports = ["from .base import Base"]
    symbols = ["Base"]
    for declaration in declarations:
        imports.append(f"from .{declaration.module_stem} import {declaration.symbol_name}")
        symbols.append(declaration.symbol_name)

    rendered_symbols = ", ".join(repr(symbol) for symbol in symbols)
    models_source = GENERATED_HEADER + "\n".join(imports) + f"\n\n__all__ = [{rendered_symbols}]\n"
    package_source = (
        GENERATED_HEADER
        + f"from .models import {', '.join(symbols)}\n\n"
        + f"__all__ = [{rendered_symbols}]\n"
    )
    return models_source, package_source


def split_generated_source(generated_source: str) -> tuple[dict[str, str], set[str]]:
    """Split sqlacodegen's full-schema output into a generated Python package."""
    try:
        tree = ast.parse(generated_source)
    except SyntaxError as exc:
        raise ModelGenerationError("sqlacodegen produced invalid Python") from exc

    has_base = any(isinstance(node, ast.ClassDef) and node.name == "Base" for node in tree.body)
    if not has_base:
        raise ModelGenerationError("Generated models do not expose a declarative Base")

    declarations = _find_table_declarations(tree)
    if not declarations:
        raise ModelGenerationError("Generated models do not contain any tables")
    declarations_by_symbol = {item.symbol_name: item for item in declarations}
    if len(declarations_by_symbol) != len(declarations):
        raise ModelGenerationError("Generated table symbols are not unique")

    sources = {
        "base.py": GENERATED_HEADER
        + "from sqlalchemy.orm import DeclarativeBase\n\n\n"
        + "class Base(DeclarativeBase):\n"
        + "    pass\n"
    }
    for declaration in declarations:
        sources[f"{declaration.module_stem}.py"] = _render_table_module(
            generated_source,
            tree,
            declaration,
            declarations_by_symbol,
        )

    models_source, package_source = _render_exports(declarations)
    sources["models.py"] = models_source
    sources["__init__.py"] = package_source
    return sources, {declaration.table_name for declaration in declarations}


def reflect_and_generate(settings: Settings) -> tuple[dict[str, str], set[str], set[str]]:
    engine = create_engine(
        settings.database_url("pymysql"),
        echo=False,
        hide_parameters=True,
        poolclass=NullPool,
        connect_args={"connect_timeout": settings.db_connect_timeout},
    )
    try:
        with engine.connect() as connection:
            selected_database = connection.scalar(text("SELECT DATABASE()"))
            if selected_database != settings.db_name:
                raise ModelGenerationError("Connected to an unexpected database")

            inspector = inspect(connection)
            table_names = set(inspector.get_table_names())
            view_names = set(inspector.get_view_names())
            if not table_names:
                raise ModelGenerationError("The selected database contains no base tables")

            metadata = MetaData()
            metadata.reflect(
                bind=connection,
                only=sorted(table_names),
                views=False,
            )
            reflected_names = set(metadata.tables)
            if reflected_names != table_names:
                raise ModelGenerationError("Not all base tables were reflected")

            generator = AllTablesDeclarativeGenerator(
                metadata,
                connection,
                sorted(GENERATOR_OPTIONS),
            )
            sources, generated_names = split_generated_source(generator.generate())
            if generated_names != table_names:
                raise ModelGenerationError("Not all base tables were split into model modules")
            return sources, table_names, view_names
    finally:
        engine.dispose()


def run_python_tool(arguments: Sequence[str], candidate: Path) -> None:
    command = [sys.executable, "-m", *arguments, str(candidate)]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=tool_environment(),
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        raise ModelGenerationError(
            f"{' '.join(arguments[:2])} rejected generated models"
            + (f":\n{output}" if output else "")
        )


def _remove_bytecode_caches(directory: Path) -> None:
    for cache_directory in directory.rglob("__pycache__"):
        shutil.rmtree(cache_directory, ignore_errors=True)


def _validate_one_table_per_module(candidate: Path, expected_tables: set[str]) -> None:
    discovered_tables: set[str] = set()
    table_module_count = 0
    for module_path in sorted(candidate.glob("*.py")):
        if module_path.name in PACKAGE_SUPPORT_FILES:
            continue
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        declarations = _find_table_declarations(tree)
        if len(declarations) != 1:
            raise ModelGenerationError(
                f"Generated table module {module_path.name!r} must contain exactly one table"
            )
        declaration = declarations[0]
        if module_path.stem != declaration.module_stem:
            raise ModelGenerationError("Generated table module name does not match its table")
        discovered_tables.add(declaration.table_name)
        table_module_count += 1

    if discovered_tables != expected_tables or table_module_count != len(expected_tables):
        raise ModelGenerationError("Generated package does not contain one module per base table")


def validate_candidate(candidate: Path, expected_tables: set[str]) -> None:
    run_python_tool(
        (
            "ruff",
            "check",
            "--select",
            "I",
            "--fix",
            "--no-cache",
            "--no-respect-gitignore",
        ),
        candidate,
    )
    run_python_tool(
        (
            "ruff",
            "format",
            "--no-cache",
            "--no-respect-gitignore",
        ),
        candidate,
    )
    run_python_tool(
        (
            "ruff",
            "check",
            "--no-cache",
            "--no-respect-gitignore",
        ),
        candidate,
    )
    run_python_tool(
        (
            "pyright",
            "--pythonpath",
            sys.executable,
        ),
        candidate,
    )

    _validate_one_table_per_module(candidate, expected_tables)
    module_name = f"app.db.{candidate.name}"
    importlib.invalidate_caches()
    try:
        package = importlib.import_module(module_name)
        base = getattr(package, "Base", None)
        if base is None or not hasattr(base, "metadata") or not hasattr(base, "registry"):
            raise ModelGenerationError("Generated models do not expose a valid Base")

        base.registry.configure()
        generated_tables = set(base.metadata.tables)
        if generated_tables != expected_tables:
            raise ModelGenerationError("Generated metadata does not contain every base table")
    finally:
        for loaded_name in tuple(sys.modules):
            if loaded_name == module_name or loaded_name.startswith(f"{module_name}."):
                del sys.modules[loaded_name]
        _remove_bytecode_caches(candidate)


def write_candidate(sources: Mapping[str, str]) -> Path:
    TARGET_DIRECTORY.parent.mkdir(parents=True, exist_ok=True)
    candidate = Path(
        tempfile.mkdtemp(
            dir=TARGET_DIRECTORY.parent,
            prefix="_generated_codegen_",
        )
    )
    for filename, source in sources.items():
        if Path(filename).name != filename or not filename.endswith(".py"):
            raise ModelGenerationError("Generated package contains an unsafe filename")
        with (candidate / filename).open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(source)
    return candidate


def _python_sources(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {
        path.name: normalize_newlines(path.read_text(encoding="utf-8"))
        for path in directory.glob("*.py")
    }


def compare_candidate(candidate: Path, show_diff: bool) -> bool:
    expected_sources = _python_sources(TARGET_DIRECTORY)
    actual_sources = _python_sources(candidate)
    if expected_sources == actual_sources:
        return True

    if show_diff:
        for filename in sorted(expected_sources.keys() | actual_sources.keys()):
            expected = expected_sources.get(filename, "")
            actual = actual_sources.get(filename, "")
            if expected == actual:
                continue
            from_file = (
                str(TARGET_DIRECTORY / filename) if filename in expected_sources else "/dev/null"
            )
            to_file = (
                f"database-reflected/{filename}" if filename in actual_sources else "/dev/null"
            )
            diff = difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile=from_file,
                tofile=to_file,
            )
            sys.stdout.writelines(diff)
    return False


def install_candidate(candidate: Path) -> None:
    backup = TARGET_DIRECTORY.parent / f"_generated_backup_{uuid.uuid4().hex}"
    target_existed = TARGET_DIRECTORY.exists()
    if target_existed:
        os.replace(TARGET_DIRECTORY, backup)
    try:
        os.replace(candidate, TARGET_DIRECTORY)
    except BaseException:
        if target_existed and backup.exists() and not TARGET_DIRECTORY.exists():
            os.replace(backup, TARGET_DIRECTORY)
        raise
    if target_existed:
        shutil.rmtree(backup)


def execute(mode: str, show_diff: bool = False) -> int:
    candidate: Path | None = None
    try:
        settings = Settings()
        sources, table_names, view_names = reflect_and_generate(settings)
        candidate = write_candidate(sources)
        validate_candidate(candidate, table_names)
        unchanged = compare_candidate(candidate, show_diff)

        if mode == "check":
            if not unchanged:
                print(
                    f"Model drift detected for {len(table_names)} base tables "
                    f"({len(view_names)} views excluded).",
                    file=sys.stderr,
                )
                return 1
            print(
                f"Models match {len(table_names)} base tables ({len(view_names)} views excluded)."
            )
            return 0

        if unchanged:
            print(
                f"Models already match {len(table_names)} base tables "
                f"({len(view_names)} views excluded)."
            )
            return 0

        install_candidate(candidate)
        candidate = None
        print(
            f"Generated one model module for each of {len(table_names)} base tables "
            f"({len(view_names)} views excluded)."
        )
        return 0
    except (DatabaseConfigurationError, ModelGenerationError):
        print(
            "Model generation failed: database configuration, reflection, "
            "or generated-code validation was unsuccessful.",
            file=sys.stderr,
        )
        return 2
    except SQLAlchemyError:
        print(
            "Model generation failed: MySQL could not be reached or reflected.",
            file=sys.stderr,
        )
        return 2
    except Exception:
        print(
            "Model generation failed: an unexpected validation error occurred.",
            file=sys.stderr,
        )
        return 2
    finally:
        if candidate is not None and candidate.exists():
            shutil.rmtree(candidate, ignore_errors=True)


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("generate", "check"))
    parser.add_argument(
        "--diff",
        action="store_true",
        help="show unified per-file model diffs in check mode",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    parsed = parse_args(arguments)
    return execute(parsed.mode, parsed.diff)


if __name__ == "__main__":
    raise SystemExit(main())
