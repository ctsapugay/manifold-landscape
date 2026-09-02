"""Independent verification primitives.

These are the *second route* to a value — the one that has to agree with the engine's
primary (usually symbolic) computation before a quantity is allowed to surface. They are
deliberately dumb and direct: finite differences, residual norms, back-substitution.
Their independence from the primary method is the point; that two unrelated computations
agree is what makes a result trustworthy rather than merely asserted (C-VERIFIED-MATH).
"""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

# Default tolerances. Symbolic-vs-analytic comparisons can be near-exact; finite-
# difference comparisons carry truncation error, so they get a looser bound.
TOL_EXACT = 1e-9
TOL_NUMERIC = 1e-6
TOL_FINITE_DIFF = 1e-5


def as_vector(v) -> np.ndarray:
    return np.asarray(v, dtype=float).reshape(-1)


def as_matrix(m) -> np.ndarray:
    return np.asarray(m, dtype=float)


def max_abs(a) -> float:
    a = np.asarray(a, dtype=float)
    return float(np.max(np.abs(a))) if a.size else 0.0


def numeric_gradient(f: Callable[[np.ndarray], float], point: Sequence[float], h: float = 1e-5) -> np.ndarray:
    """Central-difference gradient of a scalar function of n variables at ``point``.

    Independent of any symbolic differentiation: it only ever *evaluates* f.
    """
    p = as_vector(point)
    g = np.zeros_like(p)
    for i in range(p.size):
        step = np.zeros_like(p)
        step[i] = h
        g[i] = (f(p + step) - f(p - step)) / (2 * h)
    return g


def numeric_hessian(f: Callable[[np.ndarray], float], point: Sequence[float], h: float = 1e-4) -> np.ndarray:
    """Central-difference Hessian of a scalar function at ``point`` (evaluations only)."""
    p = as_vector(point)
    n = p.size
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            ei = np.zeros(n); ei[i] = h
            ej = np.zeros(n); ej[j] = h
            H[i, j] = (
                f(p + ei + ej) - f(p + ei - ej) - f(p - ei + ej) + f(p - ei - ej)
            ) / (4 * h * h)
    return H


def numeric_jacobian(F: Callable[[np.ndarray], np.ndarray], point: Sequence[float], h: float = 1e-5) -> np.ndarray:
    """Central-difference Jacobian of a vector field F: R^n -> R^m at ``point``."""
    p = as_vector(point)
    base = as_vector(F(p))
    m = base.size
    J = np.zeros((m, p.size))
    for i in range(p.size):
        step = np.zeros_like(p); step[i] = h
        J[:, i] = (as_vector(F(p + step)) - as_vector(F(p - step))) / (2 * h)
    return J


def divergence_fd(F: Callable[[np.ndarray], np.ndarray], point: Sequence[float], h: float = 1e-5) -> float:
    """Divergence by finite differences: trace of the numeric Jacobian."""
    return float(np.trace(numeric_jacobian(F, point, h)))


def curl_fd(F: Callable[[np.ndarray], np.ndarray], point: Sequence[float], h: float = 1e-5) -> np.ndarray:
    """Curl by finite differences. Returns the z-component (as a 1-vector) in 2-D,
    or the full (curl_x, curl_y, curl_z) vector in 3-D."""
    J = numeric_jacobian(F, point, h)
    if J.shape == (2, 2):
        return np.array([J[1, 0] - J[0, 1]])
    if J.shape == (3, 3):
        return np.array([
            J[2, 1] - J[1, 2],
            J[0, 2] - J[2, 0],
            J[1, 0] - J[0, 1],
        ])
    raise ValueError(f"curl is defined here for 2-D or 3-D fields, got Jacobian {J.shape}")


def residual_norm(a, b) -> float:
    """Max-abs discrepancy between two array-likes of the same shape."""
    return max_abs(as_matrix(a) - as_matrix(b))


def eig_residual(A, eigval, eigvec) -> float:
    """‖A·v − λ·v‖∞ — how well (λ, v) satisfies the eigen equation. Complex-safe."""
    A = np.asarray(A, dtype=complex)
    v = np.asarray(eigvec, dtype=complex).reshape(-1)
    return float(np.max(np.abs(A @ v - complex(eigval) * v)))


def svd_reconstruction_residual(A, U, S, Vt) -> float:
    """‖A − U·Σ·Vᵀ‖∞ for a (possibly non-square) SVD."""
    A = as_matrix(A)
    U = as_matrix(U); Vt = as_matrix(Vt)
    Sigma = np.zeros(A.shape)
    k = min(A.shape)
    Sigma[:k, :k] = np.diag(np.asarray(S, dtype=float)[:k])
    return max_abs(A - U @ Sigma @ Vt)


def orthonormality_residual(Q) -> float:
    """‖QᵀQ − I‖∞ — how close the columns of Q are to orthonormal."""
    Q = as_matrix(Q)
    return max_abs(Q.T @ Q - np.eye(Q.shape[1]))
