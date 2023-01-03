# bluemira is an integrated inter-disciplinary design tool for future fusion
# reactors. It incorporates several modules, some of which rely on other
# codes, to carry out a range of typical conceptual fusion reactor design
# activities.
#
# Copyright (C) 2021-2023 M. Coleman, J. Cook, F. Franza, I.A. Maione, S. McIntosh,
#                         J. Morris, D. Short
#
# bluemira is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# bluemira is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with bluemira; if not, see <https://www.gnu.org/licenses/>.

"""
Material mixture utility classes
"""
import copy
import typing
import warnings

import numpy as np

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    import neutronics_material_maker as nmm

from bluemira.base.look_and_feel import bluemira_warn
from bluemira.materials.constants import T_DEFAULT
from bluemira.materials.error import MaterialsError
from bluemira.materials.material import SerialisedMaterial


class HomogenisedMixture(SerialisedMaterial, nmm.MultiMaterial):
    """
    Inherits and does some dropping of 0 fractions (avoid touching nmm)
    """

    materials: typing.Dict[str, float]
    temperature_in_K: float  # noqa :N815
    enrichment: float

    default_temperature = T_DEFAULT
    _material_classes = []

    def __init__(
        self,
        name,
        materials,
        temperature_in_K=None,  # noqa :N803
        enrichment=None,
        zaid_suffix=None,
        material_id=None,
    ):
        if temperature_in_K is None:
            temperature_in_K = self.default_temperature  # noqa :N803

        mats = []
        for mat in materials.keys():
            mat.temperature = temperature_in_K
            if "enrichment" in mat.__class__.__annotations__:
                mat.enrichment = enrichment
            mats += [mat]

        super().__init__(
            material_tag=name,
            materials=mats,
            fracs=list(materials.values()),
            percent_type="vo",
            temperature_in_K=temperature_in_K,
            zaid_suffix=zaid_suffix,
            material_id=material_id,
        )

        self.name = name

    def __str__(self):
        """
        Get the name of the mixture.
        """
        return self.name

    def _calc_homogenised_property(self, prop: str, temperature: float):
        """
        Calculate an mass-fraction-averaged property for the homogenised mixture.
        """
        warn = []
        values, fractions = [], []
        # Calculate property mixtures, ignoring liquids and voids
        # for certain properties
        for mat, vf in zip(self.materials, self.fracs):
            try:
                v = getattr(mat, prop)(temperature)
                values.append(v)
                fractions.append(vf)
            except (NotImplementedError, AttributeError, MaterialsError):
                warn.append([mat, prop])

        f = np.array(fractions) / sum(fractions)  # Normalised
        value = np.dot(values, f)

        if warn:
            txt = (
                f"Materials::{self.__class__.__name__}: The following "
                + "mat.prop calls failed:\n"
            )
            for w in warn:
                txt += f"{w[0]}: {w[1]}" + "\n"
            bluemira_warn(txt)

        return value

    def E(self, temperature):  # noqa :N802
        """
        Young's modulus.

        Parameters
        ----------
        temperature: float
            The optional temperature [K].

        Returns
        -------
        youngs_modulus: float
            The Young's modulus of the material at the given temperature.
        """
        return self._calc_homogenised_property("E", temperature)

    def mu(self, temperature):
        """
        Poisson's ratio.

        Parameters
        ----------
        temperature: float
            The optional temperature [K].

        Returns
        -------
        poissons_ratio: float
            Poisson's ratio for the material at the given temperature.
        """
        return self._calc_homogenised_property("mu", temperature)

    def CTE(self, temperature):  # noqa :N802
        """
        Mean coefficient of thermal expansion in 10**-6/T

        Parameters
        ----------
        temperature: float
            The temperature in Kelvin

        Returns
        -------
        cte: float
            Mean coefficient of thermal expansion in 10**-6/T at the given temperature.
        """
        return self._calc_homogenised_property("CTE", temperature)

    def rho(self, temperature):
        """
        Density.

        Parameters
        ----------
        temperature: float
            The optional temperature [K].

        Returns
        -------
        density: float
            The density of the material at the given temperature.
        """
        return self._calc_homogenised_property("rho", temperature)

    def Sy(self, temperature):  # noqa :N802
        """
        Minimum yield stress in MPa

        Parameters
        ----------
        temperature: float
            The temperature in Kelvin

        Returns
        -------
        sy: float
            Minimum yield stress in MPa at the given temperature.
        """
        return self._calc_homogenised_property("Sy", temperature)

    @classmethod
    def from_dict(cls, name, material_dict, material_cache):
        """
        Generate an instance of the mixture from a dictionary of materials.

        Parameters
        ----------
        name : str
            The name of the mixture.
        materials_dict: Dict[str, Any]
            The dictionary defining this and any additional mixtures.
        material_cache: MaterialCache
            The cache to load the constituent materials from.

        Returns
        -------
        mixture : SerialisedMaterial
            The mixture.
        """
        mat_dict = copy.deepcopy(material_dict[name])
        if "materials" not in material_dict[name].keys():
            raise MaterialsError("Mixture must define constituent materials.")

        for mat in material_dict[name]["materials"]:
            if isinstance(mat, str):
                del mat_dict["materials"][mat]
                material_inst = material_cache.get_material(mat, False)
                material_value = material_dict[name]["materials"][mat]
                mat_dict["materials"][material_inst] = material_value

        return super().from_dict(name, {name: mat_dict})
