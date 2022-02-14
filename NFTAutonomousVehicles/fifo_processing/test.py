from datetime import datetime, timedelta
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor
from NFTAutonomousVehicles.fifo_processing.processable import TaskCPUProcessable


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

    processed = cpu_processor.process_all(current_time)
    assert(len(processed) == 0)

    processed = cpu_processor.process_all(current_time + timedelta(seconds=0.5))
    assert(len(processed) == 0)

    processed = cpu_processor.process_all(current_time + timedelta(seconds=1))
    print(processed[0].processed_at)

    processed = cpu_processor.process_all(current_time + timedelta(seconds=1.5))
    assert(len(processed) == 0)

    processed = cpu_processor.process_all(current_time + timedelta(seconds=2))
    print(processed[0].processed_at)

if __name__ == '__main__':
    _test()
