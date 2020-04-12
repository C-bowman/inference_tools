
import pytest
import unittest

from numpy import array, linspace, sin, zeros
from numpy.random import normal, seed
from inference.gp_tools import GpRegressor


class test_GpRegressor(unittest.TestCase):

    def test_marginal_likelihood_gradient(self):
        seed(1)
        N = 20
        S = 0.1
        x = linspace(0, 10, N)
        y = sin(x) + 3.0 + normal(size=N) * S
        errors = zeros(N) + S

        gpr = GpRegressor(x, y, y_err=errors)

        M = 2.5
        A = 0.1
        L = 0.6
        delta = 1e-5

        lml, grad_lml = gpr.marginal_likelihood_gradient(array([M, A, L]))

        M_pos = gpr.marginal_likelihood(array([M * (1 + delta), A, L]))
        M_neg = gpr.marginal_likelihood(array([M * (1 - delta), A, L]))

        A_pos = gpr.marginal_likelihood(array([M, A * (1 + delta), L]))
        A_neg = gpr.marginal_likelihood(array([M, A * (1 - delta), L]))

        L_pos = gpr.marginal_likelihood(array([M, A, L * (1 + delta)]))
        L_neg = gpr.marginal_likelihood(array([M, A, L * (1 - delta)]))

        fd_grad_M = (M_pos - M_neg) / (2 * M * delta)
        fd_grad_A = (A_pos - A_neg) / (2 * A * delta)
        fd_grad_L = (L_pos - L_neg) / (2 * L * delta)

        grad_M, grad_A, grad_L = grad_lml

        M_fractional_error = abs(fd_grad_M / grad_M - 1.).max()
        A_fractional_error = abs(fd_grad_A / grad_A - 1.).max()
        L_fractional_error = abs(fd_grad_L / grad_L - 1.).max()

        assert M_fractional_error < 1e-6
        assert A_fractional_error < 1e-6
        assert L_fractional_error < 1e-6

    def test_loo_likelihood_gradient(self):
        seed(1)
        N = 20
        S = 0.1
        x = linspace(0, 10, N)
        y = sin(x) + 3.0 + normal(size=N) * S
        errors = zeros(N) + S

        gpr = GpRegressor(x, y, y_err=errors)

        M = 2.5
        A = 0.1
        L = 0.6
        delta = 1e-5

        lml, grad_lml = gpr.loo_likelihood_gradient(array([M, A, L]))

        M_pos = gpr.loo_likelihood(array([M * (1 + delta), A, L]))
        M_neg = gpr.loo_likelihood(array([M * (1 - delta), A, L]))

        A_pos = gpr.loo_likelihood(array([M, A * (1 + delta), L]))
        A_neg = gpr.loo_likelihood(array([M, A * (1 - delta), L]))

        L_pos = gpr.loo_likelihood(array([M, A, L * (1 + delta)]))
        L_neg = gpr.loo_likelihood(array([M, A, L * (1 - delta)]))

        fd_grad_M = (M_pos - M_neg) / (2 * M * delta)
        fd_grad_A = (A_pos - A_neg) / (2 * A * delta)
        fd_grad_L = (L_pos - L_neg) / (2 * L * delta)

        grad_M, grad_A, grad_L = grad_lml

        M_fractional_error = abs(fd_grad_M / grad_M - 1.).max()
        A_fractional_error = abs(fd_grad_A / grad_A - 1.).max()
        L_fractional_error = abs(fd_grad_L / grad_L - 1.).max()

        assert M_fractional_error < 1e-6
        assert A_fractional_error < 1e-6
        assert L_fractional_error < 1e-6


if __name__ == '__main__':

    unittest.main()
