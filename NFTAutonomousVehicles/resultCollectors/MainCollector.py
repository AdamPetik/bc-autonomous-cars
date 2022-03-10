import os
import sqlite3
import datetime

from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus
from NFTAutonomousVehicles.utils.statistics import IncrementalEvent, Statistics



class MainCollector:

    def __init__(self, dir: str = None, dbfilename: str = None):
        if dir is None:
            cache_dir = os.path.join('results', 'databaseFiles')
        else:
            cache_dir = os.path.join(dir, 'databaseFiles')

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if dbfilename is None:
            filename = str(datetime.datetime.now()).replace(" ","_").replace(":","") +".db"
            filepath = os.path.join(cache_dir, filename)
        else:
            filepath = os.path.join(cache_dir, dbfilename + '.db')

        self.conn = sqlite3.connect(filepath)
        print("SQLITE connection ready" + sqlite3.version)
        self.createTables()

    def closeCollector(self):
        self.conn.close()
        self.conn = None


    def createTables(self):
        SQL_CREATE_TASK_STATE_TABLE = """ CREATE TABLE IF NOT EXISTS task_state (
                                                status_id integer PRIMARY KEY,
                                                name text NOT NULL
                                            ); """

        SQL_CREATE_TASK_TABLE = """ CREATE TABLE IF NOT EXISTS task (
                                                task_id integer PRIMARY KEY,
                                                vehicle_id integer NOT NULL,
                                                vehicle_type integer NOT NULL,
                                                solver_id integer,
                                                instruction_count integer NOT NULL,
                                                size_in_megabytes integer NOT NULL,
                                                single_transfer_time real,
                                                status_id integer NOT NULL,
                                                created_at TEXT NOT NULL,
                                                deadline_at TEXT NOT NULL,
                                                deadline_interval real NOT NULL,
                                                total_time_spent real,
                                                received_by_task_solver_at TEXT,
                                                solved_by_task_solver_at TEXT,
                                                returned_to_creator_at TEXT,
                                                nft_id integer,
                                                nft_signed integer,
                                                nft_valid_from TEXT,
                                                nft_valid_to TEXT,
                                                nft_reserved_ips int,
                                                nft_reserved_rbs int,
                                                FOREIGN KEY (status_id) REFERENCES task_state (status_id)
                                            ); """

        SQL_CREATE_ROUTE_TABLE = """ CREATE TABLE IF NOT EXISTS route (
                                                vehicle_id integer NOT NULL,
                                                planning_at TEXT NOT NULL,
                                                number_of_routes_considered integer,
                                                shortest_route_index integer,
                                                shortest_route_missing_nfts integer,
                                                shortest_route_step_count integer,
                                                shortest_route_length_in_meters real,
                                                shortest_route_segments_without_solvers integer,
                                                shortest_route_metrics real,
                                                best_route_index integer,
                                                best_route_missing_nfts integer,
                                                best_route_step_count integer,
                                                best_route_length_in_meters real,
                                                best_route_segments_without_solvers integer,
                                                best_route_metrics real
                                            ); """

        cursor = self.conn.cursor()
        cursor.execute(SQL_CREATE_TASK_STATE_TABLE)
        cursor.execute(SQL_CREATE_TASK_TABLE)
        cursor.execute(SQL_CREATE_ROUTE_TABLE)

        self.insertTaskStatus(1, "SUBMITTED")
        self.insertTaskStatus(2, "BEING_PROCESSED")
        self.insertTaskStatus(3, "SOLVED")
        self.insertTaskStatus(4, "PROCESSING_FAILED")
        self.insertTaskStatus(5, "TASK_TIMED_OUT")
        self.insertTaskStatus(6, "FAILED_TO_FIND_SOLVER")
        self.conn.commit()

    def insertTaskStatus(self, id, name):
        insert_query = f"""INSERT INTO task_state
                            (status_id, name) 
                            VALUES 
                            ({id},'{name}')"""
        cursor = self.conn.cursor()
        cursor.execute(insert_query)
        self.conn.commit()

    def logTask(self, task):
        if task.status != TaskStatus.SOLVED:
            Statistics().incremental_event(IncrementalEvent.DISCARDED_TASK)
        if task.solver is None:
            solver_id = "null"
        else:
            solver_id = task.solver.id

        if task.nft is None:
            total_spent = task.getTotalTimeSpent() if task.getTotalTimeSpent() == 'null' else task.getTotalTimeSpent().total_seconds()
            task.single_transfer_time = task.single_transfer_time if task.single_transfer_time is not None else 'null'
            insert_query = f"""INSERT INTO task
                                (task_id, vehicle_id, vehicle_type, solver_id, instruction_count, size_in_megabytes, single_transfer_time,
                                status_id, created_at, deadline_at, deadline_interval, total_time_spent,
                                received_by_task_solver_at, solved_by_task_solver_at, returned_to_creator_at,
                                nft_id, nft_signed, nft_valid_from, nft_valid_to, nft_reserved_ips, nft_reserved_rbs) 
                                VALUES 
                                ({task.id},{task.vehicle.id},{task.vehicle.vehicle_type},{solver_id},{task.instruction_count},{task.size_in_megabytes},{task.single_transfer_time},
                                {task.status.value},'{task.created_at}','{task.deadline_at}','{task.getDeadlineInterval()}', {total_spent},
                                '{task.received_by_task_solver_at}','{task.solved_by_task_solver_at}','{task.returned_to_creator_at}'
                                ,null, null, null, null, null, null)"""

        else:
            total_spent = task.getTotalTimeSpent() if task.getTotalTimeSpent() =='null' else task.getTotalTimeSpent().total_seconds()
            insert_query = f"""INSERT INTO task
                                (task_id, vehicle_id, vehicle_type, solver_id, instruction_count, size_in_megabytes, single_transfer_time,
                                status_id, created_at, deadline_at, deadline_interval, total_time_spent,
                                received_by_task_solver_at, solved_by_task_solver_at, returned_to_creator_at,
                                nft_id, nft_signed, nft_valid_from, nft_valid_to, nft_reserved_ips, nft_reserved_rbs) 
                                VALUES 
                                ({task.id},{task.vehicle.id},{task.vehicle.vehicle_type},{solver_id},{task.instruction_count},{task.size_in_megabytes},{task.single_transfer_time},
                                {task.status.value},'{task.created_at}','{task.deadline_at}','{task.getDeadlineInterval()}', {total_spent},
                                '{task.received_by_task_solver_at}','{task.solved_by_task_solver_at}','{task.returned_to_creator_at}'
                                ,{task.nft.id},{task.nft.signed},'{task.nft.valid_from}','{task.nft.valid_to}',{task.nft.reserved_ips},{task.nft.reserved_rbs})"""

        cursor = self.conn.cursor()
        # print(f"Insert: {insert_query}")
        cursor.execute(insert_query)
        self.conn.commit()




    def logProposedRoute(self, vehicle, planing_at, number_of_routes_considered, shortest_route, best_route):
        insert_query = f"""INSERT INTO route
                            ( vehicle_id, planning_at, number_of_routes_considered,
                            shortest_route_index, shortest_route_missing_nfts, shortest_route_step_count, shortest_route_length_in_meters,
                            shortest_route_segments_without_solvers, shortest_route_metrics,
                            best_route_index, best_route_missing_nfts, best_route_step_count, best_route_length_in_meters,
                            best_route_segments_without_solvers, best_route_metrics) 
                            VALUES 
                            (
                            {vehicle.id},'{planing_at}', {number_of_routes_considered},
                            {shortest_route.index}, {shortest_route.missing_NFTs}, {shortest_route.route_step_count}, {shortest_route.route_length_in_meters},
                            {len(shortest_route.segments_without_solvers)},{shortest_route.getMetrics()[0]},
                            {best_route.index}, {best_route.missing_NFTs}, {best_route.route_step_count}, {best_route.route_length_in_meters},
                            {len(best_route.segments_without_solvers)},{best_route.getMetrics()[0]}
                            )"""
        cursor = self.conn.cursor()
        cursor.execute(insert_query)
        self.conn.commit()

# collector = MainCollector()
#
# print("BLABALABLA")
#
# # datum = datetime.datetime.now()
# # nft = NFT(12, 2533, datum, datum, 10)
# #
# #
# # task = Task(1212, 25332533, 2536.25, 55, 15, datum, datum)
# # task.nft = nft
# # task.status=TaskStatus.PROCESSING_FAILED
# # task.received_by_task_solver_at = datum
# # task.solved_by_task_solver_at = datum
# # task.returned_to_creator_at = datum
# # task.name = "Testovaci Task"
# #
# # collector.insertTask(task)
# #
# #