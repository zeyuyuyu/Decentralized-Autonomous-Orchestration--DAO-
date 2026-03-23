import random
import time

class DecentralizedTaskOrchestrator:
    def __init__(self, num_nodes):
        self.num_nodes = num_nodes
        self.node_states = [{'available': True, 'tasks': []} for _ in range(num_nodes)]
        self.task_queue = []

    def submit_task(self, task):
        self.task_queue.append(task)
        self.allocate_tasks()

    def allocate_tasks(self):
        while self.task_queue:
            task = self.task_queue.pop(0)
            available_nodes = [node for node in self.node_states if node['available']]
            if available_nodes:
                chosen_node = random.choice(available_nodes)
                chosen_node['tasks'].append(task)
                chosen_node['available'] = False
                print(f'Allocated task {task} to node {self.node_states.index(chosen_node)}')
            else:
                self.task_queue.append(task)
                break

    def run_tasks(self):
        while True:
            for node in self.node_states:
                if node['tasks']:
                    task = node['tasks'].pop(0)
                    print(f'Running task {task} on node {self.node_states.index(node)}')
                    time.sleep(2)  # Simulating task execution
                    node['available'] = True
            self.allocate_tasks()
            time.sleep(1)

if __name__ == '__main__':
    orchestrator = DecentralizedTaskOrchestrator(num_nodes=5)
    orchestrator.submit_task('task1')
    orchestrator.submit_task('task2')
    orchestrator.submit_task('task3')
    orchestrator.run_tasks()