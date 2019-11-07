
"""
.. moduleauthor:: Chris Bowman <chris.bowman.physics@gmail.com>
"""

from numpy import exp, log, mean, std, sqrt, tanh, cos, cov
from numpy import array, linspace, sort, searchsorted, pi, argmax, argsort, logaddexp
from numpy.random import random
from scipy.integrate import quad, simps
from scipy.optimize import minimize, minimize_scalar, differential_evolution
from warnings import warn
from itertools import product
from functools import reduce
from copy import copy
import matplotlib.pyplot as plt




class DensityEstimator(object):
    """
    Parent class for the 1D density estimation classes GaussianKDE and UnimodalPdf.
    """
    def __init__(self):
        self.lwr_limit = None
        self.upr_limit = None
        self.mode = None

    def __call__(self, x):
        return None

    def interval(self, frac = 0.95):
        p_max = self.__call__(self.mode)
        p_conf = self.binary_search(self.interval_prob, frac, [0., p_max], uphill = False)
        return self.get_interval(p_conf)

    def get_interval(self, z):
        lwr = self.binary_search(self.__call__, z, [self.lwr_limit, self.mode], uphill = True)
        upr = self.binary_search(self.__call__, z, [self.mode, self.upr_limit], uphill = False)
        return lwr, upr

    def interval_prob(self, z):
        lwr, upr = self.get_interval(z)
        return quad(self.__call__, lwr, upr, limit = 100)[0]

    def moments(self):
        pass

    def plot_summary(self, filename = None, show = True, label = None):
        """
        Plot the estimated PDF along with summary statistics.

        :keyword str filename: Filename to which the plot will be saved. If unspecified, the plot will not be saved.
        :keyword bool show: Boolean value indicating whether the plot should be displayed in a window. (Default is True)
        :keyword str label: The label to be used for the x-axis on the plot as a string.
        """
        sigma_1 = self.interval(frac = 0.68268)
        sigma_2 = self.interval(frac = 0.95449)
        sigma_3 = self.interval(frac = 0.9973)
        mu, var, skw, kur = self.moments()

        if type(self).__name__ is 'GaussianKDE':
            lwr = sigma_3[0] - 5*self.h
            upr = sigma_3[1] + 5*self.h
        else:
            if hasattr(sigma_3[0], '__len__'):
                s_min = sigma_3[0][0]
                s_max = sigma_3[-1][1]
            else:
                s_min = sigma_3[0]
                s_max = sigma_3[1]

            lwr = s_min - 0.1*(s_max - s_min)
            upr = s_max + 0.1*(s_max - s_min)

        axis = linspace(lwr, upr, 500)

        fig = plt.figure(figsize = (10,6))
        ax = plt.subplot2grid((1, 3), (0, 0), colspan = 2)
        ax.plot(axis, self.__call__(axis), lw = 1, c = 'C0')
        ax.fill_between(axis, self.__call__(axis), color = 'C0', alpha = 0.1)
        ax.plot([self.mode, self.mode], [0., self.__call__(self.mode)], c = 'red', ls = 'dashed')

        if label is not None:
            ax.set_xlabel(label, fontsize = 13)
        else:
            ax.set_xlabel('argument', fontsize = 13)

        ax.set_ylabel('probability density', fontsize = 13)
        ax.grid()


        gap = 0.05
        h = 0.95
        x1 = 0.35
        x2 = 0.40
        ax = plt.subplot2grid((1, 3), (0, 2))

        ax.text(0., h, 'Basics', horizontalalignment = 'left', fontweight = 'bold')
        h -= gap
        ax.text(x1, h, 'Mode:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( self.mode ), horizontalalignment='left')
        h -= gap
        ax.text(x1, h, 'Mean:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( mu ), horizontalalignment='left')
        h -= gap
        ax.text(x1, h, 'Standard dev:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( sqrt(var) ), horizontalalignment='left')
        h -= 2*gap

        ax.text(0., h, 'Highest-density intervals', horizontalalignment = 'left', fontweight='bold')
        h -= gap
        ax.text(x1, h, '1-sigma:', horizontalalignment='right')
        if hasattr(sigma_1[0], '__len__'):
            for itvl in sigma_1:
                ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(itvl[0], itvl[1]), horizontalalignment = 'left')
                h -= gap
        else:
            ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(sigma_1[0], sigma_1[1]), horizontalalignment='left')
            h -= gap

        ax.text(x1, h, '2-sigma:', horizontalalignment='right')
        if hasattr(sigma_2[0], '__len__'):
            for itvl in sigma_2:
                ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(itvl[0], itvl[1]), horizontalalignment = 'left')
                h -= gap
        else:
            ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(sigma_2[0], sigma_2[1]), horizontalalignment='left')
            h -= gap

        ax.text(x1, h, '3-sigma:', horizontalalignment='right')
        if hasattr(sigma_3[0], '__len__'):
            for itvl in sigma_3:
                ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(itvl[0], itvl[1]), horizontalalignment = 'left')
                h -= gap
        else:
            ax.text(x2, h, r'{:.5G} $\rightarrow$ {:.5G}'.format(sigma_3[0], sigma_3[1]), horizontalalignment='left')
            h -= gap

        h -= gap
        ax.text(0., h, 'Higher moments', horizontalalignment = 'left', fontweight = 'bold')
        h -= gap
        ax.text(x1, h, 'Variance:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( var ), horizontalalignment='left')
        h -= gap
        ax.text(x1, h, 'Skewness:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( skw ), horizontalalignment='left')
        h -= gap
        ax.text(x1, h, 'Kurtosis:', horizontalalignment='right')
        ax.text(x2, h, '{:.5G}'.format( kur ), horizontalalignment='left')

        ax.axis('off')

        plt.tight_layout()
        if filename is not None:
            plt.savefig(filename)
        if show:
            plt.show()
        else:
            fig.clear()
            plt.close(fig)

    @staticmethod
    def binary_search(func, value, bounds, uphill = True):
        x_min, x_max = bounds
        x = (x_min + x_max) * 0.5

        converged = False
        while not converged:
            f = func(x)
            if f > value:
                if uphill:
                    x_max = x
                else:
                    x_min = x
            else:
                if uphill:
                    x_min = x
                else:
                    x_max = x

            x = (x_min + x_max) * 0.5
            if abs((x_max - x_min)/x) < 1e-3:
                converged = True

        # now linearly interpolate as a polish step
        f_max = func(x_max)
        f_min = func(x_min)
        df = f_max - f_min

        return x_min*((f_max-value)/df) + x_max*((value - f_min)/df)




class UnimodalPdf(DensityEstimator):
    """
    Construct a UnimodalPdf object, which can be called as a function to
    return the estimated PDF of the given sample.

    The UnimodalPdf class is designed to robustly estimate univariate, unimodal probability
    distributions given a sample drawn from that distribution. This is a parametric method
    based on an heavily modified student-t distribution, which is extremely flexible.

    :param sample: 1D array of samples from which to estimate the probability distribution
    """
    def __init__(self, sample):

        self.sample = array(sample)
        self.n_samps = len(sample)

        # chebyshev quadtrature weights and axes
        self.sd = 0.2
        self.n_nodes = 128
        k = linspace(1, self.n_nodes, self.n_nodes)
        t = cos(0.5 * pi * ((2 * k - 1) / self.n_nodes))
        self.u = t / (1. - t**2)
        self.w = (pi / self.n_nodes) * (1 + t**2) / (self.sd * (1 - t**2)**(1.5))


        # first minimise based on a slice of the sample, if it's large enough
        self.cutoff = 2000
        self.skip = self.n_samps // self.cutoff
        if self.skip is 0:
            self.skip = 1

        self.x = self.sample[::self.skip]
        self.n = len(self.x)

        # makes guesses based on sample moments
        guesses = self.generate_guesses()

        # sort the guesses by the lowest score
        guesses = sorted(guesses, key = self.minfunc)

        # minimise based on the best guess
        self.min_result = minimize(self.minfunc, guesses[0], method='Nelder-Mead')
        self.MAP = self.min_result.x
        self.mode = self.MAP[0] #: The mode of the pdf, calculated automatically when an instance of UnimodalPdf is created.

        # if we were using a reduced sample, use full sample
        if self.skip > 1:
            self.x = self.sample
            self.n = self.n_samps
            self.min_result = minimize(self.minfunc, self.MAP, method='Nelder-Mead')
            self.MAP = self.min_result.x
            self.mode = self.MAP[0]

        # normalising constant for the MAP estimate curve
        self.map_lognorm = log(self.norm(self.MAP))

        # set some bounds for the confidence limits calculation
        x0, s0, v, f, k, q = self.MAP
        self.upr_limit = x0 + s0*(4*exp(f) + 1)
        self.lwr_limit = x0 - s0*(4*exp(-f) + 1)

    def generate_guesses(self):
        mu, sigma, skew = self.sample_moments()

        x0 = [mu, mu-sigma*skew*0.15, mu-sigma*skew*0.3]
        v = [0, 5.]
        s0 = [sigma, sigma*2]
        f = [0.5*skew, skew]
        k = [1., 4., 8.]
        q = [2.]

        return [ array(i) for i in product( x0, s0, v, f, k, q ) ]

    def sample_moments(self):
        mu = mean(self.x)
        x2 = self.x**2
        x3 = x2 * self.x
        sig = sqrt(mean(x2) - mu**2)
        skew = (mean(x3) - 3*mu*sig**2 - mu**3) / sig**3

        return mu, sig, skew

    def __call__(self, x):
        """
        Evaluate the PDF estimate at a set of given axis positions.

        :param x: axis location(s) at which to evaluate the estimate.
        :return: values of the PDF estimate at the specified locations.
        """
        return exp(self.log_pdf_model(x, self.MAP) - self.map_lognorm)

    def posterior(self, paras):
        x0, s0, v, f, k, q = paras

        # prior checks
        if (s0 > 0) & (0 < k < 20) & (1 < q < 6):
            return self.log_pdf_model(self.x, paras).sum() - self.n*log(self.norm(paras))
        else:
            return -1e50

    def minfunc(self, paras):
        return -self.posterior(paras)

    def norm(self, pvec):
        v = self.pdf_model(self.u, [0., self.sd, *pvec[2:]])
        integral = (self.w * v).sum() * pvec[1]
        return integral

    def pdf_model(self, x, pvec):
        return exp(self.log_pdf_model(x, pvec))

    def log_pdf_model(self, x, pvec):
        x0, s0, v, f, k, q = pvec
        v = exp(v) + 1
        z0 = (x - x0)/s0
        ds = exp(f*tanh(z0/k))
        z = z0 / ds

        log_prob = - (0.5*(1+v))*log( 1 + (abs(z)**q)/v )
        return log_prob

    def moments(self):
        """
        Calculate the mean, variance skewness and excess kurtosis of the estimated PDF.

        :return: mean, variance, skewness, ex-kurtosis
        """
        s = self.MAP[1]
        f = self.MAP[3]

        lwr = self.mode - 5*max(exp(-f), 1.)*s
        upr = self.mode + 5*max(exp(f), 1.)*s
        x = linspace(lwr, upr, 1000)
        p = self.__call__(x)

        mu  = simps(p*x, x=x)
        var = simps(p*(x - mu)**2, x=x)
        skw = simps(p*(x - mu)**3, x=x) / var*1.5
        kur = (simps(p*(x - mu)**4, x=x) / var**2) - 3.
        return (mu, var, skw, kur)




class GaussianKDE(DensityEstimator):
    """
    Construct a GaussianKDE object, which can be called as a function to
    return the estimated PDF of the given sample.

    GaussianKDE uses Gaussian kernel-density estimation to estimate the PDF
    associated with a given sample.

    :param sample: \
        1D array of samples from which to estimate the probability distribution

    :param float bandwidth: \
        Width of the Gaussian kernels used for the estimate. If not specified,
        an appropriate width is estimated based on sample data.

    :param bool cross_validation: \
        Indicate whether or not cross-validation should be used to estimate
        the bandwidth in place of the simple 'rule of thumb' estimate which
        is normally used.

    :param int max_cv_samples: \
        The maximum number of samples to be used when estimating the bandwidth
        via cross-validation. The computational cost scales roughly quadratically
        with the number of samples used, and can become prohibitive for samples of
        size in the tens of thousands and up. Instead, if the sample size is greater
        than *max_cv_samples*, the cross-validation is performed on a sub-sample of
        this size.
    """
    def __init__(self, sample, bandwidth = None, cross_validation = False, max_cv_samples = 5000):

        self.s = sort(array(sample).flatten()) # sorted array of the samples
        self.max_cvs = max_cv_samples # maximum number of samples to be used for cross-validation

        if bandwidth is None:
            self.h = self.simple_bandwidth_estimator()  # very simple bandwidth estimate
            if cross_validation:
                self.h = self.cross_validation_bandwidth_estimator(self.h)
        else:
            self.h = bandwidth

        # define some useful constants
        self.norm = 1. / (len(self.s) * sqrt(2 * pi) * self.h)
        self.cutoff = self.h*4
        self.q = 1. / (sqrt(2)*self.h)
        self.lwr_limit = self.s[0]  - self.cutoff*0.5
        self.upr_limit = self.s[-1] + self.cutoff*0.5

        # decide how many regions the axis should be divided into
        n = int(log((self.s[-1] - self.s[0]) / self.h) / log(2)) + 1

        # now generate midpoints of these regions
        mids = linspace(self.s[0], self.s[-1], 2**n+1)
        mids = 0.5*(mids[1:] + mids[:-1])

        # get the cutoff indices
        lwr_inds = searchsorted(self.s, mids - self.cutoff)
        upr_inds = searchsorted(self.s, mids + self.cutoff)
        slices = [slice(l,u) for l,u in zip(lwr_inds, upr_inds)]

        # now build a dict that maps midpoints to the slices
        self.slice_map = dict(zip(mids, slices))

        # build a binary tree which allows fast look-up of which
        # region contains a given value
        self.tree = BinaryTree(n, (self.s[0], self.s[-1]))

        # The mode of the pdf, calculated automatically when an instance of GaussianKDE is created.
        self.mode = self.locate_mode()

    def __call__(self, x_vals):
        """
        Evaluate the PDF estimate at a set of given axis positions.

        :param x_vals: axis location(s) at which to evaluate the estimate.
        :return: values of the PDF estimate at the specified locations.
        """
        if hasattr(x_vals, '__iter__'):
            return [ self.density(x) for x in x_vals ]
        else:
            return self.density(x_vals)

    def density(self, x):
        # look-up the region
        region = self.tree.lookup(x)
        # look-up the cutting points
        slc = self.slice_map[region[2]]
        # evaluate the density estimate from the slice
        return self.norm * exp(-((x - self.s[slc])*self.q)**2).sum()

    def simple_bandwidth_estimator(self):
        # A simple estimate which assumes the distribution close to a Gaussian
        return 1.06 * std(self.s) / (len(self.s)**0.2)

    def cross_validation_bandwidth_estimator(self, initial_h):
        """
        Selects the bandwidth by maximising a log-probability derived
        using a 'leave-one out cross-validation' approach.
        """
        # first check if we need to sub-sample for computational cost reduction
        if len(self.s) > self.max_cvs:
            scrambler = argsort(random(size=len(self.s)))
            samples = (self.s[scrambler])[:self.max_cvs]
        else:
            samples = self.s

        # create a grid in log-bandwidth space and evaluate the log-prob across it
        dh = 0.5
        log_h = [initial_h + m*dh for m in (-2, -1, 0, 1, 2)]
        log_p = [self.cross_validation_logprob(samples, exp(h)) for h in log_h]


        # if the maximum log-probability is at the edge of the grid, extend it
        for i in range(5):
            # stop when the maximum is not at the edge
            max_ind = argmax(log_p)
            if (0 < max_ind < len(log_h) - 1):
                break

            if max_ind == 0: # extend grid to lower bandwidths
                new_h = log_h[0] - dh
                new_lp = self.cross_validation_logprob(samples, exp(new_h))
                log_h.insert(0, new_h)
                log_p.insert(0, new_lp)

            else: # extend grid to higher bandwidths
                new_h = log_h[-1] + dh
                new_lp = self.cross_validation_logprob(samples, exp(new_h))
                log_h.append(new_h)
                log_p.append(new_lp)

        # cost of evaluating the cross-validation is expensive, so we want to
        # minimise total evaluations. Here we assume the CV score has only one
        # maxima, and use recursive grid refinement to rapidly find it.
        for refine in range(6):
            max_ind = int(argmax(log_p))
            lwr_h = 0.5 * (log_h[max_ind - 1] + log_h[max_ind])
            upr_h = 0.5 * (log_h[max_ind] + log_h[max_ind + 1])

            lwr_lp = self.cross_validation_logprob(samples, exp(lwr_h))
            upr_lp = self.cross_validation_logprob(samples, exp(upr_h))

            log_h.insert(max_ind, lwr_h)
            log_p.insert(max_ind, lwr_lp)

            log_h.insert(max_ind + 2, upr_h)
            log_p.insert(max_ind + 2, upr_lp)

        h_estimate = exp(log_h[argmax(log_p)])
        return h_estimate

    def cross_validation_logprob(self, samples, width, c = 0.99):
        """
        This function uses a 'leave-one-out cross-validation' (LOO-CV)
        approach to calculate a log-probability associated with the
        density estimate - the bandwidth can be selected by maximising
        this log-probability.
        """
        # evaluate the log-pdf estimate at each sample point
        log_pdf = self.log_evaluation(samples, samples, width)
        # remove the contribution at each sample due to itself
        d = log(c) - log(width * len(samples) * sqrt(2*pi)) - log_pdf
        loo_adjustment = log(1 - exp(d))
        log_probs = log_pdf + loo_adjustment
        return log_probs.sum() # sum to find the overall log-probability

    @staticmethod
    def log_kernel(x, c, h):
        z = (x - c) / h
        return -0.5*z**2 - log(h)

    def log_evaluation(self, points, samples, width):
        # evaluate the log-pdf in a way which prevents underflow
        generator = (self.log_kernel(points, s, width) for s in samples)
        return reduce(logaddexp, generator) - log(len(samples) * sqrt(2*pi))

    def locate_mode(self):
        lwr, upr = sample_hdi(self.s, 0.1, force_single=True) # use the 10% HDI to get close to the mode
        result = minimize_scalar(lambda x : -self.__call__(x), bounds = [lwr, upr], method = 'bounded')
        return result.x

    def moments(self):
        """
        Calculate the mean, variance skewness and excess kurtosis of the estimated PDF.

        :return: mean, variance, skewness, ex-kurtosis

        Note that these quantities are calculated directly from the estimated PDF, and
        note from the sample values.
        """
        N = 1000
        x = linspace(self.lwr_limit, self.upr_limit, N)
        p = self.__call__(x)

        mu  = simps(p*x, x=x)
        var = simps(p*(x - mu)**2, x=x)
        skw = simps(p*(x - mu)**3, x=x) / var*1.5
        kur = (simps(p*(x - mu)**4, x=x) / var**2) - 3.
        return (mu, var, skw, kur)

    def interval(self, frac = 0.95):
        """
        Calculate the highest-density interval(s) which contain a given fraction of total probability.

        :param float frac: Fraction of total probability contained by the desired interval(s).
        :return: A list of tuples which specify the intervals.
        """
        return sample_hdi(self.s, frac)




class KDE2D(object):
    def __init__(self, x = None, y = None):

        self.x = array(x)
        self.y = array(y)
        s_x, s_y = self.estimate_bandwidth(self.x, self.y)  # very simple bandwidth estimate
        self.q_x = 1. / (sqrt(2) * s_x)
        self.q_y = 1. / (sqrt(2) * s_y)
        self.norm = 1. / (len(self.x) * sqrt(2 * pi) * s_x * s_y)

    def __call__(self, x_vals, y_vals):
        if hasattr(x_vals, '__iter__') and hasattr(y_vals, '__iter__'):
            return [ self.density(x,y) for x,y in zip(x_vals, y_vals) ]
        else:
            return self.density(x_vals, y_vals)

    def density(self, x, y):
        z_x = ((self.x - x) * self.q_x)**2
        z_y = ((self.y - y) * self.q_y)**2
        return exp( -z_x - z_y ).sum() * self.norm

    def estimate_bandwidth(self, x, y):
        S = cov(x, y)
        p = S[0,1] / sqrt(S[0,0]*S[1,1])
        return 1.06 * sqrt(S.diagonal() * (1 - p**2)) / (len(x) ** 0.2)




class BinaryTree:
    """
    divides the range specified by limits into n = 2**layers equal regions,
    and builds a binary tree which allows fast look-up of which of region
    contains a given value.

    :param int layers: number of layers that make up the tree
    :param limits: tuple of the lower and upper bounds of the look-up region.
    """
    def __init__(self, layers, limits):
        self.n = layers
        self.lims = limits
        self.midpoint = 0.5*(limits[0] + limits[1])

        # first generate n trees of depth 1
        L = linspace(limits[0], limits[1], 2**self.n + 1)
        self.mids = 0.5*(L[1:] + L[:-1])
        L = [ [L[i], L[i+1], 0.5*(L[i]+L[i+1])] for i in range(2**self.n) ]

        # now recursively merge them until we have 1 tree of depth n
        for k in range(self.n-1):
            q = []
            for i in range(len(L)//2):
                q.append( [L[2*i], L[2*i+1], 0.5*(L[2*i][2] + L[2*i+1][2])] )
            L = copy(q)

        L.append(self.midpoint)
        self.tree = L

    def lookup(self, val):
        D = self.tree
        for i in range(self.n):
            D = D[val > D[2]]
        return D




def sample_hdi(sample, fraction, force_single = False):
    """
    Estimate the highest-density interval(s) for a given sample.

    This function computes the shortest possible single interval and double
    interval which contain a chosen fraction of the elements in the given
    sample.

    The double-interval solution is returned in place of the single-interval
    solution only if it's total length is at least 1% less than that of the
    single-interval.

    :param sample: \
        A sample for which the interval will be determined

    :param float fraction: \
        The fraction of the total probability to be contained by the interval.

    :param bool force_single: \
        When set to True, only the shortest single interval is computed and
        returned, ignoring the possibility of a shorter double interval.

    :return: tuple(s) specifying the lower and upper bounds of the highest-density interval(s)
    """

    # verify inputs are valid
    if not 0. < fraction < 1.: raise ValueError('fraction parameter must be between 0 and 1')
    if not hasattr(sample, '__len__') or len(sample) < 2: raise ValueError('The sample must have at least 2 elements')

    s = array(sample)
    if len(s.shape) > 1: s = s.flatten()
    s = sort(s)
    n = len(s)
    L = int(fraction * n)

    # check that we have enough samples to estimate the HDI for the chosen fraction
    if n <= L:
        warn('The number of samples is insufficient to estimate the interval for the given fraction')
        return (s[0], s[-1])
    elif n-L < 20:
        warn('len(sample)*(1 - fraction) is small - calculated interval may be inaccurate')

    # find the optimal single HDI
    widths = s[L:] - s[:n-L]
    i = widths.argmin()
    r1, w1 = (s[i], s[i+L]), s[i+L]-s[i]

    if not force_single:
        # now get the best 2-interval solution
        minfunc = dbl_interval_length(sample, fraction)
        bounds = minfunc.get_bounds()
        de_result = differential_evolution(minfunc, bounds)
        I1, I2 = minfunc.return_intervals(de_result.x)
        w2 = (I2[1]-I2[0]) + (I1[1]-I1[0])

    # return the split interval if the width reduction is non-trivial:
    if not force_single and w2 < w1*0.99:
        return I1, I2
    else:
        return r1




class dbl_interval_length(object):
    def __init__(self, sample, fraction):
        self.sample = sort(sample)
        self.f = fraction
        self.N = len(sample)
        self.L = int(self.f*self.N)
        self.space = self.N - self.L
        self.max_length = self.sample[-1] - self.sample[0]

    def get_bounds(self):
        return [(0.,1.), (0,self.space-1), (0,self.space-1)]

    def __call__(self, paras):
        f1 = paras[0]
        start = int(paras[1]); gap = int(paras[2])

        if (start+gap)>self.space-1:
            return self.max_length

        w1 = int(f1*self.L)
        w2 = self.L - w1
        start_2 = start + w1 + gap

        I1 = self.sample[start+w1] - self.sample[start]
        I2 = self.sample[start_2+w2] - self.sample[start_2]
        return I1+I2

    def return_intervals(self,paras):
        f1 = paras[0]
        start = int(paras[1])
        gap = int(paras[2])

        w1 = int(f1 * self.L)
        w2 = self.L - w1
        start_2 = start + w1 + gap

        I1 = (self.sample[start], self.sample[start + w1])
        I2 = (self.sample[start_2], self.sample[start_2 + w2])
        return I1, I2
