# undirected connected graph

from model.b_event import BEvent
from execution.listeners.print_b_program_runner_listener import PrintBProgramRunnerListener
from model.bprogram import BProgram
from model.event_selection.bubble_event_selection import BubbleEventSelectionStrategy

# public variables
events = ["UNVISITED", "VISITED", "START", "ALL_NODES_VISITED", "ALL_NEIGHBORS_VISITED",
           "CHECK_IF_FINISHED", "VISIT"]


class Node:
    def __init__(self, id, neighbors=None):
        self.id = id
        self.neighbors = neighbors
        self.visited = False

    def get_neighbors(self):
        return self.neighbors

    def set_neighbors(self, neighbors):
        self.neighbors = neighbors

    def visited(self):
        return self.visited

    def set_visited(self):
        self.visited = True

    def get_id(self):
        return self.id


graph = []
for i in range(9):
    graph.append(Node(i))

graph[0].set_neighbors([graph[1], graph[8]])
graph[1].set_neighbors([graph[0]])
graph[2].set_neighbors([graph[3], graph[4], graph[5], graph[8]])
graph[3].set_neighbors([graph[2]])
graph[4].set_neighbors([graph[2], graph[7]])
graph[5].set_neighbors([graph[2], graph[6]])
graph[6].set_neighbors([graph[5], graph[7], graph[8]])
graph[7].set_neighbors([graph[6], graph[4]])
graph[8].set_neighbors([graph[0], graph[2], graph[6]])

visited_nodes = []
finished_nodes = []


# two sensor scenarios
# forward search sensor:
# waits for any CHECK_IF_VISITED(n) event, checks whether the node n has been visited and then requests
# VISITED(n) / UNVISITED(n) accordingly.
def sensor(i):
    while True:
        yield {'waitFor': BEvent(name="CHECK_IF_VISITED", data={i.get_id(): 'g'})}
        if i in visited_nodes:
            yield {'request': BEvent(name="VISITED", data={i.get_id(): 'g'})}
        else:
            yield {'request': BEvent(name="UNVISITED", data={i.get_id(): 'g'})}


# backtracking sensor
# waits for any CHECK_IF_FINISHED(n) event, checks whether the node n's children are finished and then requests
# FINISHED(n) / UNFINISHED(n) accordingly.
def sensor_2(i):
    while True:
        yield {'waitFor': BEvent(name="CHECK_IF_FINISHED", data={i.get_id(): 'g'})}
        if i in finished_nodes:
            yield {'request': BEvent(name="FINISHED", data={i.get_id(): 'g'})}
        else:
            yield {'request': BEvent(name="UNFINISHED", data={i.get_id(): 'g'})}


# visit scenarios
def visit_node(i):
    while True:
        yield {'waitFor': BEvent(name="UNVISITED", data={i.get_id(): 'g'})}
        yield {'request': BEvent(name="VISIT", data={i.get_id(): 'g'})}
        yield {'request': BEvent(name="CHECK_IF_VISITED", data={i.get_id(): 'g'})}


def finish(i):
    while True:
        yield {'waitFor': BEvent(name="UNFINISHED", data={i.get_id(): 'g'})}
        yield {'request': BEvent(name="VISIT_ALL_NEIGHBORS", data={i.get_id(): 'g'})}


def visit_neighbors(i):
    while True:
        yield {'waitFor': BEvent(name="VISIT_ALL_NEIGHBORS", data={i.get_id(): 'g'})}
        for j in i.get_neighbors():
            if j not in visited_nodes:
                yield {'request': BEvent(name="CHECK_IF_VISITED", data={j.get_id(): 'g'})}
                yield {'waitFor': BEvent(name="VISITED", data={j.get_id(): 'g'})}
                yield {'request': BEvent(name="CHECK_IF_FINISHED", data={j.get_id(): 'g'})}
                yield {'waitFor': BEvent(name="FINISHED", data={j.get_id(): 'g'})}
        yield {'request': BEvent(name="ALL_NEIGHBORS_VISITED", data={i.get_id(): 'g'})}
        yield {'request': BEvent(name="CHECK_IF_FINISHED", data={i.get_id(): 'g'})}


# two append to list scenarios
def mark_node_as_visited(i):
    while True:
        yield {'waitFor': BEvent(name="VISIT", data={i.get_id(): 'g'})}
        # VISIT
        visited_nodes.append(i)


def mark_node_as_finished(i):
    while True:
        yield {'waitFor': BEvent(name="ALL_NEIGHBORS_VISITED", data={i.get_id(): 'g'})}
        # FINISH
        finished_nodes.append(i)


# two print scenarios
def print_visited(i):
    while True:
        yield {'waitFor': BEvent(name="VISITED", data={i.get_id(): 'g'})}
        print("visited nodes:")
        for i in visited_nodes:
            print(i.get_id())


def print_finished(i):
    while True:
        yield {'waitFor': BEvent(name="FINISHED", data={i.get_id(): 'g'})}
        print("finished nodes:")
        for j in finished_nodes:
            print(j.get_id())


def dfs_start():
    yield {'block': set([BEvent(name="CHECK_IF_VISITED", data={graph[j].get_id(): 'g'}) for j in range(1, len(graph))] +
                        [BEvent(name=n) for n in events]),
           'request': BEvent(name="CHECK_IF_VISITED", data={graph[0].get_id(): 'g'})}
    yield {'waitFor': BEvent(name="VISITED", data={graph[0].get_id(): 'g'})}
    yield {'request': BEvent(name="CHECK_IF_FINISHED", data={graph[0].get_id(): 'g'})}


if __name__ == "__main__":
    b_program = BProgram(bthreads=[sensor(i) for i in graph] +
                                  [sensor_2(i) for i in graph] +
                                  [visit_node(i) for i in graph] +
                                  [finish(i) for i in graph] +
                                  [visit_neighbors(i) for i in graph] +
                                  [mark_node_as_visited(i) for i in graph] +
                                  [mark_node_as_finished(i) for i in graph] +
                                  [print_visited(i) for i in graph] +
                                  [print_finished(i) for i in graph] +
                                  [dfs_start()],
                         event_selection_strategy=BubbleEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()
