import logging
from typing import Any, Dict, Optional
import sys
import json
import csv
import uuid
from pathlib import Path
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import Location
import traceback
from filelock import FileLock


class BaseDyLinAnalysis(BaseAnalysis):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.unique_id = str(uuid.uuid4())
        self.findings = {}
        self.number_findings = 0
        self.meta = {}
        self.stack_levels = 20
        self.path = Path(self.output_dir)
        if not self.path.exists():
            self.path.mkdir(parents=True)
        logging.basicConfig(stream=sys.stderr)
        self.log = logging.getLogger("TestsuiteWrapper")
        self.log.setLevel(logging.DEBUG)
        self.number_unique_findings_possible = 33
        print(f"$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Loaded analysis {self.analysis_name if hasattr(self, 'analysis_name') else 'no name'} writing to {self.output_dir}")

    def setup(self):
        # Hook for subclasses
        pass

    def add_finding(
        self,
        iid: int,
        filename: str,
        name: Optional[str] = "placeholder name",
        msg: Optional[str] = None,
    ) -> None:
        print(f"########################### Found something")
        self.number_findings += 1
        stacktrace = "".join(traceback.format_stack()[-self.stack_levels :])
        location = self.iid_to_location(filename, iid)
        if name not in self.findings:
            self.findings[name] = [self._create_error_msg(iid, location, stacktrace, msg)]
        else:
            self.findings[name].append(self._create_error_msg(iid, location, stacktrace, msg))

    def get_result(self) -> Any:
        findings = self._format_issues(self.findings)
        if len(findings) == 0:
            return None
        return {
            self.analysis_name: {
                "nmb_findings": self.number_findings,
                "is_sane": self.is_sane(),
                "meta": self.meta,
                "results": findings,
            }
        }

    """
    sanity check to make sure all findings are added properly
    """

    def is_sane(self) -> bool:
        res = 0
        for name, value in self.findings.items():
            res += len(value)
        return self.number_findings == res

    def add_meta(self, meta: any):
        self.meta = meta

    def _create_error_msg(
        self,
        iid: int,
        location: Location,
        stacktrace: Optional[str] = None,
        msg: Optional[str] = None,
    ) -> Any:
        return {
            "msg": msg,
            "trace": stacktrace,
            "location": location._asdict(),
            "uid": str(location),
            "iid": iid,
        }

    def _format_issues(self, findings: Dict) -> Dict:
        res = {}
        for name in findings:
            found_iids = {}
            for finding in findings[name]:
                if not finding["uid"] in found_iids:
                    found_iids[finding["iid"]] = {"finding": finding, "n": 1}
                else:
                    found_iids[finding["iid"]]["n"] += 1
            res[name] = list(found_iids.values())
        return res

    def get_unique_findings(self):
        return self._format_issues(self.findings)

    def _write_detailed_results(self):
        print(f"$$$$$$$$$$$$$$$$$$$$$ Writing results of {self.analysis_name if hasattr(self, 'analysis_name') else 'noe name'}")
        temp_res = self.get_result()
        if temp_res is not None:
            result = {"meta": self.meta, "results": temp_res}
            filename = f"output-{str(self.analysis_name)}-{self.unique_id}-report.json"
            while (self.path / filename).exists():
                self.unique_id = str(uuid.uuid4())
                filename = f"output-{str(self.analysis_name)}-{self.unique_id}-report.json"
                # print(f"$$$$$$$$$$$$$$$$$$$$ File {filename} exists. Reading ...", file=sys.stderr)
                # with open(self.path / filename, "r") as f:
                #     rep = json.load(f)
                # for k, v in rep.items():
                #     if k == "meta" and "total_comp" in result["meta"] and "total_comp" in v:
                #         result["meta"]["total_comp"] += v["total_comp"]
                #     elif k == "results":
                #         result["results"].extend(v)
            print(f"$$$$$$$$$$$$$$$$$$$$ Writing to file {filename} ...", file=sys.stderr)
            with open(self.path / filename, "w") as report:
                report.write(json.dumps(result, indent=4))

    def _write_overview(self):
        # prevent reporting findings multiple times to the same iid
        results = self.get_unique_findings()
        row_findings = 0
        for f_name in results:
            row_findings += len(results[f_name])
        csv_row = [self.analysis_name, row_findings]
        with FileLock(str(self.path / "findings.csv") + ".lock"):
            csv_rows = []
            if (self.path / "findings.csv").exists():
                with open(self.path / "findings.csv", "r") as f:
                    reader = csv.reader(f)
                    existed = False
                    for row in reader:
                        if self.analysis_name == row[0]:
                            csv_row = [self.analysis_name, row_findings + int(row[1])]
                            existed = True
                            csv_rows.append(csv_row)
                        else:
                            csv_rows.append(row)
                    if not existed:
                        csv_rows.append(csv_row)
            else:
                csv_rows = [csv_row]
            with open(self.path / "findings.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerows(csv_rows)

    def end_execution(self) -> None:
        self._write_detailed_results()
        self._write_overview()
