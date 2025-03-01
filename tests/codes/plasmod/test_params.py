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

import os

import pytest

from bluemira.codes.plasmod.params import ParameterMapping, PlasmodSolverParams

PARAM_FILE = os.path.join(os.path.dirname(__file__), "data", "params.json")


class TestProcessSolverParams:
    params = PlasmodSolverParams.from_json(PARAM_FILE)

    @pytest.mark.parametrize("param", params, ids=lambda p: p.name)
    def test_mapping_defined_for_param(self, param):
        assert isinstance(self.params.mappings[param.name], ParameterMapping)
