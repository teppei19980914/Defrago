"""シンプルな計算機モジュール（サンプルコード）."""


def add(a: int | float, b: int | float) -> int | float:
    """2つの数値を加算する。

    Args:
        a: 最初の数値。
        b: 2番目の数値。

    Returns:
        2つの数値の合計。

    Examples:
        >>> add(1, 2)
        3
        >>> add(1.5, 2.5)
        4.0
    """
    return a + b


def subtract(a: int | float, b: int | float) -> int | float:
    """2つの数値を減算する。

    Args:
        a: 最初の数値（被減数）。
        b: 2番目の数値（減数）。

    Returns:
        a から b を引いた結果。

    Examples:
        >>> subtract(5, 3)
        2
        >>> subtract(10.5, 3.5)
        7.0
    """
    return a - b


def multiply(a: int | float, b: int | float) -> int | float:
    """2つの数値を乗算する。

    Args:
        a: 最初の数値。
        b: 2番目の数値。

    Returns:
        2つの数値の積。

    Examples:
        >>> multiply(3, 4)
        12
        >>> multiply(2.5, 4)
        10.0
    """
    return a * b


def divide(a: int | float, b: int | float) -> float:
    """2つの数値を除算する。

    Args:
        a: 最初の数値（被除数）。
        b: 2番目の数値（除数）。

    Returns:
        a を b で割った結果。

    Raises:
        ZeroDivisionError: b が 0 の場合。

    Examples:
        >>> divide(10, 2)
        5.0
        >>> divide(7, 2)
        3.5
    """
    if b == 0:
        raise ZeroDivisionError("0で割ることはできません")
    return a / b
