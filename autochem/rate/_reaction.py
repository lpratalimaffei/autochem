"""Rates."""

import itertools
import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import altair
import numpy
import pint
import pydantic
from numpy.typing import ArrayLike, NDArray

from ..unit_ import UnitsData
from ..util import chemkin
from ..util.type_ import Scalable, Scalers
from .data import (
    ArrheniusRateFit,
    Rate_,
    RateFit,
    from_chemkin_parse_results,
)
from .data import (
    chemkin_string as rate_constant_chemkin_string,
)


class Reaction(Scalable):
    """Rate class."""

    reactants: list[str]
    products: list[str]
    reversible: bool = True
    rate_constant: Rate_ = pydantic.Field(
        default_factory=lambda data: ArrheniusRateFit(
            A=1, b=0, E=0, order=len(data["reactants"])
        )
    )

    # Private attributes
    _scalers: ClassVar[Scalers] = {"rate_constant": (lambda c, x: c * x)}

    @property
    def unit(self) -> pint.Unit:
        """Unit."""
        return self.rate_constant.unit

    @property
    def third_body(self) -> str | None:
        """Third body."""
        if isinstance(self.rate_constant, RateFit):
            return self.rate_constant.third_body

        return None

    @property
    def is_pressure_dependent(self) -> bool:
        """Whether the rate is pressure dependent."""
        return not isinstance(self.rate_constant, ArrheniusRateFit)

    def __call__(
        self,
        T: ArrayLike,  # noqa: N803
        P: ArrayLike = 1,  # noqa: N803
        units: UnitsData | None = None,
    ) -> NDArray[numpy.float64]:
        """Evaluate rate constant.

        Uses:
        - If temperature and pressure are both numbers, the rate constant will be
          returned as a number, k(T, P).
        - If either temperature or pressure are both lists, the rate constant will be
          returned as a 1D array, [k(T1, P), k(T2, P), ...] or [k(T, P1), k(T, P2), ...]
        - If temperature and pressure are lists, the rate constant will be returned as a
          2D array, [[k(T1, P1), k(T1, P2), ...], [k(T2, P1), k(T2, P2), ...]]

        :param T: Temperature(s)
        :param P: Pressure(s)
        :param units: Input / desired output units
        :return: Value(s)
        """
        return self.rate_constant(T=T, P=P, units=units)


# Constructors
def from_chemkin_string(
    rate_str: str, units: UnitsData | None = None, strict: bool = True
) -> Reaction:
    """Read rate from Chemkin string.

    :param rate_str: Chemkin string
    :param units: Units
    :param strict: Whether to fail if there are unused aux keys
    :return: Rate
    """
    # Parse string
    res = chemkin.parse_rate(rate_str)

    # Extract rate constant
    rate_constant = from_chemkin_parse_results(res, units=units)

    # Check that all information was used
    if strict:
        assert not res.aux_numbers, f"Unused auxiliary values: {res.aux_numbers}"
        assert not res.aux_misc, f"Unused auxiliary values: {res.aux_misc}"
        assert not res.efficiencies, f"Unused efficiencies: {res.efficiencies}"

    # Instantiate object
    return Reaction(
        reactants=res.reactants,
        products=res.products,
        reversible=res.reversible,
        rate_constant=rate_constant,
    )


# Transformations
def expand_lumped(rate: Reaction, exp_dct: Mapping[str, Sequence[str]]) -> list[Reaction]:
    """Expand a lumped reaction rates into its components.

    Assumes an even ratio among unlumped coefficients, in the absence of information.

        unlumped rate coefficient
        = lumped rate coefficient x
            nexp ^ stoich / multiset(nexp, stoich) for each lumped reactant
            1             / multiset(nexp, stoich) for each lumped product

    Here, nexp is the number of components in the lump and stoich is its stoichiometry
    in the reaction.

    There is no physical meaning to the individual rates, and some of the reactions may
    be unphysical. This only serves to reproduce the same net rate while distinguishing
    lump components.

    :param rate: Rate
    :param exp_dct: Mapping of lumped species to lump components
    :return: Component rates
    """

    def _expand(name: str, rev: bool) -> tuple[float, list[dict[int, str]]]:
        """Determine reaction expansion and scale factor for one lumped species.

        Reaction expansion given as list of index -> name mappings representing
        different combinations of lump components.
        """
        # Get species expansion
        exp = exp_dct.get(name)
        if exp is None:
            return 1.0, [{}]

        # Get name combinations
        name_pool = rate.products if rev else rate.reactants
        stoich = name_pool.count(name)
        name_combs = list(itertools.combinations_with_replacement(exp, stoich))
        # Determine factor
        factor = 1.0 if rev else len(exp) ** stoich
        factor /= len(name_combs)
        # Determine reaction expansion dictionaries
        name_idxs = [i for i, n in enumerate(name_pool) if n == name]
        exp_dcts = [
            dict(zip(name_idxs, name_comb, strict=True)) for name_comb in name_combs
        ]
        return factor, exp_dcts

    rexps = [_expand(n, rev=False) for n in set(rate.reactants) if n in exp_dct]
    pexps = [_expand(n, rev=True) for n in set(rate.products) if n in exp_dct]

    rfactors, rexp_dcts = zip(*rexps, strict=True) if rexps else ((), ())
    pfactors, pexp_dcts = zip(*pexps, strict=True) if pexps else ((), ())

    # Scale rate by calculated factor
    rate0 = rate.model_copy()
    rate0 *= math.prod(rfactors + pfactors)

    # Expand reactions
    rexp_combs = [
        {k: v for d in ds for k, v in d.items()} for ds in itertools.product(*rexp_dcts)
    ]
    pexp_combs = [
        {k: v for d in ds for k, v in d.items()} for ds in itertools.product(*pexp_dcts)
    ]
    rates = []
    for rexp_comb, pexp_comb in itertools.product(rexp_combs, pexp_combs):
        rate_ = rate0.model_copy()
        rate_.reactants = [
            rexp_comb.get(i) if i in rexp_comb else s
            for i, s in enumerate(rate0.reactants)
        ]
        rate_.products = [
            pexp_comb.get(i) if i in pexp_comb else s
            for i, s in enumerate(rate0.products)
        ]
        rates.append(rate_)
    return rates


# Conversions
def chemkin_equation(rate: Reaction) -> str:
    """Get Chemkin equation string.

    :param rate: Rate
    :return: Chemkin equation string
    """
    return chemkin.write_equation(
        reactants=rate.reactants,
        products=rate.products,
        reversible=rate.reversible,
        third_body=rate.third_body,
        pressure_dependent=rate.is_pressure_dependent,
    )


def chemkin_string(rate: Reaction, eq_width: int = 55, dup: bool = False) -> str:
    """Get Chemkin rate string.

    :param rate: Rate
    :param eq_width: Width for equation
    :param duplicate: Whether this is a duplicate reaction
    :return: Chemkin rate string
    """
    eq = chemkin_equation(rate)
    rate_str = rate_constant_chemkin_string(rate.rate_constant, eq_width=eq_width)
    reac_str = f"{eq:<{eq_width}} {rate_str}"
    return chemkin.write_with_dup(reac_str, dup=dup)


# Display
def display(
    rate: Reaction,
    comp_rates: Sequence[Reaction] = (),
    comp_labels: Sequence[str] = (),
    T_range: tuple[float, float] = (400, 1250),  # noqa: N803
    P: float = 1,  # noqa: N803
    units: UnitsData | None = None,
    label: str = "This work",
    x_label: str = "1000/T",
    y_label: str = "k",
) -> altair.Chart:
    """Display as an Arrhenius plot, optionally comparing to other rates.

    :param rate: Rate
    :param comp_rates: Rates for comparison
    :param comp_labels: Labels for comparison
    :param t_range: Temperature range
    :param p: Pressure
    :param units: Units
    :param x_label: X-axis label
    :param y_label: Y-axis label
    :return: Chart
    """
    return rate.rate_constant.display(
        others=[r.rate_constant for r in comp_rates],
        labels=comp_labels,
        T_range=T_range,
        P=P,
        units=units,
        label=label,
        x_label=x_label,
        y_label=y_label,
    )
