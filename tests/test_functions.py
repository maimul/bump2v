import pytest
from bump2v.bumpversion.functions import NumericFunction, ValuesFunction


class TestNumericFunction:
    def test_bump_integer(self):
        f = NumericFunction()
        assert f.bump("0") == "1"
        assert f.bump("9") == "10"
        assert f.bump("99") == "100"

    def test_bump_alphanumeric(self):
        f = NumericFunction()
        assert f.bump("r3") == "r4"
        assert f.bump("dev1") == "dev2"

    def test_first_value_default(self):
        f = NumericFunction()
        assert f.first_value == "0"
        assert f.optional_value == "0"

    def test_first_value_custom(self):
        f = NumericFunction(first_value="5")
        assert f.first_value == "5"
        assert f.optional_value == "5"

    def test_invalid_first_value_raises(self):
        with pytest.raises(ValueError):
            NumericFunction(first_value="no-digits")


class TestValuesFunction:
    def test_bump_through_list(self):
        f = ValuesFunction(["alpha", "beta", "rc", "final"])
        assert f.bump("alpha") == "beta"
        assert f.bump("beta") == "rc"
        assert f.bump("rc") == "final"

    def test_bump_at_max_raises(self):
        f = ValuesFunction(["alpha", "beta", "final"])
        with pytest.raises(ValueError, match="maximum value"):
            f.bump("final")

    def test_empty_values_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ValuesFunction([])

    def test_optional_value_default(self):
        f = ValuesFunction(["alpha", "beta", "final"])
        assert f.optional_value == "alpha"

    def test_optional_value_custom(self):
        f = ValuesFunction(["alpha", "beta", "final"], optional_value="beta")
        assert f.optional_value == "beta"

    def test_invalid_optional_value_raises(self):
        with pytest.raises(ValueError):
            ValuesFunction(["alpha", "beta"], optional_value="gamma")
