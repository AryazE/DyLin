import types
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
from ..markings.obj_identifier import uniqueid, save_uid
import pandas as pd
import numpy as np


class NonFinitesAnalysis(BaseDyLinAnalysis):
    def __init__(self):
        super().__init__()
        self.analysis_name = "NonFinitesAnalysis"
        self.tracked_objects = {}
        self.total_values_investigated = 0

    def can_be_checked_with_numpy(self, value: any) -> bool:
        return isinstance(value, np.ndarray) or isinstance(value, pd.DataFrame)

    def numpy_check_not_finite(self, df: any) -> bool:
        try:
            is_finite = np.isfinite(df)
            self.total_values_investigated = self.total_values_investigated + 1
            try:
                # need to extract values from pandas.Dataframes first
                result = False in is_finite.values
                return result
            except AttributeError as e:
                return False in is_finite
        except TypeError as e:
            return False

    def check_np_issue_found(self, value: any) -> bool:
        if self.can_be_checked_with_numpy(value) and self.numpy_check_not_finite(value):
            return True
        return False

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        args = list(kw_args.values() if not kw_args is None else []) + list(pos_args if not pos_args is None else [])
        no_nan_in_input = True

        for arg in args:
            if self.check_np_issue_found(arg):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-32",
                    f"NaN in numpy or Dataframe object in input {arg}",
                )
                no_nan_in_input = False

        if self.check_np_issue_found(result):
            if no_nan_in_input:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-33",
                    f"NaN in numpy or Dataframe object in result, after applying function {function}",
                )

    def end_execution(self) -> None:
        self.add_meta({"total_values_investigated": self.total_values_investigated})