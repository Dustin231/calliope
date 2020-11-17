"""
Copyright (C) 2013-2019 Calliope contributors listed in AUTHORS.
Licensed under the Apache 2.0 License (see LICENSE file).

capacity.py
~~~~~~~~~~~~~~~~~

Capacity constraints for technologies (output, resource, area, and storage).

"""

import pyomo.core as po  # pylint: disable=import-error
import numpy as np

from calliope.backend.pyomo.util import get_param
from calliope import exceptions


def get_capacity_constraint(
    backend_model, parameter, node, tech, _equals=None, _max=None, _min=None, scale=None
):

    decision_variable = getattr(backend_model, parameter)

    if not _equals:
        _equals = get_param(backend_model, parameter + "_equals", (node, tech))
    if not _max:
        _max = get_param(backend_model, parameter + "_max", (node, tech))
    if not _min:
        _min = get_param(backend_model, parameter + "_min", (node, tech))
    if po.value(_equals) is not False and po.value(_equals) is not None:
        if np.isinf(po.value(_equals)):
            e = exceptions.ModelError
            raise e(f"Cannot use inf for {parameter}_equals for `{tech}` at `{node}`")
        if scale:
            _equals *= scale
        return decision_variable[node, tech] == _equals
    else:
        if po.value(_min) == 0 and np.isinf(po.value(_max)):
            return po.Constraint.NoConstraint
        else:
            if scale:
                _max *= scale
                _min *= scale
            return (_min, decision_variable[node, tech], _max)


def storage_capacity_constraint_rule(backend_model, node, tech):
    """
    Set maximum storage capacity. Supply_plus & storage techs only

    The first valid case is applied:

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{storage_{cap}}(loc::tech)
            \\begin{cases}
                = storage_{cap, equals}(loc::tech),& \\text{if } storage_{cap, equals}(loc::tech)\\\\
                \\leq storage_{cap, max}(loc::tech),& \\text{if } storage_{cap, max}(loc::tech)\\\\
                \\text{unconstrained},& \\text{otherwise}
            \\end{cases}
            \\forall loc::tech \\in loc::techs_{store}

    and (if ``equals`` not enforced):

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{storage_{cap}}(loc::tech) \\geq storage_{cap, min}(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs_{store}

    """
    return get_capacity_constraint(backend_model, "storage_cap", node, tech)


def energy_capacity_storage_constraint_rule_old(backend_model, node, tech):
    """
    Set an additional energy capacity constraint on storage technologies,
    based on their use of `charge_rate`.

    This is deprecated and will be removed in Calliope 0.7.0. Instead of
    `charge_rate`, please use `energy_cap_per_storage_cap_max`.

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{energy_{cap}}(loc::tech)
            \\leq \\boldsymbol{storage_{cap}}(loc::tech) \\times charge\\_rate(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs_{store}

    """
    charge_rate = get_param(backend_model, "charge_rate", (node, tech))

    return backend_model.energy_cap[node, tech] <= (
        backend_model.storage_cap[node, tech] * charge_rate
    )


def energy_capacity_storage_min_constraint_rule(backend_model, node, tech):
    """
    Limit energy capacities of storage technologies based on their storage capacities.

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{energy_{cap}}(loc::tech)
                \\geq \\boldsymbol{storage_{cap}}(loc::tech) \\times energy\\_cap\\_per\\_storage\\_cap\\_min(loc::tech)\\\\
            \\forall loc::tech \\in loc::techs_{store}

    """
    return backend_model.energy_cap[node, tech] >= (
        backend_model.storage_cap[node, tech]
        * get_param(backend_model, "energy_cap_per_storage_cap_min", (node, tech))
    )


def energy_capacity_storage_max_constraint_rule(backend_model, node, tech):
    """
    Limit energy capacities of storage technologies based on their storage capacities.

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{energy_{cap}}(loc::tech)
                \\leq \\boldsymbol{storage_{cap}}(loc::tech) \\times energy\\_cap\\_per\\_storage\\_cap\\_max(loc::tech)\\\\
            \\forall loc::tech \\in loc::techs_{store}

    """
    return backend_model.energy_cap[node, tech] <= (
        backend_model.storage_cap[node, tech]
        * get_param(backend_model, "energy_cap_per_storage_cap_max", (node, tech))
    )


def energy_capacity_storage_equals_constraint_rule(backend_model, node, tech):
    """
    Limit energy capacities of storage technologies based on their storage capacities.

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{energy_{cap}}(loc::tech)
                = \\boldsymbol{storage_{cap}}(loc::tech) \\times energy\\_cap\\_per\\_storage\\_cap\\_equals(loc::tech)
            \\forall loc::tech \\in loc::techs_{store}

    """
    return backend_model.energy_cap[node, tech] == (
        backend_model.storage_cap[node, tech]
        * get_param(backend_model, "energy_cap_per_storage_cap_equals", (node, tech))
    )


def resource_capacity_constraint_rule(backend_model, node, tech):
    """
    Add upper and lower bounds for resource_cap.

    The first valid case is applied:

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{cap}}(loc::tech)
            \\begin{cases}
                = resource_{cap, equals}(loc::tech),& \\text{if } resource_{cap, equals}(loc::tech)\\\\
                \\leq resource_{cap, max}(loc::tech),& \\text{if } resource_{cap, max}(loc::tech)\\\\
                \\text{unconstrained},& \\text{otherwise}
            \\end{cases}
            \\forall loc::tech \\in loc::techs_{finite\\_resource\\_supply\\_plus}

    and (if ``equals`` not enforced):

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{cap}}(loc::tech) \\geq resource_{cap, min}(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs_{finite\\_resource\\_supply\\_plus}
    """

    return get_capacity_constraint(backend_model, "resource_cap", node, tech)


def resource_capacity_equals_energy_capacity_constraint_rule(backend_model, node, tech):
    """
    Add equality constraint for resource_cap to equal energy_cap, for any technologies
    which have defined resource_cap_equals_energy_cap.

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{cap}}(loc::tech) = \\boldsymbol{energy_{cap}}(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs_{finite\\_resource\\_supply\\_plus}
            \\text{ if } resource\\_cap\\_equals\\_energy\\_cap = \\text{True}
    """
    return (
        backend_model.resource_cap[node, tech] == backend_model.energy_cap[node, tech]
    )


def resource_area_constraint_rule(backend_model, node, tech):
    """
    Set upper and lower bounds for resource_area.

    The first valid case is applied:

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{area}}(loc::tech)
            \\begin{cases}
                = resource_{area, equals}(loc::tech),& \\text{if } resource_{area, equals}(loc::tech)\\\\
                \\leq resource_{area, max}(loc::tech),& \\text{if } resource_{area, max}(loc::tech)\\\\
                \\text{unconstrained},& \\text{otherwise}
            \\end{cases}
            \\forall loc::tech \\in loc::techs_{area}

    and (if ``equals`` not enforced):

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{area}}(loc::tech) \\geq resource_{area, min}(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs_{area}
    """
    energy_cap_max = get_param(backend_model, "energy_cap_max", (node, tech))
    area_per_energy_cap = get_param(
        backend_model, "resource_area_per_energy_cap", (node, tech)
    )

    if po.value(energy_cap_max) == 0 and not po.value(area_per_energy_cap):
        # If a technology has no energy_cap here, we force resource_area to zero,
        # so as not to accrue spurious costs
        return backend_model.resource_area[node, tech] == 0
    else:
        return get_capacity_constraint(backend_model, "resource_area", node, tech)


def resource_area_per_energy_capacity_constraint_rule(backend_model, node, tech):
    """
    Add equality constraint for resource_area to equal a percentage of energy_cap,
    for any technologies which have defined resource_area_per_energy_cap

    .. container:: scrolling-wrapper

        .. math::

            \\boldsymbol{resource_{area}}(loc::tech) =
            \\boldsymbol{energy_{cap}}(loc::tech) \\times area\\_per\\_energy\\_cap(loc::tech)
            \\quad \\forall loc::tech \\in locs::techs_{area} \\text{ if } area\\_per\\_energy\\_cap(loc::tech)
    """
    area_per_energy_cap = get_param(
        backend_model, "resource_area_per_energy_cap", (node, tech)
    )

    return (
        backend_model.resource_area[node, tech]
        == backend_model.energy_cap[node, tech] * area_per_energy_cap
    )


def resource_area_capacity_per_loc_constraint_rule(backend_model, node):
    """
    Set upper bound on use of area for all locations which have `available_area`
    constraint set. Does not consider resource_area applied to demand technologies

    .. container:: scrolling-wrapper

        .. math::

            \\sum_{tech} \\boldsymbol{resource_{area}}(loc::tech) \\leq available\\_area
            \\quad \\forall loc \\in locs \\text{ if } available\\_area(loc)
    """
    available_area = backend_model.available_area[node]

    return sum(backend_model.resource_area[node, :]) <= available_area


def energy_capacity_constraint_rule(backend_model, node, tech):
    """
    Set upper and lower bounds for energy_cap.

    The first valid case is applied:

    .. container:: scrolling-wrapper

        .. math::

            \\frac{\\boldsymbol{energy_{cap}}(loc::tech)}{energy_{cap, scale}(loc::tech)}
            \\begin{cases}
                = energy_{cap, equals}(loc::tech),& \\text{if } energy_{cap, equals}(loc::tech)\\\\
                \\leq energy_{cap, max}(loc::tech),& \\text{if } energy_{cap, max}(loc::tech)\\\\
                \\text{unconstrained},& \\text{otherwise}
            \\end{cases}
            \\forall loc::tech \\in loc::techs

    and (if ``equals`` not enforced):

    .. container:: scrolling-wrapper

        .. math::

            \\frac{\\boldsymbol{energy_{cap}}(loc::tech)}{energy_{cap, scale}(loc::tech)}
            \\geq energy_{cap, min}(loc::tech)
            \\quad \\forall loc::tech \\in loc::techs
    """
    scale = get_param(backend_model, "energy_cap_scale", (node, tech))
    return get_capacity_constraint(backend_model, "energy_cap", node, tech, scale=scale)


def energy_capacity_systemwide_constraint_rule(backend_model, tech):
    """
    Set constraints to limit the capacity of a single technology type across all locations in the model.

    The first valid case is applied:

    .. container:: scrolling-wrapper

        .. math::

            \\sum_{loc}\\boldsymbol{energy_{cap}}(loc::tech)
            \\begin{cases}
                = energy_{cap, equals, systemwide}(loc::tech),&
                    \\text{if } energy_{cap, equals, systemwide}(loc::tech)\\\\
                \\leq energy_{cap, max, systemwide}(loc::tech),&
                    \\text{if } energy_{cap, max, systemwide}(loc::tech)\\\\
                \\text{unconstrained},& \\text{otherwise}
            \\end{cases}
            \\forall tech \\in techs

    """

    max_systemwide = get_param(backend_model, "energy_cap_max_systemwide", tech)
    equals_systemwide = get_param(backend_model, "energy_cap_equals_systemwide", tech)
    energy_cap = po.quicksum(
        backend_model.energy_cap[node, tech]
        for node in backend_model.nodes
        if [node, tech] in backend_model.energy_cap_index
    )
    if equals_systemwide:
        return energy_cap == equals_systemwide
    else:
        return energy_cap <= max_systemwide
