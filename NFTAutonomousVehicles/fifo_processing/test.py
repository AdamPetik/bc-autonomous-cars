from datetime import datetime, timedelta
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor
from NFTAutonomousVehicles.fifo_processing.processable import TaskCPUProcessable


def _test():
    dt = 0.5
    start_at = datetime(2020, 1, 1, 10, 50)
    task = Task(instruction_count=150)
    cpu_processor = FIFOProcessor(100, dt)
    task_processable = TaskCPUProcessable(task, start_at)

    cpu_processor.add((start_at, task_processable))

    processed = cpu_processor.process_all(start_at - timedelta(seconds=0.5))
    assert(processed is None)

    processed = cpu_processor.process_all(start_at)
    assert(processed is None)

    processed = cpu_processor.process_all(start_at + timedelta(seconds=0.5))
    print(processed[0].processed_at)

if __name__ == '__main__':
    _test()
