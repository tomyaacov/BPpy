from model.b_event import BEvent
from execution.listeners.print_b_program_runner_listener import PrintBProgramRunnerListener
from model.bprogram import BProgram
from model.event_selection.simple_event_selection_strategy import SimpleEventSelectionStrategy
import random

# public variables
my_array = random.sample(range(1, 100), 10)
chosen = ""
events = ["CHECK_ORDER", "UNSORTED", "SORTED", "EXTERNAL_CHANGE",
          "START", "SUFFIX_IS_SORTED", "ENTIRE_ARRAY_IS_SORTED", "SWAP"]
events2 = ["UNSORTED", "SORTED", "EXTERNAL_CHANGE",
           "START", "SUFFIX_IS_SORTED", "ENTIRE_ARRAY_IS_SORTED", "SWAP"]
events3 = [BEvent(name="CHECK_ORDER", data={i: i+1}) for i in range(len(my_array) - 1)] + \
          [BEvent(name="UNSORTED", data={i: i+1}) for i in range(len(my_array) - 1)] + \
          [BEvent(name="SORTED", data={i: i+1}) for i in range(len(my_array) - 1)] + \
          [BEvent(name="EXTERNAL_CHANGE", data={i: i+1}) for i in range(len(my_array) - 1)] + \
          [BEvent(name="START")] + \
          [BEvent(name="SUFFIX_IS_SORTED", data={i: i+1}) for i in range(len(my_array) - 1)] + \
          [BEvent(name="ENTIRE_ARRAY_IS_SORTED")] + \
          [BEvent(name="SWAP", data={i: i+1}) for i in range(len(my_array) - 1)]


def sensor(i):
    while True:
        yield {'waitFor': BEvent(name="CHECK_ORDER", data={i: i+1})}
        if my_array[i] <= my_array[i+1]:
            yield {'request': BEvent(name="SORTED", data={i: i+1})}
        else:
            yield {'request': BEvent(name="UNSORTED", data={i: i+1})}


def sort_pair(i):
    while True:
        yield {'waitFor': BEvent(name="UNSORTED", data={i: i+1})}
        yield {'request': BEvent(name="SWAP", data={i: i+1})}
        yield {'request': BEvent(name="CHECK_ORDER", data={i: i+1})}


def swap_pair(i):
    while True:
        yield {'waitFor': BEvent(name="SWAP", data={i: i+1})}
        # swap
        temp = my_array[i]
        my_array[i] = my_array[i+1]
        my_array[i + 1] = temp


def bubble_pair(i):
    while True:
        yield {'waitFor': BEvent(name="SORTED", data={i: i+1})}
        yield {'request': BEvent(name="CHECK_ORDER", data={i+1: i+2})}


def bubble_start_next_pass(i):
    while True:
        yield {'waitFor': BEvent(name="UNSORTED", data={i: i+1})}
        yield {'waitFor': BEvent(name="SORTED", data={len(my_array) - 2: len(my_array) - 1})}
        yield {'request': BEvent(name="CHECK_ORDER", data={0: 1})}


def suffix_is_sorted(i):
    while True:
        if i < len(my_array)-1:
            yield {'waitFor': BEvent(name="SUFFIX_IS_SORTED", data={i: i + 1})}
        yield {'waitFor': BEvent(name="SORTED", data={i-1: i})}
        blocked = set([BEvent(name="CHECK_ORDER", data={j: j+1}) for j in range(i-1, len(my_array)-1)])
        for elem in blocked:
            print("blocked: ", elem)
        yield {'request': BEvent(name="SUFFIX_IS_SORTED", data={i-1: i}), 'block': blocked}
        while True:
            yield {'block': blocked}


def print_array(i):
    while True:
        yield {'waitFor': BEvent(name="SUFFIX_IS_SORTED", data={i: i+1})}
        print(my_array)


# def log_selected(i):
#     with open('bubble_event_log', 'w') as event_log_file:
#         event_log_file.write("")
#     while True:
#         last_event = yield {'waitFor': BEvent(name="SUFFIX_IS_SORTED", data={i: i+1})}
#         with open('bubble_event_log', 'a') as event_log_file:
#             event_log_file.write(last_event.name + str(last_event.data) + "\n")


def bubble_sort_start():  # block rest, not random event selection (choose start first)
    yield {'block': set([BEvent(name="CHECK_ORDER", data={j: j+1}) for j in range(1, len(my_array) - 1)] +
                        [BEvent(name=n) for n in events2]),
           'request': BEvent(name="CHECK_ORDER", data={0: 1})}


def wait_for_a_couple(chosen):
    events_to_wait = set([BEvent(name="SORTED", data={i: i+1}) for i in range(len(my_array) - 1)])
    while events_to_wait:
        print("hi")
        chosen = yield {'waitFor': events_to_wait}
        print("hiii")
        events_to_wait.discard(chosen)
        print(chosen)
        print(events_to_wait)


if __name__ == "__main__":
    b_program = BProgram(bthreads=[bubble_sort_start()] +
                                  [print_array(i) for i in range(len(my_array)-1)] +
                                  [bubble_start_next_pass(i) for i in range(len(my_array)-1)] +
                                  [bubble_pair(i) for i in range(len(my_array)-2)] +
                                  [swap_pair(i) for i in range(len(my_array)-1)] +
                                  [suffix_is_sorted(i) for i in range(len(my_array))] +
                                  [wait_for_a_couple(chosen)] +
                                  [sensor(i) for i in range(len(my_array)-1)] +
                                  # [log_selected(i) for i in range(len(my_array)-1)] +
                                  [sort_pair(i) for i in range(len(my_array)-1)],
                         event_selection_strategy=SimpleEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()
    print(my_array)
