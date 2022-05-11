from abc import ABC, abstractmethod

from core.views import View


class Controller(ABC):
    @abstractmethod
    def bind(self, v: View):
        raise NotImplementedError
