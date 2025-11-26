"""Unit tests for Python version checker."""

import pytest
import sys
from src.utils.version_checker import PythonVersionChecker, VersionCheckResult


class TestPythonVersionChecker:
    """Test PythonVersionChecker functionality."""
    
    def test_check_version_tuple_below_minimum(self):
        """Test version below minimum (3.9)."""
        result = PythonVersionChecker.check_version_tuple((3, 9, 0))
        
        assert not result.is_compatible
        assert result.severity == 'error'
        assert '3.9.0' in result.message
        assert 'not supported' in result.message.lower()
    
    def test_check_version_tuple_at_minimum(self):
        """Test version at minimum (3.10)."""
        result = PythonVersionChecker.check_version_tuple((3, 10, 0))
        
        assert result.is_compatible
        assert result.severity == 'warning'
        assert '3.10.0' in result.message
        assert 'recommended' in result.message.lower()
    
    def test_check_version_tuple_recommended(self):
        """Test recommended version (3.11)."""
        result = PythonVersionChecker.check_version_tuple((3, 11, 0))
        
        assert result.is_compatible
        assert result.severity == 'ok'
        assert '3.11.0' in result.message
        assert 'supported' in result.message.lower()
    
    def test_check_version_tuple_above_tested(self):
        """Test version above maximum tested (3.13+)."""
        result = PythonVersionChecker.check_version_tuple((3, 13, 0))
        
        assert result.is_compatible
        assert result.severity == 'warning'
        assert '3.13.0' in result.message
        assert 'newer' in result.message.lower()
    
    def test_check_version_tuple_python_2(self):
        """Test Python 2.x (should fail)."""
        result = PythonVersionChecker.check_version_tuple((2, 7, 18))
        
        assert not result.is_compatible
        assert result.severity == 'error'
    
    def test_check_version_tuple_edge_cases(self):
        """Test edge case versions."""
        # 3.9.13 (current problematic version)
        result = PythonVersionChecker.check_version_tuple((3, 9, 13))
        assert not result.is_compatible
        
        # 3.10.0 (minimum)
        result = PythonVersionChecker.check_version_tuple((3, 10, 0))
        assert result.is_compatible
        
        # 3.12.0 (maximum tested)
        result = PythonVersionChecker.check_version_tuple((3, 12, 0))
        assert result.is_compatible
        assert result.severity == 'ok'
    
    def test_check_current_version(self):
        """Test checking current Python version."""
        result = PythonVersionChecker.check_version()
        
        assert isinstance(result, VersionCheckResult)
        assert result.current_version == sys.version_info[:3]
        assert result.message is not None
        assert result.severity in ('ok', 'warning', 'error')
    
    def test_get_version_info(self):
        """Test getting version information."""
        info = PythonVersionChecker.get_version_info()
        
        assert 'version' in info
        assert 'version_tuple' in info
        assert 'full_version' in info
        assert 'implementation' in info
        assert 'minimum_required' in info
        assert 'recommended' in info
        assert 'maximum_tested' in info
        
        assert info['minimum_required'] == '3.10'
        assert info['recommended'] == '3.11'
        assert info['maximum_tested'] == '3.12'
    
    def test_version_check_result_attributes(self):
        """Test VersionCheckResult attributes."""
        result = VersionCheckResult(
            is_compatible=True,
            current_version=(3, 11, 0),
            message="Test message",
            severity='ok'
        )
        
        assert result.is_compatible is True
        assert result.current_version == (3, 11, 0)
        assert result.message == "Test message"
        assert result.severity == 'ok'
    
    def test_version_comparison_logic(self):
        """Test version comparison logic."""
        # Test various version combinations
        test_cases = [
            ((3, 8, 0), False, 'error'),
            ((3, 9, 0), False, 'error'),
            ((3, 9, 13), False, 'error'),
            ((3, 10, 0), True, 'warning'),
            ((3, 10, 5), True, 'warning'),
            ((3, 11, 0), True, 'ok'),
            ((3, 11, 5), True, 'ok'),
            ((3, 12, 0), True, 'ok'),
            ((3, 12, 5), True, 'ok'),
            ((3, 13, 0), True, 'warning'),
            ((3, 14, 0), True, 'warning'),
        ]
        
        for version, expected_compatible, expected_severity in test_cases:
            result = PythonVersionChecker.check_version_tuple(version)
            assert result.is_compatible == expected_compatible, \
                f"Version {version} compatibility mismatch"
            assert result.severity == expected_severity, \
                f"Version {version} severity mismatch"
    
    def test_version_tuple_with_two_elements(self):
        """Test version tuple with only major and minor."""
        result = PythonVersionChecker.check_version_tuple((3, 11))
        
        assert result.is_compatible
        assert result.current_version == (3, 11, 0)
    
    def test_version_tuple_with_extra_elements(self):
        """Test version tuple with more than 3 elements."""
        result = PythonVersionChecker.check_version_tuple((3, 11, 5, 'final', 0))
        
        assert result.is_compatible
        assert result.current_version == (3, 11, 5)
    
    def test_deterministic_results(self):
        """Test that same version always returns same result."""
        version = (3, 11, 0)
        
        result1 = PythonVersionChecker.check_version_tuple(version)
        result2 = PythonVersionChecker.check_version_tuple(version)
        result3 = PythonVersionChecker.check_version_tuple(version)
        
        assert result1.is_compatible == result2.is_compatible == result3.is_compatible
        assert result1.severity == result2.severity == result3.severity
        assert result1.current_version == result2.current_version == result3.current_version
    
    def test_message_content(self):
        """Test that messages contain useful information."""
        # Error message
        result = PythonVersionChecker.check_version_tuple((3, 9, 0))
        assert 'not supported' in result.message.lower()
        assert '3.10' in result.message
        
        # Warning message (at minimum)
        result = PythonVersionChecker.check_version_tuple((3, 10, 0))
        assert 'recommended' in result.message.lower()
        assert '3.11' in result.message
        
        # OK message
        result = PythonVersionChecker.check_version_tuple((3, 11, 0))
        assert 'supported' in result.message.lower()
        
        # Warning message (above tested)
        result = PythonVersionChecker.check_version_tuple((3, 13, 0))
        assert 'newer' in result.message.lower()
        assert 'not been fully tested' in result.message.lower()


class TestVersionCheckIntegration:
    """Integration tests for version checking."""
    
    def test_log_version_check(self, caplog):
        """Test logging version check results."""
        import logging
        caplog.set_level(logging.INFO)
        
        result = PythonVersionChecker.log_version_check()
        
        assert isinstance(result, VersionCheckResult)
        # Should have logged something
        assert len(caplog.records) > 0
    
    def test_ensure_compatible_version_with_compatible(self):
        """Test ensure_compatible_version with compatible version."""
        # Mock check_version to return compatible
        original_check = PythonVersionChecker.check_version
        
        def mock_check():
            return VersionCheckResult(
                is_compatible=True,
                current_version=(3, 11, 0),
                message="Compatible",
                severity='ok'
            )
        
        PythonVersionChecker.check_version = mock_check
        
        try:
            # Should not raise
            PythonVersionChecker.ensure_compatible_version()
        finally:
            PythonVersionChecker.check_version = original_check
    
    def test_ensure_compatible_version_with_incompatible(self):
        """Test ensure_compatible_version with incompatible version."""
        # Mock check_version to return incompatible
        original_check = PythonVersionChecker.check_version
        
        def mock_check():
            return VersionCheckResult(
                is_compatible=False,
                current_version=(3, 9, 0),
                message="Incompatible",
                severity='error'
            )
        
        PythonVersionChecker.check_version = mock_check
        
        try:
            # Should raise SystemExit
            with pytest.raises(SystemExit):
                PythonVersionChecker.ensure_compatible_version()
        finally:
            PythonVersionChecker.check_version = original_check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
