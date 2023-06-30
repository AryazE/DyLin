from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
import builtins


class BuiltinAllAnalysis(BaseDyLinAnalysis):
    def __init__(self):
        super(BuiltinAllAnalysis, self).__init__()
        self.analysis_name = "BuiltinAllAnalysis"

    def _flatten(self, l):
        new_list = []
        for i in l:
            if isinstance(i, list):
                new_list = new_list + self._flatten(i)
            else:
                new_list.append(i)
        return new_list

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        val: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        if function == builtins.all or function == builtins.any:
            arg = pos_args[0]
            if isinstance(arg, list):
                flattened = self._flatten(arg)
                if len(flattened) == 0 and val == True:
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-21",
                        f"Potentially unintended result for any() call, result: {val} arg: {arg}",
                    )