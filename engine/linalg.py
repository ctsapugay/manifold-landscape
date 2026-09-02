"""Linear algebra as geometry: a matrix as a transformation of space.

Quantities:
  * **determinant** — the signed area/volume scale factor (exact via SymPy, confirmed
    against NumPy's numeric determinant);
  * **eigen-structure** — invariant directions and their scalings (exact eigenvalues,
    eigenvectors and algebraic/geometric multiplicities via SymPy, each confirmed by the
    numeric residual ‖A·v − λ·v‖); a defective matrix is detected as geometric < algebraic
    multiplicity;
  * **SVD** — the singular values and vectors that turn the unit sphere into an ellipsoid,
    confirmed by the reconstruction residual ‖A − UΣVᵀ‖ and the orthonormality of U and V.
"""

from __future__ import annotations

import numpy as np
import sympy as sp

from .result import Quantity, Solution, Verification
from .verify import (
    eig_residual,
    orthonormality_residual,
    svd_reconstruction_residual,
)


class LinearTransformation:
    def __init__(self, matrix):
        self.A = np.asarray(matrix, dtype=float)
        # Build the SymPy matrix from the ORIGINAL entries and rationalize, so exact
        # eigen-structure (e.g. a defective shear) is detected. Building it from the
        # float ndarray would hide the defect behind floating-point noise.
        self.M = sp.Matrix(matrix).applyfunc(lambda e: sp.nsimplify(e, rational=True))
        self.rows, self.cols = self.A.shape

    # --- determinant ------------------------------------------------------------

    def determinant(self) -> Quantity:
        if self.rows != self.cols:
            raise ValueError("determinant needs a square matrix")
        exact = self.M.det()
        numeric = float(np.linalg.det(self.A))
        resid = abs(float(exact) - numeric)
        return Quantity(
            name="determinant",
            kind="scalar",
            value=float(exact),
            display=f"det A = {sp.nsimplify(exact)} (area/volume scale factor)",
            provenance="sympy.Matrix.det",
            verification=Verification.from_residual(
                "numeric determinant (numpy.linalg.det)", resid, 1e-9,
                detail=f"exact {exact}, numeric {numeric:.6g}",
            ),
        )

    # --- eigen-structure --------------------------------------------------------

    def eigen(self) -> Quantity:
        if self.rows != self.cols:
            raise ValueError("eigen-structure needs a square matrix")
        pairs = []
        worst = 0.0
        alg_total = 0
        geo_total = 0
        for eigval, alg_mult, vecs in self.M.eigenvects():
            alg_total += alg_mult
            geo_total += len(vecs)
            lam = complex(eigval)
            for v in vecs:
                vv = np.array([complex(c) for c in v], dtype=complex).reshape(-1)
                vv = vv / np.linalg.norm(vv)
                worst = max(worst, eig_residual(self.A.astype(complex), lam, vv))
                pairs.append({
                    "eigenvalue": [lam.real, lam.imag],
                    "eigenvector": [[c.real, c.imag] for c in vv],
                    "algebraic_multiplicity": int(alg_mult),
                })
        defective = geo_total < alg_total
        return Quantity(
            name="eigen",
            kind="matrix",
            value={
                "pairs": pairs,
                "defective": defective,
                "algebraic_total": alg_total,
                "geometric_total": geo_total,
            },
            display=("eigenvalues "
                     + ", ".join(str(sp.nsimplify(p["eigenvalue"][0])) for p in pairs)
                     + (" (defective — repeated direction)" if defective else "")),
            provenance="sympy.Matrix.eigenvects",
            verification=Verification.from_residual(
                "eigen residual ‖A·v − λ·v‖ over all returned pairs", worst, 1e-9,
                detail=f"alg={alg_total}, geo={geo_total}, defective={defective}",
            ),
        )

    # --- singular value decomposition -------------------------------------------

    def svd(self) -> Quantity:
        U, S, Vt = np.linalg.svd(self.A)
        recon = svd_reconstruction_residual(self.A, U, S, Vt)
        ortho = max(orthonormality_residual(U), orthonormality_residual(Vt.T))
        resid = max(recon, ortho)
        return Quantity(
            name="svd",
            kind="matrix",
            value={
                "U": U.tolist(),
                "singular_values": [float(s) for s in S],
                "Vt": Vt.tolist(),
                "reconstruction_residual": float(recon),
                "orthonormality_residual": float(ortho),
            },
            display=("singular values "
                     + ", ".join(f"{s:.4g}" for s in S)
                     + " (semi-axes of the image ellipsoid)"),
            provenance="numpy.linalg.svd",
            verification=Verification.from_residual(
                "reconstruction ‖A−UΣVᵀ‖ and orthonormality of U, V", resid, 1e-9,
                detail=f"reconstruction {recon:.2e}, orthonormality {ortho:.2e}",
            ),
        )

    def solve(self, problem_id: str, title: str, want=("determinant", "eigen")) -> Solution:
        sol = Solution(problem_id=problem_id, area="linear-algebra", title=title)
        step = 0
        for name in want:
            step += 1
            q = getattr(self, name)()
            sol.add(q)
            sol.steps.append({"step": step, "introduces": name, "quantity": name})
        return sol
