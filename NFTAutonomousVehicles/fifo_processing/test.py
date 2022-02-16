from datetime import datetime, timedelta
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.radio_communication.radio_communication_processor import SimpleBSRadioCommProcessor
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor
from NFTAutonomousVehicles.fifo_processing.processable import TaskCPUProcessable, TaskConnectionProcessable


def _test():
    dt = 0.5
    current_time = datetime(2020, 1, 1, 10, 50, 0)
    start_at = datetime(2020, 1, 1, 10, 50, 0, int(0.6e6))
    task1 = Task(instruction_count=150)
    task2 = Task(instruction_count=150)
    cpu_processor = FIFOProcessor(100, dt)
    task_processable1 = TaskCPUProcessable(task1, start_at)
    task_processable2 = TaskCPUProcessable(task2, start_at)

    cpu_processor.add((start_at,'1', task_processable1))
    cpu_processor.add((start_at,'2', task_processable2))

    processed = cpu_processor.process(current_time)
    assert(len(processed) == 0)

    processed = cpu_processor.process(current_time + timedelta(seconds=0.5))
    assert(len(processed) == 0)

    processed = cpu_processor.process(current_time + timedelta(seconds=1))
    print(processed[0].processed_at)

    processed = cpu_processor.process(current_time + timedelta(seconds=1.5))
    assert(len(processed) == 0)

    processed = cpu_processor.process(current_time + timedelta(seconds=2))
    print(processed[0].processed_at)

def _test_rcp():
    class Vehicle():
        def __init__(self, id) -> None:
            self.id = id
        def getLocation():
            return None
    start = datetime(2020, 1, 1, 1, 0)
    dt = 0.5
    vehicles = [Vehicle(0), Vehicle(1), Vehicle(2)]

    processables = [
        TaskConnectionProcessable(
            Task(instruction_count=15, size_in_megabytes=15, vehicle=vehicles[0]),
            start + timedelta(seconds=0.2)
        ),
        TaskConnectionProcessable(
            Task(instruction_count=15, size_in_megabytes=15, vehicle=vehicles[1]),
            start + timedelta(seconds=0.2)
        ),
        TaskConnectionProcessable(
            Task(instruction_count=15, size_in_megabytes=15, vehicle=vehicles[2]),
            start + timedelta(seconds=0.2)
        )
    ]

    fifos = {
        0: FIFOProcessor(0, dt),
        1: FIFOProcessor(0, dt),
        2: FIFOProcessor(0, dt),
    }
    fifos[0].add((processables[0].can_start_at, processables[0].entity.id, processables[0]))
    fifos[1].add((processables[1].can_start_at, processables[1].entity.id, processables[1]))
    fifos[2].add((processables[2].can_start_at, processables[2].entity.id, processables[2]))

    bs = TaskSolver(None, None, dt)
    bsrcp = SimpleBSRadioCommProcessor(bs, fifos, dt, lambda a,b,c: 30)
    result = bsrcp.process(start)
    print(len(result))
    print(result[0].processed_at)
    print(result[1].processed_at)
    print(result[2].processed_at)


if __name__ == '__main__':
    _test_rcp()
