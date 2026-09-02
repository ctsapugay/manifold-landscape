"""Linear algebra as geometry: eigen, determinant, SVD (L1–L3)."""

import numpy as np

from engine.linalg import LinearTransformation


def test_symmetric_L1():
    """A = [[2,1],[1,2]]: eigenvalues 3 and 1, det 3, not defective."""
    T = LinearTransformation([[2, 1], [1, 2]])
    sol = T.solve("L1", "Symmetric", want=("determinant", "eigen")).require_verified()
    assert abs(sol.get("determinant").value - 3.0) < 1e-9
    eig = sol.get("eigen").value
    vals = sorted(round(p["eigenvalue"][0]) for p in eig["pairs"])
    assert vals == [1, 3]
    assert eig["defective"] is False


def test_shear_L2():
    """A = [[1,1],[0,1]]: det 1, single eigenvalue 1, defective (geometric<algebraic)."""
    T = LinearTransformation([[1, 1], [0, 1]])
    sol = T.solve("L2", "Shear", want=("determinant", "eigen")).require_verified()
    assert abs(sol.get("determinant").value - 1.0) < 1e-9
    eig = sol.get("eigen").value
    assert eig["defective"] is True
    assert all(abs(p["eigenvalue"][0] - 1.0) < 1e-9 for p in eig["pairs"])


def test_svd_L3():
    """A general 3x3: SVD reconstructs A, singular values are the ellipsoid semi-axes."""
    A = [[1, 2, 0], [0, 1, 2], [2, 0, 1]]
    T = LinearTransformation(A)
    q = T.svd()
    assert q.verified
    S = q.value["singular_values"]
    assert len(S) == 3 and all(s > 0 for s in S)
    # independent reconstruction check
    U = np.array(q.value["U"]); Vt = np.array(q.value["Vt"])
    recon = U @ np.diag(S) @ Vt
    assert np.allclose(recon, np.array(A, dtype=float), atol=1e-9)
