from typing import Any, Callable, Iterator, List, Dict, Optional, Tuple, Union
from ctypes import Array
import importlib
import os
from pathlib import Path
from typing import Any, Callable
from .base_analysis import BaseDyLinAnalysis

"""
Mirrors AnalysisWrapper, utilized as baseline for performance evaluation.
Ignores ignores all calls to specific analyses and does not write results, 
otherwise the same as AnalysisWrapper
"""


class BaselineWrapper(BaseDyLinAnalysis):
    def __init__(self) -> None:
        self.analysis_name = "BaselineWrapper"
        self.analysis_classes: Array[BaseDyLinAnalysis] = []
        self.log_msgs: List[str] = []
        classNames = [
            "FilesClosedAnalysis",
            "ComparisonBehaviorAnalysis",
            "InPlaceSortAnalysis",
            "SideEffectsDunderAnalysis",
            "InvalidComparisonAnalysis",
            "MutableDefaultArgsAnalysis",
            "StringConcatAnalysis",
            "WrongTypeAddedAnalysis",
            "BuiltinAllAnalysis",
            "ChangeListWhileIterating",
            "StringStripAnalysis",
            "NonFinitesAnalysis",
            # Analyses below require tensorflow, pytorch, scikit-learn dependencies
            # "GradientAnalysis",
            # "TensorflowNonFinitesAnalysis",
            # "InconsistentPreprocessing"
        ]
        self.metadata = None
        self.path = Path(os.path.expanduser("~"))
        self.analysis_name = None

        # TODO workaround, make this dynamic later
        self.number_unique_findings_possible = 33

        for name in classNames:
            module = importlib.import_module("dylin." + name)
            cls = getattr(module, name)()
            if cls is not None:
                self.analysis_classes.append(cls)
            else:
                raise ValueError(f"class with name {name} not found")

        import pathlib
        from os import listdir
        from os.path import isfile, join

        pwd = pathlib.Path(__file__).parent.resolve()
        configs_path = pwd / "markings" / "configs"

        files = [f for f in listdir(configs_path) if isfile(join(configs_path, f))]
        for file in files:
            module = importlib.import_module("dylin.ObjectMarkingAnalysis")
            cls: BaseDyLinAnalysis = getattr(module, "ObjectMarkingAnalysis")()
            cls.add_meta({"configName": file})
            cls.setup()
            if cls is not None:
                self.analysis_classes.append(cls)
            else:
                raise ValueError(f"class with name {name} not found")

    def call_if_exists(self, f: str, *args) -> Any:
        # ignore calls to analyses to have performance baseline
        return None

    def end_execution(self) -> None:
        self.call_if_exists("end_execution")

    def runtime_event(self, dyn_ast: str, iid: int) -> None:
        pass

    def read_attribute(self, dyn_ast, iid, base, name, val):
        return self.call_if_exists("read_attribute", dyn_ast, iid, base, name, val)

    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args):
        return self.call_if_exists(
            "pre_call", dyn_ast, iid, function, pos_args, kw_args
        )

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        val: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        return self.call_if_exists(
            "post_call", dyn_ast, iid, val, function, pos_args, kw_args
        )

    def comparison(
        self, dyn_ast: str, iid: int, left: Any, op: str, right: Any, result: Any
    ) -> bool:
        return self.call_if_exists("comparison", dyn_ast, iid, left, op, right, result)

    def add_assign(self, dyn_ast: str, iid: int, left: Any, right: Any) -> Any:
        return self.call_if_exists("add_assign", dyn_ast, iid, left, right)

    def add(
        self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any = None
    ) -> Any:
        return self.call_if_exists("add", dyn_ast, iid, left, right, result)

    def write(self, dyn_ast: str, iid: int, old_val: Any, new_val: Any) -> Any:
        return self.call_if_exists("write", dyn_ast, iid, old_val, new_val)

    def read_identifier(self, dyn_ast: str, iid: int, val: Any) -> Any:
        return self.call_if_exists("read_identifier", dyn_ast, iid, val)

    def function_enter(
        self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool
    ) -> None:
        return self.call_if_exists(
            "function_enter", dyn_ast, iid, args, name, is_lambda
        )

    def function_exit(
        self, dyn_ast: str, iid: int, function_name: str, result: Any
    ) -> Any:
        return self.call_if_exists("function_exit", dyn_ast, iid, function_name, result)

    def _list(self, dyn_ast: str, iid: int, value: List) -> List:
        return self.call_if_exists("_list", dyn_ast, iid, value)

    def binary_operation(
        self, dyn_ast: str, iid: int, op: str, left: Any, right: Any, result: Any
    ) -> Any:
        return self.call_if_exists(
            "binary_operation", dyn_ast, iid, op, left, right, result
        )

    def read_subscript(
        self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any
    ) -> Any:
        return self.call_if_exists("read_subscript", dyn_ast, iid, base, sl, val)

    def enter_for(
        self, dyn_ast: str, iid: int, next_value: Any, iterator: Iterator
    ) -> Optional[Any]:
        return self.call_if_exists("enter_for", dyn_ast, iid, next_value, iterator)

    def exit_for(self, dyn_ast, iid):
        return self.call_if_exists("exit_for", dyn_ast, iid)