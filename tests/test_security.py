"""Tests for security features."""

import pytest
import tempfile
from pathlib import Path

from src.utils import validate_file_path, check_file_size, MAX_FILE_SIZE
from src.cli import positive_int, parse_args


class TestValidateFilePath:
    """Tests for path validation security."""

    def test_valid_relative_path(self):
        """Test that valid relative paths are accepted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            # Get just the filename
            filename = Path(temp_path).name
            result = validate_file_path(filename)
            assert isinstance(result, Path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_valid_absolute_path(self):
        """Test that valid absolute paths are accepted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        try:
            result = validate_file_path(temp_path)
            assert isinstance(result, Path)
            assert result.is_absolute()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_path_traversal_to_etc_blocked(self):
        """Test that path traversal to /etc is blocked."""
        # Direct path to forbidden directory
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/etc/shadow")

    def test_etc_directory_blocked(self):
        """Test that /etc directory access is blocked."""
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/etc/passwd")

    def test_proc_directory_blocked(self):
        """Test that /proc directory access is blocked."""
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/proc/cpuinfo")

    def test_sys_directory_blocked(self):
        """Test that /sys directory access is blocked."""
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/sys/kernel/debug")

    def test_dev_directory_blocked(self):
        """Test that /dev directory access is blocked."""
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/dev/null")

    def test_root_directory_blocked(self):
        """Test that /root directory access is blocked."""
        with pytest.raises(ValueError, match="forbidden"):
            validate_file_path("/root/.bashrc")

    def test_check_exists_validates_existence(self):
        """Test that check_exists flag validates file existence."""
        with pytest.raises(FileNotFoundError):
            validate_file_path("/tmp/nonexistent_file_12345.txt", check_exists=True)

    def test_check_exists_allows_existing_file(self):
        """Test that existing files pass when check_exists is True."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        try:
            result = validate_file_path(temp_path, check_exists=True)
            assert result.exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCheckFileSize:
    """Tests for file size validation."""

    def test_small_file_allowed(self):
        """Test that small files pass validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("small content")
            temp_path = Path(f.name)

        try:
            # Should not raise any exception
            check_file_size(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_large_file_rejected(self):
        """Test that files exceeding MAX_FILE_SIZE are rejected."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Write just over 10MB
            f.write(b'0' * (MAX_FILE_SIZE + 1))
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="exceeds maximum allowed size"):
                check_file_size(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_file_at_limit_allowed(self):
        """Test that files exactly at MAX_FILE_SIZE are allowed."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Write exactly 10MB
            f.write(b'0' * MAX_FILE_SIZE)
            temp_path = Path(f.name)

        try:
            # Should not raise any exception
            check_file_size(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_nonexistent_file_raises_error(self):
        """Test that checking nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            check_file_size(Path("/tmp/nonexistent_file_99999.txt"))

    def test_custom_max_size(self):
        """Test that custom max_size parameter works."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("x" * 1000)  # 1000 bytes
            temp_path = Path(f.name)

        try:
            # Should pass with 2000 byte limit
            check_file_size(temp_path, max_size=2000)

            # Should fail with 500 byte limit
            with pytest.raises(ValueError, match="exceeds maximum"):
                check_file_size(temp_path, max_size=500)
        finally:
            temp_path.unlink(missing_ok=True)


class TestPositiveInt:
    """Tests for positive_int validator."""

    def test_valid_positive_integer(self):
        """Test that valid positive integers are accepted."""
        assert positive_int("1") == 1
        assert positive_int("5") == 5
        assert positive_int("100") == 100
        assert positive_int("1000") == 1000

    def test_zero_rejected(self):
        """Test that zero is rejected."""
        with pytest.raises(Exception, match="positive integer"):
            positive_int("0")

    def test_negative_rejected(self):
        """Test that negative numbers are rejected."""
        with pytest.raises(Exception, match="positive integer"):
            positive_int("-1")

        with pytest.raises(Exception, match="positive integer"):
            positive_int("-100")

    def test_too_large_rejected(self):
        """Test that numbers over 1000 are rejected."""
        with pytest.raises(Exception, match="<= 1000"):
            positive_int("1001")

        with pytest.raises(Exception, match="<= 1000"):
            positive_int("9999")

    def test_non_integer_rejected(self):
        """Test that non-integer values are rejected."""
        with pytest.raises(Exception, match="must be an integer"):
            positive_int("abc")

        with pytest.raises(Exception, match="must be an integer"):
            positive_int("12.5")

    def test_boundary_values(self):
        """Test boundary values."""
        assert positive_int("1") == 1  # Minimum valid
        assert positive_int("1000") == 1000  # Maximum valid


class TestMaxResultsValidation:
    """Tests for max_results argument validation."""

    def test_valid_max_results(self):
        """Test that valid max_results values are accepted."""
        config = parse_args(["search", "test", "--max-results", "10"])
        assert config.max_results == 10

    def test_max_results_at_boundaries(self):
        """Test max_results at boundary values."""
        config = parse_args(["search", "test", "--max-results", "1"])
        assert config.max_results == 1

        config = parse_args(["search", "test", "--max-results", "1000"])
        assert config.max_results == 1000

    def test_max_results_zero_rejected(self, capsys):
        """Test that zero max_results is rejected."""
        with pytest.raises(SystemExit):
            parse_args(["search", "test", "--max-results", "0"])

    def test_max_results_negative_rejected(self, capsys):
        """Test that negative max_results is rejected."""
        with pytest.raises(SystemExit):
            parse_args(["search", "test", "--max-results", "-5"])

    def test_max_results_too_large_rejected(self, capsys):
        """Test that max_results over 1000 is rejected."""
        with pytest.raises(SystemExit):
            parse_args(["search", "test", "--max-results", "1001"])
