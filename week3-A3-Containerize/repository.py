from abc import ABC, abstractmethod


class TaskRepository(ABC):
    @abstractmethod
    def list_tasks(self):
        ...

    @abstractmethod
    def get_task(self, task_id):
        ...

    @abstractmethod
    def create_task(self, title, done=False):
        ...

    @abstractmethod
    def update_task(self, task_id, title, done):
        ...

    @abstractmethod
    def delete_task(self, task_id):
        ...
