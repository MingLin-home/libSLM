'''
Generate synthetic dataset and train SLM using greedy algorithm. Suppose the second order coefficient matrix of the SLM is diagonal free.
Note that the greedy algorithm only accepts sparse input.
Show the learning curves along iteration.

@author: Ming Lin
@contact: linmin@umich.edu
'''

import numpy
import sys
import matplotlib.pyplot as plt
import sklearn.metrics
import sklearn.preprocessing
import scipy.sparse

sys.path.append('../')
import libSLM


repeat_times = 1 # repeat experiments
dim = 100 # the dimension of features
rank_k = 3 # the rank of gFM
total_iteration = 60 # number of iterations to train gFM
total_record = 20 # number of check points
max_init_iter = 20 # number of iterations to initialize gFM

# We save the recovery error, training set prection error and testing set prediction error along iteration
trainset_error_record = numpy.zeros((repeat_times, total_record))
testset_error_record = numpy.zeros((repeat_times, total_record))
# The count of iteration at each check point
record_iteration_axis = numpy.round(numpy.linspace(0, total_iteration, total_record, endpoint=True)).astype('int')


def train(export_filename):
    """
    Train gFM and save learning curve in file named by export_filename
    :param export_filename: the namve of the file saving the learning curve
    :return:
    """
    for repeat_count in xrange(repeat_times):
        print 'generating training toy set'
        n_trainset = 20 * rank_k * dim # size of training set
        n_testset = 10000 # size of testing set

        # # ----- Generate sparse training/testing instance from Bernoulli distribution ----- #
        bernoulli_p = 0.1
        X = numpy.random.binomial(1,bernoulli_p,size=(n_trainset,dim))/numpy.sqrt(dim*bernoulli_p) # training set instances
        X_test = numpy.random.binomial(1, bernoulli_p, size=(n_testset, dim))/numpy.sqrt(dim*bernoulli_p) # testing set instances

        X = scipy.sparse.csr_matrix(X)
        X_test = scipy.sparse.csr_matrix(X_test)

        # ---------- Synthetic $M^*$ and $w^*$ as our ground-truth gFM model
        U_true = numpy.random.randn(dim, rank_k) / numpy.sqrt(dim)
        w_true = numpy.random.randn(dim, 1) / numpy.sqrt(dim)

        # generate true labels for training
        the_bias_term = -0.5
        y = X.dot(w_true) + libSLM.A_diag0_sparse(U_true, U_true, X.T, numpy.asarray(X.T.mean(axis=1))) + the_bias_term
        y = y.flatten()

        # generate true labels for testing
        y_test = X_test.dot(w_true) + libSLM.A_diag0_sparse(U_true, U_true, X_test.T, numpy.asarray(X_test.T.mean(axis=1))) + the_bias_term
        y_test = y_test.flatten()

        # ----- create an SLM estimator ----- #
        the_estimator = libSLM.SLM(rank_M=rank_k, max_iter=total_iteration, tol=1e-6, max_init_iter=max_init_iter, init_tol=1e-2, lambda_w=0, lambda_M=0,
                                   using_cache=True, solver_algorithm='Greedy', learning_rate=numpy.inf, diag_zero=True, truncate_y=False)

        # Initialize gFM with no iteration. This will assign memory space for U,V,w without iteration.
        the_estimator.fit(X, y, n_more_iter=0)
        record_count = 0
        n_more_iter = 0
        y_trainset_pred = the_estimator.predict(X)
        y_testset_pred = the_estimator.predict(X_test)
        trainset_error = sklearn.metrics.mean_squared_error(y, y_trainset_pred) / sklearn.metrics.mean_squared_error(y, numpy.zeros((len(y),)))
        testset_error = sklearn.metrics.mean_squared_error(y_test, y_testset_pred) / sklearn.metrics.mean_squared_error(y_test, numpy.zeros((len(y_test),)))
        trainset_error_record[repeat_count, record_count] = trainset_error
        testset_error_record[repeat_count, record_count] = testset_error

        print '[ite=%d(+%d), trainset predict error= %g, testset predict error=%g,] ' % \
              (record_count, n_more_iter, trainset_error, testset_error,)

        # start iteration
        for record_count in xrange(1, total_record):
            n_more_iter = record_iteration_axis[record_count] - record_iteration_axis[record_count - 1]
            # In each fit() call, we limite the number of iteration to be n_more_iter=n_more_iter.
            the_estimator.fit(X, y, n_more_iter=n_more_iter)
            y_trainset_pred = the_estimator.predict(X)
            y_testset_pred = the_estimator.predict(X_test)
            trainset_error = sklearn.metrics.mean_squared_error(y, y_trainset_pred) / sklearn.metrics.mean_squared_error(y, numpy.zeros((len(y),)))
            testset_error = sklearn.metrics.mean_squared_error(y_test, y_testset_pred) / sklearn.metrics.mean_squared_error(y_test, numpy.zeros((len(y_test),)))
            trainset_error_record[repeat_count, record_count] = trainset_error
            testset_error_record[repeat_count, record_count] = testset_error
            print '[ite=%d(+%d), trainset predict error= %g, testset predict error=%g,] ' % \
                  (record_count, n_more_iter, trainset_error, testset_error,)
        # end for record_count
    # end for repeat

    # save learning curve to file named export_filename.
    numpy.savez_compressed(export_filename, record_iteration_axis=record_iteration_axis,
                           trainset_error_record=trainset_error_record, testset_error_record=testset_error_record)
# end def


if __name__ == '__main__':
    export_filename = './SLM_diag0_Greedy_Alg_learning_curve.npz'
    train(export_filename)

    the_results = numpy.load(export_filename)
    record_iteration_axis = the_results['record_iteration_axis']

    trainset_error_record = the_results['trainset_error_record']
    testset_error_record = the_results['testset_error_record']

    # plot curves
    export_figname = './SLM_diag0_Greedy_Alg_learning_curve.png'
    plt.semilogy(record_iteration_axis, numpy.mean(trainset_error_record, axis=0), '-xb', label='train error')
    plt.semilogy(record_iteration_axis, numpy.mean(testset_error_record, axis=0), '-xr', label='test error')
    plt.legend()
    plt.savefig(export_figname)
    plt.close()