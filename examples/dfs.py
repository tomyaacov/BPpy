from model.b_event import BEvent
from execution.listeners.print_b_program_runner_listener import PrintBProgramRunnerListener
from model.bprogram import BProgram
from model.event_selection.bubble_event_selection import BubbleEventSelectionStrategy

# public variables
events = ["UNVISITED", "VISITED", "START", "ALL_NODES_VISITED", "ALL_DESCENDENTS_VISITED",
           "CHECK_IF_FINISHED", "VISIT"]


class Node:
    def __init__(self, value, parent, children=None):
        self.value = value
        self.parent = parent
        self.children = children
        self.visited = False

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent

    def get_children(self):
        return self.children

    def visited(self):
        return self.visited

    def set_visited(self):
        self.visited = True

    def get_value(self):
        return self.value


n6 = Node(6, None)
n5 = Node(5, None)
n4 = Node(4, None)
n3 = Node(3, None)
n2 = Node(2, None, [n6])
n1 = Node(1, None, [n3, n4, n5])
n0 = Node(0, None, [n1, n2])

n1.set_parent(n0)
n2.set_parent(n0)
n3.set_parent(n1)
n4.set_parent(n1)
n5.set_parent(n1)
n6.set_parent(n2)

graph = [n0, n1, n2, n3, n4, n5, n6]
visited_nodes = []
finished_nodes = []


# two sensor scenarios
# forward search sensor:
# waits for any CHECK_IF_VISITED(n) event, checks whether the node n has been visited and then requests
# VISITED(n) / UNVISITED(n) accordingly.
def sensor(i):
    while True:
        yield {'waitFor': BEvent(name="CHECK_IF_VISITED", data={i.get_value(): 'g'})}
        if i in visited_nodes:
            yield {'request': BEvent(name="VISITED", data={i.get_value(): 'g'})}
        else:
            yield {'request': BEvent(name="UNVISITED", data={i.get_value(): 'g'})}


# backtracking sensor
# waits for any CHECK_IF_FINISHED(n) event, checks whether the node n's children are finished and then requests
# FINISHED(n) / UNFINISHED(n) accordingly.
def sensor_2(i):
    while True:
        yield {'waitFor': BEvent(name="CHECK_IF_FINISHED", data={i.get_value(): 'g'})}
        if i in finished_nodes:
            yield {'request': BEvent(name="FINISHED", data={i.get_value(): 'g'})}
        else:
            yield {'request': BEvent(name="UNFINISHED", data={i.get_value(): 'g'})}


# two visit scenarios
def visit_node(i):
    while True:
        yield {'waitFor': BEvent(name="UNVISITED", data={i.get_value(): 'g'})}
        yield {'request': BEvent(name="VISIT", data={i.get_value(): 'g'})}
        yield {'request': BEvent(name="CHECK_IF_VISITED", data={i.get_value(): 'g'})}


def visit_descendants(i):
    while True:
        yield {'waitFor': BEvent(name="UNFINISHED", data={i.get_value(): 'g'})}
        for j in i.get_children():
            yield {'request': BEvent(name="CHECK_IF_VISITED", data={j.get_value(): 'g'})}
            yield {'waitFor': BEvent(name="VISITED", data={j.get_value(): 'g'})}
            if not j.get_children():
                yield {'request': BEvent(name="VISIT_ALL_DESCENDANTS", data={j.get_value(): 'g'})}
            yield {'request': BEvent(name="CHECK_IF_FINISHED", data={j.get_value(): 'g'})}
            yield {'waitFor': BEvent(name="FINISHED", data={j.get_value(): 'g'})}
        yield {'request': BEvent(name="VISIT_ALL_DESCENDANTS", data={i.get_value(): 'g'})}
        yield {'request': BEvent(name="CHECK_IF_FINISHED", data={i.get_value(): 'g'})}


# two append to list scenarios
def mark_node_as_visited(i):
    while True:
        yield {'waitFor': BEvent(name="VISIT", data={i.get_value(): 'g'})}
        # VISIT
        visited_nodes.append(i)


def mark_node_as_finished(i):
    while True:
        yield {'waitFor': BEvent(name="VISIT_ALL_DESCENDANTS", data={i.get_value(): 'g'})}
        # FINISH
        finished_nodes.append(i)


# two print scenarios
def print_visited(i):
    while True:
        yield {'waitFor': BEvent(name="VISITED", data={i.get_value(): 'g'})}
        print("visited nodes:")
        for i in visited_nodes:
            print(i.get_value())


def print_finished(i):
    while True:
        yield {'waitFor': BEvent(name="FINISHED", data={i.get_value(): 'g'})}
        print("finished nodes:")
        for j in finished_nodes:
            print(j.get_value())


def dfs_start():
    yield {'block': set([BEvent(name="CHECK_IF_VISITED", data={graph[j].get_value(): 'g'}) for j in range(1, len(graph))] +
                        [BEvent(name=n) for n in events]),
           'request': BEvent(name="CHECK_IF_VISITED", data={graph[0].get_value(): 'g'})}
    yield {'waitFor': BEvent(name="VISITED", data={graph[0].get_value(): 'g'})}
    yield {'request': BEvent(name="CHECK_IF_FINISHED", data={graph[0].get_value(): 'g'})}


if __name__ == "__main__":
    b_program = BProgram(bthreads=[sensor(i) for i in graph] +
                                  [sensor_2(i) for i in graph] +
                                  [visit_node(i) for i in graph] +
                                  [visit_descendants(i) for i in graph] +
                                  [mark_node_as_visited(i) for i in graph] +
                                  [mark_node_as_finished(i) for i in graph] +
                                  [print_visited(i) for i in graph] +
                                  [print_finished(i) for i in graph] +
                                  [dfs_start()],
                         event_selection_strategy=BubbleEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()