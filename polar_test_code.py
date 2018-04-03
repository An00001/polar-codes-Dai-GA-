#!/usr/bin/env python3
from __future__ import print_function, division
import numpy as np
import unittest
# import os
# import time
from polar_code_tools import design_snr_to_bec_eta, calculate_bec_channel_capacities, get_frozenBitMap, get_frozenBitPositions, get_polar_generator_matrix, get_polar_encoder_matrix_systematic

import sys
sys.path.insert(0, './build/lib.linux-x86_64-2.7')

import pypolar

'''
EncoderA of the paper:
    Harish Vangala, Yi Hong, and Emanuele Viterbo,
    "Efficient Algorithms for Systematic Polar Encoding",
    IEEE Communication Letters, 2015.
'''


def polar_encode_systematic(u, N, frozenBitMap):
    # print(u.dtype, frozenBitMap.dtype)
    y = frozenBitMap
    x = np.zeros(N, dtype=int)
    x[np.where(frozenBitMap == -1)] = u
    return polar_encode_systematic_algorithm_A(y, x, N, frozenBitMap)


def polar_encode_systematic_algorithm_A(y, x, N, frozenBitMap):
    n = int(np.log2(N))

    X = np.zeros((N, n + 1), dtype=int)
    X[:, 0] = y
    X[:, -1] = x

    for i in np.arange(N - 1, -1, -1):
        bits = tuple(np.binary_repr(i, n))
        # print(i, ' == ', bits)
        if frozenBitMap[i] < 0:
            # print('is info bit', frozenBitMap[i])
            for j in np.arange(n - 1, -1, -1):
                kappa = 2 ** (n - j - 1)
                # print(i, j, bits[j], kappa)
                if bits[j] == '0':
                    X[i, j] = (X[i, j + 1] + X[i + kappa, j + 1]) % 2
                else:
                    X[i, j] = X[i, j + 1]
        else:
            # print('is frozen bit', frozenBitMap[i])
            for j in np.arange(n):
                kappa = 2 ** (n - j - 1)
                # print(i, j, bits[j], kappa)
                if bits[j] == '0':
                    X[i, j + 1] = (X[i, j] + X[i + kappa, j]) % 2
                else:
                    X[i, j + 1] = X[i, j]

    return X[:, 0], X[:, -1]


def encode_systematic_matrix(u, N, frozenBitMap):
    n = int(np.log2(N))
    G = get_polar_generator_matrix(n)
    x = np.copy(frozenBitMap)
    x[np.where(frozenBitMap == -1)] = u
    # print(u, x, np.where(frozenBitMap == -1))
    # print(frozenBitMap[np.where(frozenBitMap > -1)])
    x = x.dot(G) % 2
    x[np.where(frozenBitMap > -1)] = frozenBitMap[np.where(frozenBitMap > -1)]
    x = x.dot(G) % 2
    return x


def encode_matrix(u, N, frozenBitMap):
    n = int(np.log2(N))
    G = get_polar_generator_matrix(n)
    x = np.copy(frozenBitMap)
    x[np.where(frozenBitMap == -1)] = u
    x = x.dot(G) % 2
    return x


class PolarEncoderTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_001_encode_systematic(self):
        frozenBitMap = np.array([0, -1, 0, -1, 0, -1, -1, -1], dtype=int)
        for i in range(100):
            u = np.random.randint(0, 2, 5)
            Y, X = polar_encode_systematic(u, 8, frozenBitMap)
            xm = encode_systematic_matrix(u, 8, frozenBitMap)
            self.assertTrue(np.all(X == xm))

        N = 2 ** 6
        K = N // 2
        eta = design_snr_to_bec_eta(-1.59, 1.0)
        polar_capacities = calculate_bec_channel_capacities(eta, N)
        frozenBitMap = get_frozenBitMap(polar_capacities, N - K)
        # print(frozenBitMap)

        for i in range(100):
            u = np.random.randint(0, 2, K)
            Y, X = polar_encode_systematic(u, N, frozenBitMap)
            xm = encode_systematic_matrix(u, N, frozenBitMap)
            self.assertTrue(np.all(X == xm))

    def test_002_frozen_bit_positions(self):
        for snr in np.arange(-1.5, 3.5, .25):
            for inv_coderate in np.array([8, 6, 5, 4, 3, 2, 1.5, 1.2]):
                for n in range(6, 11):
                    N = 2 ** n
                    K = int(N / inv_coderate)
                    # print(N, K, inv_coderate)
                    cf = pypolar.frozen_bits(N, K, snr)
                    eta = design_snr_to_bec_eta(snr, 1. * K / N)
                    polar_capacities = calculate_bec_channel_capacities(eta, N)
                    pf = get_frozenBitPositions(polar_capacities, N - K)
                    pf = np.sort(pf)
                    encoder = pypolar.PolarEncoder(N, cf)
                    decoder = pypolar.PolarDecoder(N, 1, cf)

                    pp = encoder.frozenBits()
                    pd = decoder.frozenBits()

                    if not np.all(pf == cf):
                        print(cf)
                        print(pf)
                        print(cf == pf)
                    self.assertTrue(np.all(pf == cf))
                    self.assertTrue(np.all(pp == cf))
                    self.assertTrue(np.all(pd == cf))

    def test_003_systematic_matrix(self):
        snr = 2.
        for n in range(4, 8):
            N = 2 ** n
            K = N // 2
            self.matrix_validation(N, K, snr)
            self.matrix_validation(N, K // 2, snr)

    def matrix_validation(self, N, K, snr):
        eta = design_snr_to_bec_eta(snr, 1.0)
        polar_capacities = calculate_bec_channel_capacities(eta, N)
        f = np.sort(get_frozenBitPositions(polar_capacities, N - K))
        ip = np.setdiff1d(np.arange(N, dtype=f.dtype), f)
        frozenBitMap = get_frozenBitMap(polar_capacities, N - K)

        n = int(np.log2(N))
        G = get_polar_generator_matrix(n)
        Gs = get_polar_encoder_matrix_systematic(N, f)
        for i in range(10):
            u = np.random.randint(0, 2, K).astype(dtype=np.uint8)
            x = np.zeros(N, dtype=np.uint8)
            x[ip] = u
            xref = np.copy(frozenBitMap)
            xref[np.where(frozenBitMap == -1)] = u
            self.assertTrue(np.all(x == xref))
            x = x.dot(G) % 2
            x[f] = 0
            x = x.dot(G) % 2
            xs = u.dot(Gs) % 2

            self.assertTrue(np.all(x == xs))
        self.matrix_gen_check_validation(Gs, f)

    def matrix_gen_check_validation(self, Gs, f):
        K, N = np.shape(Gs)
        P = Gs[:, f]
        G = np.hstack((np.identity(K, dtype=Gs.dtype), P))
        H = np.hstack((P.T, np.identity(N - K, dtype=Gs.dtype)))
        self.assertEquals(np.linalg.matrix_rank(H), N - K)
        self.assertTrue(np.all(G.dot(H.T) % 2 == 0))

    def test_004_encoder_config(self):
        snr = 2.
        for n in range(4, 10):
            N = 2 ** n
            K = N // 2
            self.validate_config(N, K, snr)
            self.validate_config(N, K // 2, snr)

    def validate_config(self, N, K, snr):
        eta = design_snr_to_bec_eta(snr, 1.0)
        polar_capacities = calculate_bec_channel_capacities(eta, N)
        f = get_frozenBitPositions(polar_capacities, N - K)
        f = np.sort(f)
        frozenBitMap = get_frozenBitMap(polar_capacities, N - K)
        info_pos = np.setdiff1d(np.arange(N, dtype=f.dtype), f)
        self.assertEquals(info_pos.size, K)
        self.assertEquals(f.size, N - K)
        self.assertEquals(np.sum(frozenBitMap), -K)

        p = pypolar.PolarEncoder(N, f)
        self.assertEquals(p.blockLength(), N)

        self.assertTrue(np.all(f == p.frozenBits()))
        self.assertTrue(np.all(f == np.arange(N)[np.where(frozenBitMap == 0)]))

        self.assertTrue(p.isSystematic())
        p.setSystematic(False)
        self.assertFalse(p.isSystematic())
        p.setSystematic(True)
        self.assertTrue(p.isSystematic())

    def test_005_cpp_encoder_impls(self):
        snr = 0.
        test_size = np.array([4, 5, 6, 9, 10, 11])
        for i in test_size:
            N = 2 ** i
            K = N // 2
            verify_cpp_encoder_impl(N, int(N * .75), snr)
            verify_cpp_encoder_impl(N, N // 2, snr)
            verify_cpp_encoder_impl(N, N // 4, snr)


def verify_cpp_encoder_impl(N=2 ** 4, K=5, snr=2.):
    eta = design_snr_to_bec_eta(snr, 1.0)
    polar_capacities = calculate_bec_channel_capacities(eta, N)
    f = get_frozenBitPositions(polar_capacities, N - K)
    f = np.sort(f)
    frozenBitMap = get_frozenBitMap(polar_capacities, N - K)
    info_pos = np.setdiff1d(np.arange(N, dtype=f.dtype), f)

    p = pypolar.PolarEncoder(N, f)
    print("Encoder CPP test ({}, {})".format(N, K))
    # print(f)

    for i in np.arange(10):
        print(i)
        u = np.random.randint(0, 2, K).astype(dtype=np.uint8)
        d = np.packbits(u)
        dref = np.copy(d)
        # print(d)
        # print(u)
        p.setInformation(d)
        p.encode()
        codeword = p.getEncodedData()
        # print('codeword', codeword)

        cw_pack = p.encode_vector(d)
        assert np.all(cw_pack == codeword)

        # print(np.unpackbits(cw_pack)[info_pos])
        assert np.all(np.unpackbits(cw_pack)[info_pos] == u)

        xm = encode_systematic_matrix(u, N, frozenBitMap)

        # print(xm[info_pos])

        assert np.all(u == xm[info_pos])
        assert np.all(d == dref)

        xmp = np.packbits(xm)

        if not np.all(xmp == cw_pack):
            print(d)
            print(u)
            print(cw_pack)
            print(xmp)
            print(xm)
            print(np.unpackbits(cw_pack))

        assert np.all(xmp == cw_pack)
        assert np.all(xm == np.unpackbits(cw_pack))


def verify_cpp_decoder_impl(N=2 ** 6, K=2 ** 5, n_iterations=100, crc=None):
    print('verify CPP decoder implementation with ({}, {}) polar code'.format(N, K))
    eta = design_snr_to_bec_eta(2, float(1. * K / N))
    polar_capacities = calculate_bec_channel_capacities(eta, N)
    f = get_frozenBitPositions(polar_capacities, N - K)
    # f = np.sort(f)
    # print(f)
    # f = pypolar.frozen_bits(N, K, 2)

    p = pypolar.PolarEncoder(N, f)
    dec = pypolar.PolarDecoder(N, 1, f, 'char')

    if crc is 'CRC8':
        p.setErrorDetection()
        dec.setErrorDetection()

    ctr = 0
    num_errors = 0
    for i in np.arange(n_iterations):
        u = np.random.randint(0, 2, K).astype(dtype=np.uint8)
        d = np.packbits(u)
        dc = np.copy(d)

        cw_pack = p.encode_vector(dc)
        b = np.unpackbits(cw_pack)
        llrs = -2. * b + 1.
        llrs = llrs.astype(dtype=np.float32)
        llrs += np.random.normal(0.0, .001, len(llrs))
        dhat = dec.decode_vector(llrs)
        # print(d)
        # print(dhat)
        if not np.all(dhat == d) and crc is None:
            print('Decoder test fails in iteration', i)
            ud = np.unpackbits(d)
            udhat = np.unpackbits(dhat)
            print(d)
            print(dhat)
            print(ud)
            print(udhat)
            print(np.sum(udhat == ud) - len(ud))
            # num_errors += 1

        if crc is 'CRC8':
            assert np.all(dhat[0:-1] == d[0:-1])
        else:
            assert np.all(dhat == d)
        ctr += 1
    if num_errors > 0:
        print('Decoder test failed in {} out of {}'.format(
            num_errors, n_iterations))
    assert num_errors == 0


def verify_cpp_decoder_impls():
    n_iterations = 100
    inv_coderate = 4 / 3
    for n in range(5, 11):
        N = 2 ** n
        K = int(N // inv_coderate)
        verify_cpp_decoder_impl(N, K, n_iterations)

    inv_coderate = 2
    for n in range(5, 11):
        N = 2 ** n
        K = int(N // inv_coderate)
        verify_cpp_decoder_impl(N, K, n_iterations)
        verify_cpp_decoder_impl(N, K, n_iterations, 'CRC8')

    inv_coderate = 4
    for n in range(5, 9):
        N = 2 ** n
        K = int(N // inv_coderate)
        verify_cpp_decoder_impl(N, K, n_iterations)


def matrix_row_weight(G):
    w = np.sum(G, axis=1)
    print(w)
    w = np.sum(G, axis=0)
    print(w)


def calculate_code_properties(N, K, design_snr_db):
    eta = design_snr_to_bec_eta(design_snr_db, 1.0 * K / N)
    polar_capacities = calculate_bec_channel_capacities(eta, N)
    frozenBitMap = get_frozenBitMap(polar_capacities, N - K)

    f = pypolar.frozen_bits(N, K, design_snr_db)
    p = pypolar.PolarEncoder(N, f)
    Gp = get_polar_generator_matrix(int(np.log2(N)))
    print(Gp)

    assert np.all(np.where(frozenBitMap > -1) == f)

    numInfoWords = 2 ** K
    n_prepend_bits = int(8 * np.ceil(K / 8.) - K)
    print(n_prepend_bits)
    weights = {}
    for i in range(numInfoWords):
        # b = np.binary_repr(i, K + n_prepend_bits)
        b = np.binary_repr(i, K)
        u = np.array([int(l) for l in b], dtype=np.uint8)
        # nb = np.concatenate((np.zeros(n_prepend_bits, dtype=nb.dtype), nb))
        nbp = np.packbits(u)
        cw = p.encode_vector(nbp)
        # xm = encode_systematic_matrix(u, N, frozenBitMap)
        c = np.unpackbits(cw)
        # assert np.all(xm == c)
        weight = np.sum(c)
        if weight in weights:
            weights[weight] += 1
        else:
            weights[weight] = 1
        # nb = bin(i)
        # print(i, b, u, nbp, c)
    print(f)
    print(frozenBitMap)
    # print(n_prepend_bits)
    weights.pop(0)
    print(weights)
    dmin_ext_search = np.min(weights.keys())
    print(dmin_ext_search)

    validate_systematic_matrix(N, f, frozenBitMap)

    Gs = get_polar_encoder_matrix_systematic(N, f)

    P = Gs[:, f]
    # print(P)
    G = np.hstack((np.identity(K, dtype=Gs.dtype), P))
    H = np.hstack((P.T, np.identity(N - K, dtype=Gs.dtype)))
    # print(P)
    print(H)
    # print(G.dot(H.T) % 2)
    #
    # print(Gs.dot(Gs.T) % 2)

    print(np.linalg.matrix_rank(H))
    dmin_H = np.min(np.sum(H, axis=1))
    dmin_P = 1 + np.min(np.sum(P, axis=1))
    print(np.sum(H, axis=1))
    print(np.sum(P, axis=1))
    print('search {} vs {} H, P{}'.format(dmin_ext_search, dmin_H, dmin_P))
    assert dmin_ext_search == dmin_P


def main():
    # calculate_code_properties(32, 16, 0.0)
    verify_cpp_decoder_impls()


if __name__ == '__main__':
    unittest.main(failfast=True)
    # main()
