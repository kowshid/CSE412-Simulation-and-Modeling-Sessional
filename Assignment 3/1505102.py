from scipy import stats
from collections import defaultdict
import math

mult = 65539
moddiv = math.pow(2, 31)
alph = 0.1
seed = 1505102

randomNumbers = []

a = [[4529.4, 9044.9, 13568, 18091, 22615, 27892],
     [9044.9, 18097, 27139, 36187, 45234, 55789],
     [13568, 27139, 40721, 54281, 67852, 83685],
     [18091, 36187, 54281, 72414, 90470, 111580],
     [22615, 45234, 67852, 90470, 113262, 139476],
     [27892, 55789, 83685, 111580, 139476, 172860]
     ]
b = [1 / 6, 5 / 24, 11 / 120, 19 / 720, 29 / 5040, 1 / 840]

def randomNumberGeneration(N):
    global randomNumbers
    randomNumbers = [0.0] * N
    randomNumbers[0] = seed

    for i in range(1, N):
        randomNumbers[i] = (mult * randomNumbers[i - 1]) % moddiv

    for i in range(N):
        randomNumbers[i] /= moddiv

    # print(randomNumbers)

def uniformityTest(N, k, alpha):
    global randomNumbers
    randomNumberGeneration(N)

    counts = [0] * k

    for rand in randomNumbers:
        idx = math.floor(rand * k)
        counts[idx] += 1

    chiSquared = 0.0
    for i in range(k):
        chiSquared += math.pow((counts[i] - N / k), 2)

    chiSquared *= (k / N)

    print("Uniformity Test for k = ", k, " alpha = ", alpha)
    if chiSquared > stats.chi2.ppf(1 - alpha, k - 1):
        print("Rejected\n")
    else:
        print("Not Rejected\n")

def serialTest(N, k, d, alpha):
    global randomNumbers
    randomNumberGeneration(N)

    upIdx = math.floor(N/d)
    counts = defaultdict(int)

    tuples = []
    for i in range(upIdx):
        tuples.append(randomNumbers[i])

        if len(tuples) == d:
            tupleIdx = []
            for rand in tuples:
                idx = math.floor(rand * k)
                tupleIdx.append(str(idx))

            # print(tupleIdx)
            pattern = ''.join(tupleIdx)
            # print(pattern)
            counts[pattern] += 1
            tuples = []

    chiSquared = 0.0
    zeroCount = math.pow(k, d) - len(counts)
    # print(k, d, len(counts))
    zeroCount = int(zeroCount)

    for i in range(zeroCount):
        temp = - (N / math.pow(k, d))
        chiSquared += math.pow(temp, 2)

    for key in counts:
        temp = counts[key] - (N / math.pow(k, d))
        chiSquared += math.pow(temp, 2)

    print("Serial Test for k = ", k, " d = ", d, " alpha = ", alpha)
    if chiSquared > stats.chi2.ppf(1 - alpha, k - 1):
        print("Rejected\n")
    else:
        print("Not Rejected\n")

def runsTest(N, alpha):
    global randomNumbers
    randomNumberGeneration(N)

    runLen = [0] * 6
    currentRun = 1
    for i in range(N-1):
        if randomNumbers[i] < randomNumbers[i+1]:
            currentRun += 1
        else:
            currentRun = min(6, currentRun)
            runLen[currentRun - 1] += 1
            currentRun = 1

    currentRun = min(6, currentRun)
    runLen[currentRun - 1] += 1

    R = 0
    for i in range(6):
        for j in range(6):
            R += a[i][j] * (runLen[i] - (N * b[i])) * (runLen[j] - (N * b[j]))

    R /= N

    print("R = ", R)
    print("Runs Test for alpha = ", alpha)
    if R > stats.chi2.ppf(1 - alpha, 6):
        print("Rejected\n")
    else:
        print("Not Rejected\n")

def correlationTest(N, alpha, j):
    global randomNumbers
    randomNumberGeneration(N)

    h = math.floor(((N - 1) / j) - 1)
    ro = 0.0

    for i in range(h + 1):
        ro += randomNumbers[i * j] * randomNumbers[(i + 1) * j]

    ro = (12 * ro) / (h + 1)
    ro -= 3

    roVariance = ((13 * h) + 7) / math.pow(h + 1, 2)
    Aj = ro / math.sqrt(roVariance)

    print("Correlation Test for alpha = ", alpha, " j = ", j)
    if abs(Aj) > stats.norm.ppf(1 - (alpha / 2)):
        print("Rejected\n")
    else:
        print("Not Rejected\n")

def main():
    n = 20
    uniformityTest(n, 10, alph)
    uniformityTest(n, 20, alph)
    serialTest(n, 4, 2, alph)
    serialTest(n, 4, 3, alph)
    serialTest(n, 8, 2, alph)
    serialTest(n, 8, 3, alph)
    runsTest(n, alph)
    correlationTest(n, alph, 1)
    correlationTest(n, alph, 3)
    correlationTest(n, alph, 5)

if __name__ == "__main__":
    main()