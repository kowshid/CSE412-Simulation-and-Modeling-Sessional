import heapq
import random
import math
import numpy as np
import time

hotfood = 0
sandwich = 1
drinks = 2
cash = 3

groupID = -1

idle = 0
busy = 1

groups = [1, 2, 3, 4]
groupsProb = [0.5, 0.3, 0.1, 0.1]

interArrivalMean = 30.0
simDuration = 90 * 60

counters = [hotfood, sandwich, drinks, cash]
customerTypes = [0, 1, 2]
customerTypesProb = [0.80, 0.15, 0.05]
customerRoutes = [[hotfood, drinks, cash], [sandwich, drinks, cash], [drinks, cash]]

counterST = [[50, 120], [60, 180], [5, 20]]
counterACT = [[20, 40], [5, 15], [5, 10]]

counterCount = [0] * len(counters)

arrivalTracker = []

precision = 4

def exponential(mean):
    return random.expovariate(1 / mean)

class States:
    def __init__(self):
        self.hotfoodQ = []
        self.sandwichQ = []
        self.cashQ = []
        for i in range(counterCount[cash]):
            q = []
            self.cashQ.append(q)

        # self.queue = [hotfoodQ, sandwichQ, [0],  cashQ]
        self.availableServers = [1, 1, math.inf, counterCount[cash]]

        self.cashServersStatus = []
        for i in range(counterCount[cash]):
            self.cashServersStatus.append(idle)

        # don't need the index = 2
        self.avgQDelay = [0.0, 0.0, 0.0, 0.0]
        self.maxQDelay = [0.0, 0.0, 0.0, 0.0]

        # don't need the index = 2
        self.avgQLen = [0.0, 0.0, 0.0, 0.0]
        self.maxQLen = [0, 0, 0, 0]

        self.avgCustomerDelay = [0.0, 0.0, 0.0]
        self.maxCustomerDelay = [0.0, 0.0, 0.0]

        self.customerServedCounter = [0] * len(counters)
        self.customerArrivedType = [0] * len(customerTypes)

        self.timeLastEvent = 0
        self.maxCustomer = 0
        self.activeCustomers = 0
        self.overallAvgDelay = 0
        self.avgCustomerInSystem = 0
        self.timeSpent = 0

    def update(self, event):
        timeSinceLastEvent = event.eventTime - self.timeLastEvent
        self.timeLastEvent = event.eventTime

        # max customer at a time
        self.maxCustomer = max(self.maxCustomer, self.activeCustomers)
        self.avgCustomerInSystem += timeSinceLastEvent * self.activeCustomers

        self.avgQLen[hotfood] += len(self.hotfoodQ) * timeSinceLastEvent
        self.avgQLen[sandwich] += len(self.sandwichQ) * timeSinceLastEvent
        for i in range(counterCount[cash]):
            self.avgQLen[cash] = len(self.cashQ[i]) * timeSinceLastEvent

        # avg q lengths
        self.maxQLen[hotfood] = max(self.maxQLen[hotfood], len(self.hotfoodQ))
        self.maxQLen[sandwich] = max(self.maxQLen[sandwich], len(self.sandwichQ))
        for i in range(counterCount[cash]):
            self.maxQLen[cash] = max(self.maxQLen[cash], len(self.cashQ[i]))

    def finish(self, sim):
        # average delay and q lengths in queues
        # print(self.customerServedCounter)
        for i in range(len(counters)):
            if i == 2:
                None
            else:
                self.avgQDelay[i] /= self.customerServedCounter[i]
                self.avgQLen[i] /= sim.exitTime

        self.overallAvgDelay = 0

        for i in range(len(customerTypes)):
            self.avgCustomerDelay[i] /= self.customerArrivedType[i]
            self.overallAvgDelay += self.avgCustomerDelay[i] * customerTypesProb[i]

        # average served
        self.avgCustomerInSystem = self.avgCustomerInSystem / sim.exitTime

    def printResults(self):
        # print all the results
        print("Average Customers in System: ", round(self.avgCustomerInSystem, precision))
        print("Maximum Customers in System: ", self.maxCustomer)
        print("Total Customer served: ", self.customerServedCounter[cash])
        print("Overall Average Delay: ", round(self.overallAvgDelay, precision))
        print("Average Queue Length of Counters")
        print(self.avgQLen)
        print("Max Queue Length for Counters")
        print(self.maxQLen)
        print("Average Delay in Oueue for Counters")
        print(self.avgQDelay)
        print("Max Delay in Oueue for Counters")
        print(self.maxQDelay)
        print("Average Delay for Types of Customers")
        print(self.avgCustomerDelay)
        print("Max Delay for Type of Customers")
        print(self.maxCustomerDelay)

class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.eventTime = None

    def process(self):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType

    def __lt__(self, other):
        return True


class StartEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'START'
        self.sim = sim

    def process(self):
        global groupID

        arrivalTime = self.sim.now() + exponential(interArrivalMean)
        groupID += 1
        groupSize = np.random.choice(groups, p = groupsProb)

        # scheduling first arrival
        # q Number and station index will be zero
        for i in range(groupSize):
            customerType = np.random.choice(customerTypes, p = customerTypesProb)
            self.sim.states.customerArrivedType[customerType] += 1
            self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim, groupID, customerType, 0, 0))

        self.sim.scheduleEvent(ExitEvent(simDuration, self.sim))


class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self):
        print("simulation is going to end now. current time:", self.eventTime)


class ArrivalEvent(Event):
    def __init__(self, eventTime, sim, groupID, customerType, currentCounterIdx, qNumber):
        self.eventTime = eventTime
        self.eventType = 'ARRIVAL'
        self.sim = sim
        self.groupNo = groupID  # every chunk of people is assigned a unique number
        self.customerType = customerType  # customer type : hot_food/sandwich/drinks
        self.currentCounterIdx = currentCounterIdx  # current station number, an index
        self.qNumber = qNumber  # the server number where the customer is taking service / q where it is waiting

    # arrival is done groupwise, not individually
    def process(self):
        global groupID

        # first station, so customer in the system will increase
        if self.currentCounterIdx == 0:
            self.sim.states.activeCustomers += 1
            self.sim.states.timeSpent = 0

        # schedule next group arrival
        if self.currentCounterIdx == 0 and self.groupNo not in arrivalTracker:
            arrivalTracker.append(self.groupNo)

            arrivalTime = self.sim.now() + exponential(interArrivalMean)
            groupID += 1
            groupSize = np.random.choice(groups, p=groupsProb)

            for i in range(groupSize):
                tempCustomerType = np.random.choice(customerTypes, p = customerTypesProb)
                self.sim.states.customerArrivedType[tempCustomerType] += 1
                self.sim.scheduleEvent(ArrivalEvent(arrivalTime, self.sim, groupID, tempCustomerType, 0, 0))

        # finding counter from counter index
        currentCounter = customerRoutes[self.customerType][self.currentCounterIdx]

        # process the current arrival
        # server not available, q push
        if self.sim.states.availableServers[currentCounter] == 0:
            # append to the shortest queue for cash
            # for hotfood and sandwich idx will always be 0
            # for drinks it will never reach there

            if currentCounter == cash:
                idx = 0
                currentQLen = math.inf
                for i in range(len(self.sim.states.cashQ)):
                    if len(self.sim.states.cashQ[i]) < currentQLen:
                        currentQLen = len(self.sim.states.cashQ[i])
                        idx = i

                self.qNumber = idx
                self.sim.states.cashQ[idx].append(self)

            elif currentCounter == hotfood:
                self.qNumber = 0
                self.sim.states.hotfoodQ.append(self)

            elif currentCounter == sandwich:
                self.qNumber = 0
                self.sim.states.sandwichQ.append(self)

            elif currentCounter == drinks:
                print("Vul hoise")

        # servers available so scheduling departure
        elif self.sim.states.availableServers[currentCounter] > 0:
            self.sim.states.availableServers[currentCounter] -= 1

            # for cash find which q it is, else keeping qNumber 0
            for i in range(len(self.sim.states.cashServersStatus)):
                if self.sim.states.cashServersStatus[i] == idle:
                    self.sim.states.cashServersStatus[i] = busy
                    self.qNumber = i
                    break

            # for cash use act, else use st
            totalServiceTime = 0
            if currentCounter == cash:
                for i in range(len(counterACT)):
                    if i in customerRoutes[self.customerType]:
                        rand = np.random.uniform(counterACT[i][0], counterACT[i][1])
                        totalServiceTime += rand
            else:
                totalServiceTime = np.random.uniform(counterST[currentCounter][0], counterST[currentCounter][1])

            departTime = self.eventTime + totalServiceTime
            self.sim.scheduleEvent(DepartureEvent(departTime, self.sim, self.groupNo, self.customerType,
                                                  self.currentCounterIdx, self.qNumber))


class DepartureEvent(Event):
    def __init__(self, eventTime, sim, groupID, customerType, currentCounterIdx, qNumber):
        self.eventTime = eventTime
        self.eventType = 'DEPARTURE'
        self.sim = sim
        self.groupNo = groupID  # every chunk of people is assigned a unique number
        self.customerType = customerType  # customer type : hot_food/sandwich/drinks
        self.currentCounterIdx = currentCounterIdx  # current station number, an index
        self.qNumber = qNumber  # the server number where the customer is taking service / q where it is waiting

    def process(self):
        # finding counter from counter index
        # increasing customer served for counter
        currentCounter = customerRoutes[self.customerType][self.currentCounterIdx]
        self.sim.states.customerServedCounter[currentCounter] += 1

        if currentCounter == hotfood:
            # q is empty
            if len(self.sim.states.hotfoodQ) == 0:
                self.sim.states.availableServers[currentCounter] += 1
            # q is not empty, process nextOnQ's departures and related delays
            elif len(self.sim.states.hotfoodQ) > 0:
                nextOnQ = self.sim.states.hotfoodQ.pop(0)

                delay = self.eventTime - nextOnQ.eventTime
                self.sim.states.avgQDelay[currentCounter] += delay
                self.sim.states.maxQDelay[currentCounter] = max(self.sim.states.maxQDelay[currentCounter], delay)

                self.sim.states.avgCustomerDelay[self.customerType] += delay
                self.sim.states.maxCustomerDelay[self.customerType] = max(
                    self.sim.states.maxCustomerDelay[self.customerType], delay)

                totalServiceTime = np.random.uniform(counterST[currentCounter][0], counterST[currentCounter][1])
                departTime = self.eventTime + totalServiceTime

                # qNumber will be 0, as departing from hotfood or sandwich
                self.sim.scheduleEvent(DepartureEvent(departTime, nextOnQ.sim, nextOnQ.groupNo, nextOnQ.customerType,
                                                      nextOnQ.currentCounterIdx, 0))
            # scheduling arrival to next station
            self.sim.scheduleEvent(ArrivalEvent(self.eventTime, self.sim, self.groupNo, self.customerType,
                                                self.currentCounterIdx + 1, self.qNumber))

        elif currentCounter == sandwich:
            #q is empty
            if len(self.sim.states.sandwichQ) == 0:
                self.sim.states.availableServers[currentCounter] += 1
            # q is not empty, process nextOnQ's departures and related delays
            elif len(self.sim.states.sandwichQ) > 0:
                nextOnQ = self.sim.states.sandwichQ.pop(0)

                delay = self.eventTime - nextOnQ.eventTime
                self.sim.states.avgQDelay[currentCounter] += delay
                self.sim.states.maxQDelay[currentCounter] = max(self.sim.states.maxQDelay[currentCounter], delay)

                self.sim.states.avgCustomerDelay[self.customerType] += delay
                self.sim.states.maxCustomerDelay[self.customerType] = max(
                    self.sim.states.maxCustomerDelay[self.customerType], delay)
                totalServiceTime = np.random.uniform(counterST[currentCounter][0], counterST[currentCounter][1])
                departTime = self.eventTime + totalServiceTime

                # qNumber will be 0, as departing from hotfood or sandwich
                self.sim.scheduleEvent(DepartureEvent(departTime, nextOnQ.sim, nextOnQ.groupNo, nextOnQ.customerType,
                                                      nextOnQ.currentCounterIdx, 0))
            # # scheduling arrival to next station
            self.sim.scheduleEvent(ArrivalEvent(self.eventTime, self.sim, self.groupNo, self.customerType,
                                                self.currentCounterIdx + 1, self.qNumber))

        elif currentCounter == drinks:
            # need to calculate the service time and depart to next station
            totalServiceTime = np.random.uniform(counterST[currentCounter][0], counterST[currentCounter][1])
            self.sim.states.timeSpent += totalServiceTime
            departTime = self.eventTime + totalServiceTime
            self.sim.scheduleEvent(ArrivalEvent(departTime, self.sim, self.groupNo, self.customerType,
                                                self.currentCounterIdx + 1, self.qNumber))

        elif currentCounter == cash:
            # q is empty
            if len(self.sim.states.cashQ[self.qNumber]) == 0:
                self.sim.states.availableServers[currentCounter] += 1
                self.sim.states.cashServersStatus[self.qNumber] = idle
            # q is not empty, nextOnQ's departures and related delays
            elif len(self.sim.states.cashQ[self.qNumber]) > 0:
                nextOnQ = self.sim.states.cashQ[self.qNumber].pop(0)

                delay = self.eventTime - nextOnQ.eventTime
                self.sim.states.avgQDelay[currentCounter] += delay
                self.sim.states.maxQDelay[currentCounter] = max(self.sim.states.maxQDelay[currentCounter], delay)

                self.sim.states.avgCustomerDelay[self.customerType] += delay
                self.sim.states.timeSpent += delay
                self.sim.states.maxCustomerDelay[self.customerType] = max(
                    self.sim.states.maxCustomerDelay[self.customerType], delay)

                # print("CASH", currentCounter)

                totalServiceTime = 0
                for i in range(len(counterACT)):
                    if i in customerRoutes[self.customerType]:
                        rand = np.random.uniform(counterACT[i][0], counterACT[i][1])
                        totalServiceTime += rand
                departTime = self.eventTime + totalServiceTime

                self.sim.scheduleEvent(DepartureEvent(departTime, nextOnQ.sim, nextOnQ.groupNo, nextOnQ.customerType,
                                                      nextOnQ.currentCounterIdx, nextOnQ.qNumber))
                self.sim.states.activeCustomers -= 1
                # no arrival to any more stations

class Simulator:
    def __init__(self):
        self.eventQ = []
        self.simclock = 0
        self.states = States()
        self.exitTime = 0

    def initialize(self):
        self.simclock = 0
        self.scheduleEvent(StartEvent(0, self))

    def now(self):
        return self.simclock

    def scheduleEvent(self, event):
        heapq.heappush(self.eventQ, (event.eventTime, event))

    def run(self):
        self.initialize()

        start = time.time()
        while len(self.eventQ) > 0:
            currentTime, event = heapq.heappop(self.eventQ)
            if event.eventType == 'EXIT':
                self.exitTime = self.now()
                break

            if self.states is not None:
                self.states.update(event)

            self.simclock = event.eventTime
            event.process()
            # print(event.eventTime, event.eventType)

        end = time.time()
        print("time taken to finish simulation:", end - start, end="\n\n")

        self.states.finish(self)
        self.states.printResults()

def cafeteriaModel(hotfoodCounter, sandwichCounter, cashCounter):
    global counterCount, counterST, counterACT

    counterCount[0] = hotfoodCounter
    counterCount[1] = sandwichCounter
    counterCount[2] = math.inf
    counterCount[3] = cashCounter
    for i in range(len(counterST)):
        for j in range(len(counterST[0])):
            counterST[i][j] /= counterCount[j]
            counterACT[i][j] /= counterCount[j]

    # print(counterCount)

    seed = 102
    np.random.seed(seed)
    random.seed(seed)

    sim = Simulator()
    sim.run()

def main():
    cafeteriaModel(1, 1, 2)

if __name__ == "__main__":
    main()
