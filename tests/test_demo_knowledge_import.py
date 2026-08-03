from pathlib import Path

from app.knowledge import importer


def test_demo_import_uses_only_public_example_sources(tmp_path, monkeypatch) -> None:
    for filename in (
        "skus.csv",
        "skus.example.csv",
        "sop.csv",
        "sop.example.csv",
        "faq.md",
        "faq.example.md",
    ):
        (tmp_path / filename).write_text(filename, encoding="utf-8")

    selected_paths: dict[str, Path | None] = {}
    monkeypatch.setattr(importer, "_upsert_catalog", lambda _db: None)
    monkeypatch.setattr(
        importer,
        "_replace_skus",
        lambda _db, path: selected_paths.setdefault("skus", path) is not None,
    )
    monkeypatch.setattr(
        importer,
        "_replace_sop",
        lambda _db, path: selected_paths.setdefault("sop", path) is not None,
    )
    monkeypatch.setattr(
        importer,
        "_replace_faq",
        lambda _db, path: selected_paths.setdefault("faq", path) is not None,
    )
    monkeypatch.setattr(
        importer,
        "_replace_safety_rules",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Demo import must not read private safety files")
        ),
    )

    result = importer.import_knowledge_sources(
        knowledge_dir=tmp_path,
        safety_dir=tmp_path,
        db=object(),
        use_example_sources=True,
        include_safety_rules=False,
    )

    assert result["safety_rules"] == 0
    assert selected_paths == {
        "skus": tmp_path / "skus.example.csv",
        "sop": tmp_path / "sop.example.csv",
        "faq": tmp_path / "faq.example.md",
    }
