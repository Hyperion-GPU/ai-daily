import inspect
import re
import subprocess
import sys
from pathlib import Path

from src.contracts import (
    CONTRACT_DEFINITIONS,
    DigestQueryParams,
    GitHubQueryParams,
    build_contract_schema_json,
    build_frontend_typescript,
)
from src.server import api, schemas

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_server_schemas_reexport_canonical_contracts():
    for definition in CONTRACT_DEFINITIONS:
        if hasattr(schemas, definition.name):
            assert getattr(schemas, definition.name) is definition.model


def test_api_response_models_are_registered_in_contract_registry():
    response_model_names = {
        route.response_model.__name__
        for route in api.router.routes
        if getattr(route, "response_model", None) is not None
    }

    registered_model_names = {definition.name for definition in CONTRACT_DEFINITIONS}

    assert response_model_names <= registered_model_names


def test_digest_query_contract_matches_api_signature_shape():
    assert list(DigestQueryParams.model_fields) == ["tags", "category", "min_importance", "sort", "q"]
    assert _model_defaults(DigestQueryParams) == _signature_defaults(api.get_digest, DigestQueryParams.model_fields.keys())
    assert _model_enum_choices(DigestQueryParams, "sort") == _signature_pattern_choices(api.get_digest, "sort")


def test_github_query_contract_matches_api_signature_shape():
    expected_fields = ["category", "language", "min_stars", "sort", "q", "trend"]
    assert list(GitHubQueryParams.model_fields) == expected_fields

    latest_defaults = _signature_defaults(api.get_latest_github_trending, GitHubQueryParams.model_fields.keys())
    by_date_defaults = _signature_defaults(api.get_github_trending_by_date, GitHubQueryParams.model_fields.keys())

    assert _model_defaults(GitHubQueryParams) == latest_defaults == by_date_defaults
    assert _model_enum_choices(GitHubQueryParams, "sort") == _signature_pattern_choices(api.get_latest_github_trending, "sort")
    assert _model_enum_choices(GitHubQueryParams, "sort") == _signature_pattern_choices(api.get_github_trending_by_date, "sort")
    assert set(_model_enum_choices(GitHubQueryParams, "trend")) == set(
        _signature_pattern_choices(api.get_latest_github_trending, "trend")
    )
    assert set(_model_enum_choices(GitHubQueryParams, "trend")) == set(
        _signature_pattern_choices(api.get_github_trending_by_date, "trend")
    )


def test_generated_frontend_types_are_up_to_date():
    assert (REPO_ROOT / "frontend" / "src" / "types" / "index.ts").read_text(encoding="utf-8") == build_frontend_typescript()


def test_generated_contract_schema_bundle_is_up_to_date():
    schema_path = REPO_ROOT / "frontend" / "src" / "types" / "contracts.schema.json"
    assert schema_path.read_text(encoding="utf-8") == build_contract_schema_json()


def test_export_contracts_script_check_mode_passes():
    result = subprocess.run(
        [sys.executable, "scripts/export_contracts.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def _model_defaults(model):
    return {
        name: field.get_default(call_default_factory=True)
        for name, field in model.model_fields.items()
    }


def _signature_defaults(function, field_names):
    signature = inspect.signature(function)
    defaults = {}
    for field_name in field_names:
        default = signature.parameters[field_name].default
        defaults[field_name] = getattr(default, "default", default)
    return defaults


def _model_enum_choices(model, field_name: str) -> tuple[str, ...]:
    schema = model.model_json_schema()
    property_schema = schema["properties"][field_name]
    if "enum" in property_schema:
        return tuple(property_schema["enum"])

    for item in property_schema.get("anyOf", ()):
        if "enum" in item:
            return tuple(item["enum"])

    raise AssertionError(f"No enum choices found for {model.__name__}.{field_name}")


def _signature_pattern_choices(function, field_name: str) -> tuple[str, ...]:
    signature = inspect.signature(function)
    default = signature.parameters[field_name].default
    pattern = None
    for metadata in getattr(default, "metadata", ()):
        pattern = getattr(metadata, "pattern", None)
        if pattern is not None:
            break
    assert pattern is not None

    match = re.fullmatch(r"^\^\((.+)\)\$$", pattern)
    assert match is not None
    return tuple(match.group(1).split("|"))
