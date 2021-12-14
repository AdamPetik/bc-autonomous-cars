from NFTAutonomousVehicles.resultCollectors.MainCollector import MainCollector
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
import  datetime

from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus


def main():
    collector = MainCollector()



    # datum = datetime.datetime.now()
    # nft = NFT(12, 2533, datum, datum, 10)
    #
    #
    # task = Task(1212, 25332533, 2536.25, 55, 15, datum, datum)
    # task.nft = nft
    # task.status=TaskStatus.PROCESSING_FAILED
    # task.received_by_task_solver_at = datum
    # task.solved_by_task_solver_at = datum
    # task.returned_to_creator_at = datum
    # task.name = "Testovaci Task"
    #
    # collector.insertTask(task)
    # 
    #

if __name__ == "__main__":
    main()