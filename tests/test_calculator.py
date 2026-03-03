"""calculator モジュールのテスト."""

import pytest

from study_python.calculator import add, divide, multiply, subtract


class TestAdd:
    """add 関数のテストクラス."""

    def test_add_positive_numbers(self) -> None:
        """正の整数の加算をテスト."""
        assert add(1, 2) == 3

    def test_add_negative_numbers(self) -> None:
        """負の整数の加算をテスト."""
        assert add(-1, -2) == -3

    def test_add_with_zero(self) -> None:
        """0との加算をテスト."""
        assert add(0, 5) == 5
        assert add(5, 0) == 5

    def test_add_float_numbers(self) -> None:
        """浮動小数点数の加算をテスト."""
        assert add(1.5, 2.5) == 4.0


class TestSubtract:
    """subtract 関数のテストクラス."""

    def test_subtract_positive_numbers(self) -> None:
        """正の整数の減算をテスト."""
        assert subtract(5, 3) == 2

    def test_subtract_result_negative(self) -> None:
        """結果が負になる減算をテスト."""
        assert subtract(3, 5) == -2

    def test_subtract_with_fixture(self, sample_numbers: tuple[int, int]) -> None:
        """フィクスチャを使用した減算テスト."""
        a, b = sample_numbers
        assert subtract(a, b) == 5


class TestMultiply:
    """multiply 関数のテストクラス."""

    def test_multiply_positive_numbers(self) -> None:
        """正の整数の乗算をテスト."""
        assert multiply(3, 4) == 12

    def test_multiply_with_zero(self) -> None:
        """0との乗算をテスト."""
        assert multiply(5, 0) == 0

    def test_multiply_negative_numbers(self) -> None:
        """負の整数を含む乗算をテスト."""
        assert multiply(-3, 4) == -12
        assert multiply(-3, -4) == 12


class TestDivide:
    """divide 関数のテストクラス."""

    def test_divide_evenly(self) -> None:
        """割り切れる除算をテスト."""
        assert divide(10, 2) == 5.0

    def test_divide_with_remainder(self) -> None:
        """余りが出る除算をテスト."""
        assert divide(7, 2) == 3.5

    def test_divide_by_zero_raises_error(self) -> None:
        """0で割った場合にZeroDivisionErrorが発生することをテスト."""
        with pytest.raises(ZeroDivisionError, match="0で割ることはできません"):
            divide(10, 0)
