"""
The task is to simulate an M/M/k system with a single queue.
Complete the skeleton code and produce results for three experiments.
The study is mainly to show various results of a queue against its ro parameter.
ro is defined as the ratio of arrival rate vs service rate.
For the sake of comparison, while plotting results from simulation, also produce the analytical results.
"""

import heapq
import random
import matplotlib.pyplot as plt

def exponential(rate):
    return random.expovariate(rate)

busy = 1
idle = 0
simDuration = 99999

# Parameters
class Params:
    def __init__(self, lambd, mu, k):
        self.lambd = lambd  # interarrival rate
        self.mu = mu  # service rate
        self.k = k
    # Note lambd and mu are not mean value, they are rates i.e. (1/mean)

# Write more functions if required

# States and statistical counters
class States:
    def __init__(self):
        # States
        self.queue = []
        # Declare other states variables that might be needed

        # Statistics
        self.util = 0.0
        self.avgQdelay = 0.0
        self.avgQlength = 0.0
        self.served = 0

        self.serverStatus = idle
        self.peopleInQ = 0
        self.totalDelayTime = 0
        self.totalServiceTime = 0
        self.totalDelayedPeople = 0
        self.areaNumInQ = 0
        self.timeLastEvent = 0

    def update(self, sim, event):
        timeSinceLastEvent = event.eventTime - self.timeLastEvent
        self.timeLastEvent = event.eventTime

        self.areaNumInQ += self.peopleInQ * timeSinceLastEvent
        self.totalServiceTime += self.serverStatus * timeSinceLastEvent

    def finish(self, sim):

        self.util = self.totalServiceTime / sim.exitTime
        self.avgQdelay = self.totalDelayTime / self.served
        #print("total delay time")
        #print(self.totalDelayTime)
        self.avgQlength = self.areaNumInQ / sim.exitTime


    def printResults(self, sim):
        print('MM1 Results: lambda = %lf, mu = %lf, k = %d' % (sim.params.lambd, sim.params.mu, sim.params.k))
        print('MM1 Total customer served: %d' % (self.served))
        print('MM1 Average queue length: %lf' % (self.avgQlength))
        print('MM1 Average customer delay in queue: %lf' % (self.avgQdelay))
        print('MM1 Time-average server utility: %lf' % (self.util))

    def getResults(self, sim):
        return (self.avgQlength, self.avgQdelay, self.util)

# Write more functions if required

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
        arrivalTime = self.eventTime + exponential(self.sim.params.lambd)
        self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim))

        # set the exit event here
        self.sim.scheduleEvent(ExitEvent(simDuration, self.sim))

class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        print("Simulation Ended\n")

class ArrivalEvent(Event):
    # Write __init__ function
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'ARRIVAL'
        self.sim = sim

    def process(self, sim):
        timeNextEvent = sim.now() + exponential(sim.params.lambd)
        sim.scheduleEvent(ArrivalEvent(timeNextEvent, sim))

        if sim.states.serverStatus == busy:
            sim.states.peopleInQ += 1
            sim.states.queue.append(sim.now())
            sim.states.totalDelayedPeople += 1

        else:
            sim.states.serverStatus = busy
            sim.states.served += 1

            departTime = sim.now() + exponential(sim.params.mu)
            sim.scheduleEvent(DepartureEvent(departTime, sim))

class DepartureEvent(Event):
    # Write __init__ function
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'DEPARTURE'
        self.sim = sim

    def process(self, sim):
        if sim.states.peopleInQ > 0:
            sim.states.peopleInQ -= 1

            delay = sim.now() - sim.states.queue[0]
            sim.states.totalDelayTime += delay
            sim.states.served += 1

            departTime = sim.now() + exponential(sim.params.mu)
            sim.scheduleEvent(DepartureEvent(departTime, sim))

            sim.states.queue.pop(0)

        else:
            sim.states.serverStatus = idle
            #print("No deperture operation, Q is empty\n")

class Simulator:
    def __init__(self, seed):
        self.eventQ = []
        self.simclock = 0
        self.seed = seed
        self.exitTime = 0
        self.params = None
        self.states = None

    def initialize(self):
        self.simclock = 0
        self.scheduleEvent(StartEvent(0, self))

    def configure(self, params, states):
        self.params = params
        self.states = states

    def now(self):
        return self.simclock

    def scheduleEvent(self, event):
        heapq.heappush(self.eventQ, (event.eventTime, event))

    def run(self):
        random.seed(self.seed)
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)

            if event.eventType == 'EXIT':
                self.exitTime = self.now()
                break

            if self.states != None:
                self.states.update(self, event)

            #print(event.eventTime, 'Event', event)
            self.simclock = event.eventTime
            event.process(self)

        self.states.finish(self)

    def printResults(self):
        self.states.printResults(self)

    def getResults(self):
        return self.states.getResults(self)

    def printAnalyticalResults(self):
        avgQlen = (self.params.lambd * self.params.lambd) / (self.params.mu * (self.params.mu - self.params.lambd))
        avgDelayInQ = self.params.lambd / (self.params.mu * (self.params.mu - self.params.lambd))
        serverUtilFactor = self.params.lambd / self.params.mu
        print("Analytical Results:\n")
        print('MM1 Average queue length: %lf' % (avgQlen))
        print('MM1 Average customer delay in queue: %lf' % (avgDelayInQ))
        print('MM1 Time-average server utility: %lf' % (serverUtilFactor))

def experiment1():
    seed = 101
    sim = Simulator(seed)
    sim.configure(Params(5.0 / 60, 8.0 / 60, 1), States())
    sim.run()
    sim.printResults()
    sim.printAnalyticalResults()

def main():
    experiment1()

if __name__ == "__main__":
    main()