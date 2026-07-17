"""Unit tests for CLI common (backend_context validation)."""

from pathlib import Path

import pytest

from kospel_cmi.tools.cli_common import backend_context


@pytest.fixture
def yaml_state_file(tmp_path: Path) -> Path:
    """Create minimal YAML state file for backend context tests."""
    state_file = tmp_path / "state.yaml"
    state_file.write_text('"0b00": "0000"\n', encoding="utf-8")
    return state_file


class TestBackendContextValidation:
    """Tests for backend_context validation and return values."""

    def test_backend_context_returns_none_when_neither_url_nor_yaml(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """backend_context returns None when neither --url nor --yaml provided."""
        class Args:
            url = None
            yaml_path = None

        result = backend_context(Args())
        assert result is None
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Specify --url" in captured.err or "yaml" in captured.err.lower()

    def test_backend_context_returns_none_when_both_url_and_yaml(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """backend_context returns None when both --url and --yaml provided."""
        class Args:
            url = "http://192.168.1.1/api/dev/65"
            yaml_path = "/tmp/state.yaml"

        result = backend_context(Args())
        assert result is None
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "either" in captured.err.lower() or "not both" in captured.err.lower()

    @pytest.mark.asyncio
    async def test_backend_context_returns_context_manager_when_yaml_provided(
        self, yaml_state_file: Path
    ) -> None:
        """backend_context returns context manager when --yaml points to valid file."""
        class Args:
            url = None
            yaml_path = str(yaml_state_file)

        cm = backend_context(Args())
        assert cm is not None
        async with cm as backend:
            assert backend is not None
            regs = await backend.read_registers("0b00", 1)
            assert "0b00" in regs
            assert regs["0b00"] == "0000"

    @pytest.mark.asyncio
    async def test_backend_context_returns_context_manager_when_url_provided(
        self,
    ) -> None:
        """backend_context returns context manager when --url provided."""
        class Args:
            url = "http://192.168.1.1/api/dev/65"
            yaml_path = None

        cm = backend_context(Args())
        assert cm is not None
        async with cm as backend:
            assert backend is not None
