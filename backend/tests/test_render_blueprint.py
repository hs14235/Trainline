from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_render_blueprint_uses_entrypoint_boolean_contract():
    blueprint = yaml.safe_load(
        (REPOSITORY_ROOT / "render.yaml").read_text(encoding="utf-8")
    )
    api_service = next(
        service
        for service in blueprint["services"]
        if service["name"] == "hs14235-trainline-api-demo"
    )
    environment = {
        variable["key"]: variable.get("value")
        for variable in api_service["envVars"]
    }

    assert environment["RUN_MIGRATIONS"] == "true"
    assert environment["COLLECT_STATIC"] == "true"
