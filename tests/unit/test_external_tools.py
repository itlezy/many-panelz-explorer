from __future__ import annotations

from pathlib import Path

from many_panelz_explorer import external_tools


def test_expand_tool_args_keeps_paths_with_spaces_as_single_tokens() -> None:
    archive = Path(r"C:\Archive Dir\sample.7z")
    target = Path(r"D:\Target Dir")

    args = external_tools.expand_tool_args(
        "x -y {archive} -o{target}",
        archive=archive,
        target=target,
    )

    assert args == ["x", "-y", str(archive), rf"-o{target}"]


def test_launch_everything_search_uses_path_argument(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        external_tools,
        "resolve_tool_executable",
        lambda executable, *, tool_name: Path(executable),
    )
    monkeypatch.setattr(
        external_tools,
        "_launch_process",
        lambda args, *, tool_name: captured.update(
            {"args": list(args), "tool_name": tool_name}
        ),
    )

    external_tools.launch_everything_search(
        executable="Everything.exe",
        path=Path(r"C:\Work Dir"),
    )

    assert captured["tool_name"] == "Everything"
    assert captured["args"] == ["Everything.exe", "-path", r"C:\Work Dir"]


def test_launch_archive_extract_expands_archive_and_target(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        external_tools,
        "resolve_tool_executable",
        lambda executable, *, tool_name: Path(executable),
    )
    monkeypatch.setattr(
        external_tools,
        "_launch_process",
        lambda args, *, tool_name: captured.update(
            {"args": list(args), "tool_name": tool_name}
        ),
    )

    external_tools.launch_archive_extract(
        executable="7z.exe",
        args_template="x -y {archive} -o{target}",
        archive=Path(r"C:\Archive Dir\sample.7z"),
        target=Path(r"D:\Target Dir"),
        tool_name="7-Zip",
    )

    assert captured["tool_name"] == "7-Zip"
    assert captured["args"] == [
        "7z.exe",
        "x",
        "-y",
        r"C:\Archive Dir\sample.7z",
        r"-oD:\Target Dir",
    ]
