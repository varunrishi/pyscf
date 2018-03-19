#!/usr/bin/env python
# Copyright 2014-2018 The PySCF Developers. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: James D. McClain
#          Timothy Berkelbach <tim.berkelbach@gmail.com>
#

#import unittest
import unittest
import numpy as np

from pyscf import gto, scf

from pyscf.pbc import gto as pbcgto
from pyscf.pbc import scf as pbchf
from pyscf.pbc.ao2mo import eris
import pyscf.pbc.tools

import pyscf.pbc.cc
import pyscf.pbc.cc.kccsd_t as kccsd_t
import pyscf.pbc.cc.kccsd

import make_test_cell

def run_kcell(cell, n, nk):
    abs_kpts = cell.make_kpts(nk, wrap_around=True)

    # RHF calculation
    kmf = pbchf.KRHF(cell, abs_kpts, exxdiv=None)
    kmf.conv_tol = 1e-14
    ekpt = kmf.scf()

    # RCCSD calculation
    cc = pyscf.pbc.cc.kccsd.CCSD(pbchf.addons.convert_to_ghf(kmf))
    cc.conv_tol = 1e-8
    ecc, t1, t2 = cc.kernel()
    return ekpt, ecc

class KnownValues(unittest.TestCase):
    def test_111_n0(self):
        L = 10.0
        n = 11
        cell = make_test_cell.test_cell_n0(L,[n]*3)
        nk = (1, 1, 1)
        hf_111 = -0.73491491306419987
        cc_111 = -1.1580008204825658e-05
        escf, ecc = run_kcell(cell,n,nk)
        self.assertAlmostEqual(escf,hf_111,9)
        self.assertAlmostEqual(ecc, cc_111,6)

    def test_111_n1(self):
        L = 7.0
        n = 9
        cell = make_test_cell.test_cell_n1(L,[n]*3)
        nk = (1, 1, 1)
        hf_111 = -0.73506011036963814
        cc_111 = -0.023265431169472835
        escf, ecc = run_kcell(cell,n,nk)
        self.assertAlmostEqual(escf,hf_111,9)
        self.assertAlmostEqual(ecc, cc_111,6)

    def test_111_n3(self):
        n = 11
        cell = make_test_cell.test_cell_n3([n]*3)
        nk = (1, 1, 1)
        hf_111 = -7.4117951240232118
        cc_111 = -0.19468901057053406
        escf, ecc = run_kcell(cell,n,nk)
        self.assertAlmostEqual(escf,hf_111,9)
        self.assertAlmostEqual(ecc, cc_111,6)

    def test_311_n1(self):
        L = 7.0
        n = 9
        cell = make_test_cell.test_cell_n1(L,[n]*3)
        nk = (3, 1, 1)
        hf_311 = -0.92687629918229486
        cc_311 = -0.042702177586414237
        escf, ecc = run_kcell(cell,n,nk)
        self.assertAlmostEqual(escf,hf_311, 9)
        self.assertAlmostEqual(ecc, cc_311, 6)

    def test_frozen_n3(self):
        mesh = 5
        cell = make_test_cell.test_cell_n3([mesh]*3)
        nk = (1, 1, 3)
        ehf_bench = -9.15349763559837
        ecc_bench = -0.06713556649654

        abs_kpts = cell.make_kpts(nk, with_gamma_point=True)

        # RHF calculation
        kmf = pbchf.KRHF(cell, abs_kpts, exxdiv=None)
        ehf = kmf.scf()

        # KGCCSD calculation, equivalent to running supercell
        # calculation with frozen=[0,1,2] (if done with larger mesh)
        cc = pyscf.pbc.cc.kccsd.CCSD(kmf, frozen=[[0,1],[],[0]])
        ecc, t1, t2 = cc.kernel()
        self.assertAlmostEqual(ehf, ehf_bench, 9)
        self.assertAlmostEqual(ecc, ecc_bench, 9)

    def test_frozen_n3(self):
        mesh = 5
        cell = make_test_cell.test_cell_n3([mesh]*3)
        nk = (1, 1, 3)
        ehf_bench = -9.15349763559837
        ecc_bench = -0.06713556649654

        abs_kpts = cell.make_kpts(nk, with_gamma_point=True)

        # RHF calculation
        kmf = pbchf.KRHF(cell, abs_kpts, exxdiv=None)
        ehf = kmf.scf()

        # KGCCSD calculation, equivalent to running supercell
        # calculation with frozen=[0, 1, 2] (if done with larger mesh)
        cc = pyscf.pbc.cc.kccsd.CCSD(kmf, frozen=[[0,1],[],[0]])
        ecc, t1, t2 = cc.kernel()
        self.assertAlmostEqual(ehf, ehf_bench, 9)
        self.assertAlmostEqual(ecc, ecc_bench, 9)

    def test_cu_metallic(self):
        mesh = 7
        cell = make_test_cell.test_cell_cu_metallic([mesh]*3)
        nk = [1,1,2]
        ehf_bench = -52.5393701339723
        ecc1_bench = -1.1633910051553982
        ecc2_bench = -1.0430822430909346

        # KRHF calculation
        kmf = pbchf.KRHF(cell, exxdiv=None)
        kmf.kpts = cell.make_kpts(nk, scaled_center=[0.0, 0.0, 0.0], wrap_around=True)
        kmf.conv_tol_grad = 1e-6  # Stricter tol needed for answer to agree with supercell
        ehf = kmf.scf()

        self.assertAlmostEqual(ehf, ehf_bench, 6)

        # The following calculation at full convergence gives -0.711071910294612
        # for a cell.mesh = [25, 25, 25].
        mycc = pyscf.pbc.cc.KGCCSD(kmf, frozen=0)
        mycc.iterative_damping = 0.04
        mycc.max_cycle = 2  # Too expensive to do more!
        ecc1, t1, t2 = mycc.kernel()

        self.assertAlmostEqual(ecc1, ecc1_bench, 6)

        # The following calculation at full convergence gives -0.6440448716452378
        # for a cell.mesh = [25, 25, 25].  It is equivalent to a supercell [1, 1, 2]
        # calculation with frozen = [0, 3].
        mycc = pyscf.pbc.cc.KGCCSD(kmf, frozen=[[2, 3], [0, 1]])
        mycc.iterative_damping = 0.04
        mycc.max_cycle = 2
        ecc2, t1, t2 = mycc.kernel()

        self.assertAlmostEqual(ecc2, ecc2_bench, 6)

    def test_ccsd_t(self):
        n = 14
        cell = make_test_cell.test_cell_n3([n]*3)

        kpts = cell.make_kpts([1, 1, 2])
        kpts -= kpts[0]
        kmf = pbchf.KRHF(cell, kpts=kpts, exxdiv=None)
        ehf = kmf.kernel()

        mycc = pyscf.pbc.cc.KGCCSD(kmf)
        ecc, t1, t2 = mycc.kernel()

        energy_t = kccsd_t.kernel(mycc)
        energy_t_bench = -0.00191440345386
        self.assertAlmostEqual(energy_t, energy_t_bench, 6)

if __name__ == '__main__':
    print("Full kpoint test")
    unittest.main()

