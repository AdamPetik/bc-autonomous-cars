import sqlite3
import datetime

from NFTAutonomousVehicles.taskProcessing.Task import Task


class MainCollector:


    def __init__(self):
        filename = "results_" + str(datetime.datetime.now()).replace(" ","_")
        self.conn = sqlite3.connect(filename)
        print("SQLITE connection ready" + sqlite3.version)

    def closeCollector(self):
        self.conn.close()
        self.conn = None


    def create_table(self):
        SQL_CREATE_TASK_STATE_TABLE = """ CREATE TABLE IF NOT EXISTS task_state (
                                                status_id integer PRIMARY KEY,
                                                name text NOT NULL
                                            ); """

        SQL_CREATE_TASK_TABLE = """ CREATE TABLE IF NOT EXISTS task (
                                                task_id integer PRIMARY KEY,
                                                vehicle_id integer NOT NULL,
                                                solver_id integer NOT NULL,
                                                capacity_needed_to_solve integer NOT NULL,
                                                size_in_megabytes integer NOT NULL,
                                                transfer_rate real NOT NULL,
                                                status_id integer NOT NULL,
                                                created_at TEXT NOT NULL,
                                                deadline_at TEXT NOT NULL,
                                                received_by_task_solver_at TEXT NOT NULL,
                                                solved_by_task_solver_at TEXT NOT NULL,
                                                returned_to_creator_at TEXT NOT NULL,
                                                nft_id integer NOT NULL
                                                nft_valid_from TEXT NOT NULL,
                                                nft_valid_to TEXT NOT NULL,
                                                nft_reserved_cores_each_iteration int NOT NULL
                                                FOREIGN KEY (status_id) REFERENCES task_state (status_id)
                                            ); """

        cursor = self.conn.cursor()
        cursor.execute(SQL_CREATE_TASK_STATE_TABLE)
        cursor.execute(SQL_CREATE_TASK_TABLE)

        self.insertTaskSTatus(1, "SUBMITTED")
        self.insertTaskSTatus(2, "BEING_PROCESSED")
        self.insertTaskSTatus(3, "SOLVED")
        self.insertTaskSTatus(4, "PROCESSING_FAILED")
        self.insertTaskSTatus(5, "TASK_TIMED_OUT")


    def insertTaskSTatus(self, id, name):
        insert_query = f"""INSERT INTO task_state
                            (id, name) 
                            VALUES 
                            ({id},'{name}')"""
        cursor = self.conn.cursor()
        cursor.execute(insert_query)


    def insertTask(self, task:Task):
        insert_query = f"""INSERT INTO task_state
                            (task_id, vehicle_id, solver_id, capacity_needed_to_solve, size_in_megabytes, transfer_rate,
                            status_id, created_at, deadline_at,
                            received_by_task_solver_at, solved_by_task_solver_at, returned_to_creator_at,
                            nft_id, nft_valid_from, nft_valid_to, nft_reserved_cores_each_iteration, ) 
                            VALUES 
                            ({task.id},{task.vehicle.id},{task.solver.id},{task.capacity_needed_to_solve},{task.size_in_megabytes},{task.transfer_rate},
                            {task.status.value},'{task.created_at}','{task.deadline_at}',
                            '{task.received_by_task_solver_at}','{task.solved_by_task_solver_at}','{task.returned_to_creator_at}'
                            ,{task.nft.id},'{task.nft.valid_from}','{task.nft.valid_to}',{task.nft.reserved_cores_each_iteration})"""
        cursor = self.conn.cursor()
        cursor.execute(insert_query)


