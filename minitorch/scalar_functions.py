from __future__ import annotations

from typing import TYPE_CHECKING

import minitorch

from . import operators
from .autodiff import Context

if TYPE_CHECKING:
    from typing import Tuple

    from .scalar import Scalar, ScalarLike


def wrap_tuple(x):  # type: ignore
    "Turn a possible value into a tuple"
    if isinstance(x, tuple):
        return x
    return (x,)


def unwrap_tuple(x):  # type: ignore
    "Turn a singleton tuple into a value"
    if len(x) == 1:
        return x[0]
    return x


class ScalarFunction:
    """
    A wrapper for a mathematical function that processes and produces
    Scalar variables.

    This is a static class and is never instantiated. We use `class`
    here to group together the `forward` and `backward` code.
    处理和生成标量Variables的数学函数的包装器
    是一个从来不会被实例化的静态类，使用这个类把 `forward` 和`backward` 代码组合到一起
    """

    @classmethod
    def _backward(cls, ctx: Context, d_out: float) -> Tuple[float, ...]:
        return wrap_tuple(cls.backward(ctx, d_out))  # type: ignore

    @classmethod
    def _forward(cls, ctx: Context, *inps: float) -> float:
        return cls.forward(ctx, *inps)  # type: ignore

    @classmethod
    def apply(cls, *vals: "ScalarLike") -> Scalar:
        raw_vals = []
        scalars = []
        for v in vals:
            if isinstance(v, minitorch.scalar.Scalar):
                scalars.append(v)
                raw_vals.append(v.data)
            else:
                scalars.append(minitorch.scalar.Scalar(v))
                raw_vals.append(v)

        # Create the context.
        ctx = Context(False)

        # Call forward with the variables.
        c = cls._forward(ctx, *raw_vals)
        assert isinstance(c, float), "Expected return type float got %s" % (type(c))

        # Create a new variable from the result with a new history.
        back = minitorch.scalar.ScalarHistory(cls, ctx, scalars)
        return minitorch.scalar.Scalar(c, back)


# Examples
class Add(ScalarFunction):
    "Addition function $f(x, y) = x + y$"

    @staticmethod
    def forward(ctx: Context, a: float, b: float) -> float:
        return a + b

    @staticmethod
    def backward(ctx: Context, d_output: float) -> Tuple[float, ...]:
        return d_output, d_output


class Log(ScalarFunction):
    "Log function $f(x) = log(x)$"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        ctx.save_for_backward(a)
        return operators.log(a)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        (a,) = ctx.saved_values
        return operators.log_back(a, d_output)


# To implement.


class Mul(ScalarFunction):
    "Multiplication function"

    @staticmethod
    def forward(ctx: Context, a: float, b: float) -> float:
        ctx.save_for_backward(a, b)
        return a * b

    @staticmethod
    def backward(ctx: Context, d_output: float) -> Tuple[float, float]:
        (a, b,) = ctx.saved_values
        return b * d_output, a * d_output


class Inv(ScalarFunction):
    "Inverse function"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        ctx.save_for_backward(a)
        return operators.inv(a)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        (a,) = ctx.saved_values
        return -d_output / a ** 2


class Neg(ScalarFunction):
    "Negation function"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        return -a

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        return -d_output


class Sigmoid(ScalarFunction):
    "Sigmoid function"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        ctx.save_for_backward(a)
        return operators.sigmoid(a)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        a, = ctx.saved_values
        return operators.sigmoid(a) * (1 - operators.sigmoid(a)) * d_output


class ReLU(ScalarFunction):
    "ReLU function"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        ctx.save_for_backward(a)
        return operators.relu(a)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        a, = ctx.saved_values
        return d_output if a > 0 else 0


class Exp(ScalarFunction):
    "Exp function"

    @staticmethod
    def forward(ctx: Context, a: float) -> float:
        ctx.save_for_backward(a)
        return operators.exp(a)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> float:
        a, = ctx.saved_values
        return d_output * operators.exp(a)


class LT(ScalarFunction):
    "Less-than function $f(x) =$ 1.0 if x is less than y else 0.0"

    @staticmethod
    def forward(ctx: Context, a: float, b: float) -> float:
        return operators.lt(a, b)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> Tuple[float, float]:
        return 0, 0


class EQ(ScalarFunction):
    "Equal function $f(x) =$ 1.0 if x is equal to y else 0.0"

    @staticmethod
    def forward(ctx: Context, a: float, b: float) -> float:
        return operators.eq(a, b)

    @staticmethod
    def backward(ctx: Context, d_output: float) -> Tuple[float, float]:
        return 0, 0
