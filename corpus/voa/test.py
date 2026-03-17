from pathlib import Path
import yaml


def cases():
    for yaml_file in sorted(Path(__file__).parent.glob("*.yaml")):
        for item in yaml.safe_load(yaml_file.read_text()) or []:
            yield {
                "input": item["input"],
                "hints": item.get("hints", []),
                "expected": item.get("expected"),
                "error": item.get("error"),
                "notes": item.get("notes", item["input"][:40]),
            }
