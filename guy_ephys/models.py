"""Cell template class"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


# pylint: disable=W0511

# TODO take into account that one might want to run protocols on different
# machines
# TODO rename this to 'CellModel' -> definitely

import collections
import pdb

import logging
logger = logging.getLogger(__name__)


class CellModel(object):

    """Cell model class"""

    def __init__(
            self,
            name,
            morph=None,
            mechs=None,
            params=None):
        """Constructor"""

        self.name = name

        # morphology
        self.morphology = morph
        # mechanisms
        self.mechanisms = mechs
        # Model params
        self.params = collections.OrderedDict()
        for param in params:
            self.params[param.name] = param

        # Cell instantiation in simulator
        self.icell = None

        self.param_values = None

    def freeze(self, param_dict):
        """Set params"""

        for param_name, param_value in param_dict.items():
            self.params[param_name].freeze(param_value)

    def unfreeze(self, param_names):
        """Unset params"""

        for param_name in param_names:
            self.params[param_name].unfreeze()

    @staticmethod
    def create_empty_cell(name, sim=None):
        """Create an empty cell in Neuron"""

        # TODO minize hardcoded definition
        # E.g. sectionlist can be procedurally generated
        template_content = 'begintemplate %s\n' \
            'objref all, apical, basal, somatic, axonal\n' \
            'proc init() {\n' \
            'all 	= new SectionList()\n' \
            'somatic = new SectionList()\n' \
            'basal 	= new SectionList()\n' \
            'apical 	= new SectionList()\n' \
            'axonal 	= new SectionList()\n' \
            'forall delete_section()\n' \
            '}\n' \
            'create soma[1], dend[1], apic[1], axon[1]\n' \
            'endtemplate %s\n' % (name, name)

        sim.neuron.h(template_content)

        template_function = getattr(sim.neuron.h, name)

        return template_function()

    def instantiate(self, sim=None):
        """Instantiate model in simulator"""

        sim.neuron.h.load_file('stdrun.hoc')

        # TODO replace this with the real template name
        if not hasattr(sim.neuron.h, 'Cell'):
            self.icell = self.create_empty_cell('Cell', sim=sim)
        else:
            self.icell = sim.neuron.h.Cell()

        self.morphology.instantiate(sim=sim, icell=self.icell)

        for mechanism in self.mechanisms:
            mechanism.instantiate(sim=sim, icell=self.icell)
        for param in self.params.values():
            param.instantiate(sim=sim, icell=self.icell)

        print self.icell.soma[0].g_pas
        self.guy_hack(sim)
    def guy_hack(self,sim):
        RM = 38907
        F = 1.9
        CM = 0.45
        RM = 38907
        StepDist = 60
        soma = self.icell.soma[0]
        h = sim.neuron.h
        h.distance(0,0.5,sec=soma)
        for sec in self.icell.basal:
            for seg in sec:
                if h.distance(seg.x,sec=sec)>StepDist:
                    seg.cm=CM*F
                    seg.g_pas=(1.0/RM)*F
        for sec in self.icell.apical:
            for seg in sec:
                if h.distance(seg.x,sec=sec)>StepDist:
                    seg.cm=CM*F
                    seg.g_pas=(1.0/RM)*F

     

    def destroy(self):
        """Destroy instantiated model in simulator"""

        self.icell = None
        self.morphology.destroy()
        for mechanism in self.mechanisms:
            mechanism.destroy()
        for param in self.params.values():
            param.destroy()

    def check_nonfrozen_params(self, param_names):
        """Check if all nonfrozen params are set"""

        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    'CellModel: Nonfrozen param %s needs to be '
                    'set before simulation' %
                    param_name)

    def __str__(self):
        """Return string representation"""

        content = '%s:\n' % self.name

        content += '  morphology:\n'
        content += '    %s\n' % str(self.morphology)

        content += '  mechanisms:\n'
        for mechanism in self.mechanisms:
            content += '    %s\n' % mechanism
        content += '  params:\n'
        for param in self.params.values():
            content += '    %s\n' % param

        return content
