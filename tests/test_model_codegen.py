import importlib
import sys
from pathlib import Path

from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, create_engine

from scripts.db_models import (
    AllTablesDeclarativeGenerator,
    normalize_newlines,
    split_generated_source,
    table_module_stem,
    tool_environment,
)


def test_codegen_does_not_ignore_migration_version_tables() -> None:
    generator = object.__new__(AllTablesDeclarativeGenerator)
    table = Table("alembic_version", MetaData())

    assert generator.should_ignore_table(table) is False


def test_newline_normalization_is_platform_independent() -> None:
    assert normalize_newlines("first\r\nsecond\n") == "first\nsecond\n"


def test_tool_environment_does_not_forward_database_secrets() -> None:
    environment = tool_environment(
        {
            "PATH": "example",
            "DB_USER": "agent_user",
            "DB_PASSWORD": "secret-value",
        }
    )

    assert environment == {"PATH": "example"}


def test_tool_environment_respects_an_explicit_empty_source() -> None:
    assert tool_environment({}) == {}


def test_table_module_stem_is_safe_and_deterministic() -> None:
    assert table_module_stem("market_daily_bar") == "market_daily_bar"
    assert table_module_stem("trade-order") == "trade_order"
    assert table_module_stem("123_table") == "table_123_table"
    assert table_module_stem("class") == "table_class"
    assert table_module_stem("models") == "table_models"


def test_generated_package_has_one_module_per_table(
    tmp_path: Path,
    monkeypatch,
) -> None:
    metadata = MetaData()
    Table("parent", metadata, Column("id", Integer, primary_key=True))
    Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", ForeignKey("parent.id"), nullable=False),
    )
    engine = create_engine("sqlite://")
    try:
        source = AllTablesDeclarativeGenerator(metadata, engine, ["nojoined"]).generate()
        sources, table_names = split_generated_source(source)
    finally:
        engine.dispose()

    assert table_names == {"parent", "child"}
    assert set(sources) == {
        "__init__.py",
        "base.py",
        "child.py",
        "models.py",
        "parent.py",
    }
    assert sources["child.py"].count("__tablename__") == 1
    assert sources["parent.py"].count("__tablename__") == 1
    assert "__tablename__" not in sources["models.py"]
    assert "if TYPE_CHECKING:" in sources["child.py"]

    package_name = "generated_models_test_package"
    package_directory = tmp_path / package_name
    package_directory.mkdir()
    for filename, generated_source in sources.items():
        (package_directory / filename).write_text(generated_source, encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        package = importlib.import_module(package_name)
        package.Base.registry.configure()
        assert set(package.Base.metadata.tables) == table_names
        assert package.Child.__table__.metadata is package.Base.metadata
        assert package.Parent.__table__.metadata is package.Base.metadata
    finally:
        for module_name in tuple(sys.modules):
            if module_name == package_name or module_name.startswith(f"{package_name}."):
                del sys.modules[module_name]
