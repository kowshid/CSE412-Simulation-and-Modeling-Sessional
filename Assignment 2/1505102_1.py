import random
import numpy as np
import heapq

stationCount = 0
machineCount = []
interArrivalTime = 0
jobs = []
jobTypes = 0
jobProbs = []
jobStationCount = []
jobStationRouting = []
jobTaskTime = []

avgDelayInJobGlobal = []
totalAvgDelayGlobal = 0
avgJobsCountGlobal = 0
avgNumInQGlobal = []
avgDelayInQGlobal = []

busy = 1
idle = 0

simDuration = 8
iteration = 30
precision = 4

def exponential(rate):
    return random.expovariate(1 / rate)

def erlang(mean):
    return exponential(mean / 2) + exponential(mean / 2)

def input():
    global stationCount, machineCount, interArrivalTime, jobTypes, jobs, jobProbs, jobStationCount
    global jobStationRouting, jobTaskTime

    inputFile = open("Job Shop Input.txt", "r")
    lines = inputFile.readlines()
    # number of stations
    stationCount = lines[0].strip()
    stationCount = int(stationCount)

    # number of machines in each station
    line = lines[1].split()
    for i in range(stationCount):
        machineCount.append(int(line[i]))

    # inter-arrival time for jobs (t)
    interArrivalTime = lines[2]
    interArrivalTime = float(interArrivalTime)

    # number of job types (k)
    jobTypes = lines[3].strip()
    jobTypes = int(jobTypes)

    for i in range(jobTypes):
        jobs.append(i)

    # job probabilities for each types
    line = lines[4].split()
    for i in range(jobTypes):
        jobProbs.append(float(line[i]))

    # number of stations needed for each task
    line = lines[5].split()
    for i in range(jobTypes):
        jobStationCount.append(int(line[i]))

    #each job routing and probability
    k = 6
    list1 = []
    list2 = []
    for i in range(jobTypes):
        line1 = lines[k].split()
        line2 = lines[k+1].split()
        # print("line 1",lines[k].split())
        # print("line 2", lines[k+1].split())
        # print(len(line1))
        for j in range(len(line1)):
            list1.append(int(line1[j]))
            list2.append(float(line2[j]))

        jobStationRouting.append(list1)
        jobTaskTime.append(list2)

        k += 2
        list1 = []
        list2 = []

    # print(stationCount, machineCount, interArrivalTime, jobTypes, jobProbs, jobStationCount, jobStationRouting, jobTaskProbs)

class States:
    def __init__(self):
        # q at a particular station
        self.queue = [[] for i in range(stationCount)]
        self.qLen = [0] * stationCount
        self.serverStatus = [idle] * stationCount
        self.avgQdelay = [0] * stationCount
        self.avgQdelay = [0] * stationCount
        self.served = [0] * stationCount
        self.peopleInQ = [0] * stationCount
        self.delayInQ = [0] * stationCount
        self.avgDelayInQ = [0] * stationCount
        self.delayInJob = [0] * jobTypes
        self.avgDelayInJob = [0] * jobTypes
        self.jobCount = [0] * jobTypes
        self.areaNumInQ = [0] * stationCount
        self.avgNumInQ = [0] * stationCount
        self.totalJobsOngoing = 0
        self.totalJobsCount = 0
        self.totalAvgDelay = 0
        self.avgJobsCount = 0
        self.timeLastEvent = 0
        self.exitTime = 0

    def update(self, sim, event):
        timeSinceLastEvent = event.eventTime - self.timeLastEvent
        self.timeLastEvent = event.eventTime

        for i in range(stationCount):
            self.areaNumInQ[i] += self.qLen[i] * timeSinceLastEvent

        self.totalJobsCount += self.totalJobsOngoing * timeSinceLastEvent

    def finish(self, sim):
        global avgDelayInJobGlobal, totalAvgDelayGlobal, avgJobsCountGlobal, avgNumInQGlobal, avgDelayInQGlobal

        # average delay for each jobs
        for i in range(jobTypes):
            self.avgDelayInJob[i] = self.delayInJob[i] / self.jobCount[i]

        # overall delay for all jobs
        for i in range(jobTypes):
            self.totalAvgDelay += self.avgDelayInJob[i] * jobProbs[i]

        # average number of jobs in the system
        self.avgJobsCount = self.totalJobsCount / sim.exitTime

        # average delay in each station
        for i in range(stationCount):
            self.avgDelayInQ[i] = self.delayInQ[i] / self.served[i]

        # average number of people in each stations
        for i in range(stationCount):
            self.avgNumInQ[i] = self.areaNumInQ[i] / sim.exitTime

        avgDelayInJobGlobal = self.avgDelayInJob
        # print("assigned global", avgDelayInJobGlobal, self.avgDelayInJob)
        totalAvgDelayGlobal = self.totalAvgDelay
        avgJobsCountGlobal = self.avgJobsCount
        avgNumInQGlobal = self.avgNumInQ
        avgDelayInQGlobal = self.avgDelayInQ

class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.eventTime = None

    def process(self, sim):
        raise Exception('Unimplemented process method for the event!\n')

    def __repr__(self):
        return self.eventType

class StartEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'START'
        self.sim = sim

    def process(self, sim):
        job = np.random.choice(jobs, p = jobProbs)
        arrivalTime = self.eventTime + exponential(interArrivalTime)

        # scheduling the first job
        self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim, 0, job))

        # scheduling the termination
        self.sim.scheduleEvent(ExitEvent(simDuration, self.sim))

class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        print("Simulation Ended\n")

class ArrivalEvent(Event):
    def __init__(self, eventTime, sim, stationIdx, jobIdx):
        self.eventTime = eventTime
        self.eventType = 'ARRIVAL'
        self.sim = sim
        self.jobIdx = jobIdx
        self.stationIdx = stationIdx

    def process(self, sim):
        # scheduling another job if first station
        if self.stationIdx == 0:
            self.sim.states.totalJobsOngoing += 1
            self.sim.states.jobCount[self.jobIdx] += 1

            job = np.random.choice(jobs, p = jobProbs)
            arrivalTime = self.eventTime + exponential(interArrivalTime)
            self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim, 0, job))

        # finding station number from station index
        # zero indexing
        station = jobStationRouting[self.jobIdx][self.stationIdx] - 1

        # station was idle
        if self.sim.states.serverStatus[station] == idle:
            self.sim.states.serverStatus[station] = busy

            # scheduling departure from this station
            temp = erlang(jobTaskTime[self.jobIdx][self.stationIdx])
            departTime = sim.now() + temp
            sim.scheduleEvent(DepartureEvent(departTime, self.sim, self.stationIdx, self.jobIdx))

        # station was busy
        else:
            self.sim.states.queue[station].append(self)
            self.sim.states.qLen[station] += 1

class DepartureEvent(Event):
    def __init__(self, eventTime, sim, stationIdx, jobIdx):
        self.eventTime = eventTime
        self.eventType = 'DEPARTURE'
        self.sim = sim
        self.stationIdx = stationIdx
        self.jobIdx = jobIdx

    def process(self, sim):
        station = jobStationRouting[self.jobIdx][self.stationIdx] - 1

        # not final station
        # need to schedule arrival to next station
        if self.stationIdx + 1 < jobStationCount[self.jobIdx]:
            arrivalTime = self.eventTime + exponential(interArrivalTime)
            self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim, (self.stationIdx + 1), self.jobIdx))

        # on final station
        else:
            self.sim.states.totalJobsOngoing -= 1

        self.sim.states.served[station] += 1

        # station is busy
        if self.sim.states.qLen[station] > 0:
            self.sim.states.qLen[station] -= 1
            nextOnQ = self.sim.states.queue[station].pop(0)
            delay = self.sim.now() - nextOnQ.eventTime

            # delay calculation for station and job type
            self.sim.states.delayInQ[station] += delay
            self.sim.states.delayInJob[nextOnQ.jobIdx] += delay

            # scheduling a departure
            departTime = sim.now() + erlang(jobTaskTime[nextOnQ.jobIdx][nextOnQ.stationIdx])
            sim.scheduleEvent(DepartureEvent(departTime, self.sim, nextOnQ.stationIdx, nextOnQ.jobIdx))

        else:
            self.sim.states.serverStatus[station] = idle

class Simulator:
    def __init__(self):
        self.eventQ = []
        self.simclock = 0
        self.exitTime = 0
        self.states = States()

    def initialize(self):
        global avgDelayInJobGlobal, totalAvgDelayGlobal, avgJobsCountGlobal, avgNumInQGlobal, avgDelayInQGlobal

        self.simclock = 0
        self.scheduleEvent(StartEvent(0, self))

        # global variable reset for simulation
        avgDelayInJobGlobal = [0] * jobTypes
        totalAvgDelayGlobal = 0
        avgJobsCountGlobal = 0
        avgNumInQGlobal = [0] * stationCount
        avgDelayInQGlobal = [0] * stationCount

    def now(self):
        return self.simclock

    def scheduleEvent(self, event):
        heapq.heappush(self.eventQ, (event.eventTime, event))

    def run(self):
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)

            if event.eventType == 'EXIT':
                self.exitTime = self.now()
                break

            if self.states != None:
                self.states.update(self, event)

            # print(event.eventTime, 'Event', event)
            self.simclock = event.eventTime
            event.process(self)

        return self.states.finish(self)

def jobShopModel():
    seed = 102
    np.random.seed(seed)
    random.seed(seed)

    avgDelayInJob = [0] * jobTypes
    totalAvgDelay = 0
    avgJobsCount = 0
    avgNumInQ = [0] * stationCount
    avgDelayInQ = [0] * stationCount

    for i in range(iteration):
        sim = Simulator()
        sim.run()

        # print(avgDelayInJob, avgDelayInJobGlobal)
        for j in range(jobTypes):
            avgDelayInJob[j] += avgDelayInJobGlobal[j]

        totalAvgDelay += totalAvgDelayGlobal
        avgJobsCount += avgJobsCountGlobal

        for j in range(stationCount):
            avgNumInQ[j] += avgNumInQGlobal[j]
            avgDelayInQ[j] += avgDelayInQGlobal[j]

    for j in range(jobTypes):
        avgDelayInJob[j] /= iteration

    totalAvgDelay /= iteration
    avgJobsCount /= iteration

    for j in range(stationCount):
        avgNumInQ[j] /= iteration
        avgDelayInQ[j] /= iteration

    output = open("Job Shop Output.txt", "w")

    output.write("Average Total Delay in Queue for Jobs:\n")
    for i in range(jobTypes):
        output.write(str(round(avgDelayInJob[i], precision)))
        output.write(" ")

    output.write("\n")
    output.write("Overall Average Delay of System for Jobs: ")
    output.write(str(round(totalAvgDelay, precision)))

    output.write("\n")
    output.write("Expected average number in each queue: \n")
    for i in range(stationCount):
        output.write(str(round(avgNumInQ[i], precision)))
        output.write(" ")

    output.write("\n")
    output.write("Average number of jobs in the whole system: ")
    output.write(str(round(avgJobsCount, precision)))

    output.write("\n")
    output.write("Average Total Delay:\n")
    for i in range(stationCount):
        output.write(str(round(avgDelayInQ[i], precision)))
        output.write(" ")

def main():
    input()
    jobShopModel()

if __name__ == "__main__":
    main()