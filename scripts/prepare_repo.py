import argparse
import sys
from pathlib import Path
import subprocess
import shutil
from dynapyt.run_instrumentation import instrument_dir
from dynapyt.run_analysis import run_analysis
import os
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def install_special(url):
    if url == "https://github.com/lorien/grab.git":
        command = "pip install cssselect pyquery pymongo fastrq"  # required for running tests
    elif url == "https://github.com/psf/black.git":
        command = "pip install aiohttp"  # required for running tests
    elif url == "https://github.com/errbotio/errbot.git":
        command = "pip install mock"  # required for running tests
    elif url == "https://github.com/PyFilesystem/pyfilesystem2.git":
        command = "pip install parameterized pyftpdlib psutil"  # required for running tests
    elif url == "https://github.com/wtforms/wtforms.git":
        command = "pip install babel email_validator"  # required for running tests
    elif url == "https://github.com/geopy/geopy.git":
        command = "pip install docutils"  # required for running tests
    elif url == "https://github.com/gawel/pyquery.git":
        command = "pip install webtest"  # required for running tests
    elif url == "https://github.com/elastic/elasticsearch-dsl-py.git":
        command = "pip install pytz"  # required for running tests
    elif url == "https://github.com/marshmallow-code/marshmallow.git":
        command = "pip install pytz simplejson"  # required for running tests
    elif url == "https://github.com/pytest-dev/pytest.git":
        command = "pip install hypothesis xmlschema"  # required for running tests
    elif url == "https://github.com/miso-belica/sumy.git":
        subprocess.run(["pip", "install", "nltk"])
        command = "python -m nltk.downloader all"
    elif url == "https://github.com/python-telegram-bot/python-telegram-bot.git":
        command = "pre-commit install"
    elif url == "https://github.com/dpkp/kafka-python.git":
        command = "pip install pytest-mock mock python-snappy zstandard lz4 xxhash crc32c"
    elif url == "https://github.com/sphinx-doc/sphinx.git":
        command = "pip install html5lib"
    elif url == "https://github.com/Trusted-AI/adversarial-robustness-toolbox.git":
        command = "pip install Pillow"
    elif url == "https://github.com/spotify/dh-virtualenv.git":
        command = "pip install mock nose tf_keras"
    else:
        return
    subprocess.run(command.split(" "))


def post_process_special(url):
    if url == "https://github.com/pallets/click.git":
        (Path("click").resolve() / "tests" / "test_imports.py").unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a git repo")
    parser.add_argument("--repo", help="the repo index", type=int)
    parser.add_argument("--config", help="DyLin config file path", type=str)
    args = parser.parse_args()

    here = Path(__file__).parent.resolve()
    with open(here / "projects.txt", "r") as f:
        project_infos = f.read().split("\n")

    project_infos = [p for p in project_infos if not p.startswith("#")]

    project_info = project_infos[args.repo - 1].split(" ")
    if "r" in project_info[2]:
        url, commit, flags, requirements, tests = tuple(project_info)
    else:
        url, commit, flags, tests = tuple(project_info)
        requirements = None
    name = url.split("/")[-1].split(".")[0].replace("-", "_")
    print("Extracted repo info")
    install_special(url)
    print("Installed special requirements")

    if url.startswith("http"):
        subprocess.run(["sh", here / "get_repo.sh", url, commit, name])
        print("Cloned repo and switched to commit")
        if requirements:
            subprocess.run(["pip", "install", "-r", f"{name}/{requirements}"])
        subprocess.run(["pip", "install", "-e", f"{name}/"])
        print("Installed requirements")
    else:
        if requirements:
            print((here/url/requirements).exists())
            subprocess.run(["pip", "install", "-r", f"{str((here/url/requirements).resolve())}"])
        print((here/url).exists())
        subprocess.run(["ls", f"{str(here)}/.."])
        subprocess.run(["pip", "install", "-e", f"{str((here/url).resolve())}/"])

    post_process_special(url)
    print("Post processed special requirements")

    if not url.startswith("http"):
        name = str((here / url).resolve())

    if hasattr(args, "config") and args.config is not None:
        with open(args.config, "r") as f:
            config_content = f.read()
        analyses = config_content.strip().split("\n")
    else:
        analyses = [
            f"dylin.analyses.{a}.{a}"
            for a in [
                "ComparisonBehaviorAnalysis",
                "InPlaceSortAnalysis",
                "InvalidComparisonAnalysis",
                "MutableDefaultArgsAnalysis",
                "StringConcatAnalysis",
                "WrongTypeAddedAnalysis",
                "BuiltinAllAnalysis",
                "ChangeListWhileIterating",
                "StringStripAnalysis",
                "NonFinitesAnalysis",
                # Analyses below require tensorflow, pytorch, scikit-learn dependencies
                "GradientAnalysis",
                "TensorflowNonFinitesAnalysis",
                "InconsistentPreprocessing",
            ]
        ] + [
            f"dylin.analyses.ObjectMarkingAnalysis.ObjectMarkingAnalysis;config={a}"
            for a in [
                "/Work/DyLin/src/dylin/markings/configs/forced_order.yml",
                "/Work/DyLin/src/dylin/markings/configs/leak_preprocessing.yml",
                "/Work/DyLin/src/dylin/markings/configs/leaked_data.yml",
                # "/Work/DyLin/src/dylin/markings/configs/weak_hash.yml",
            ]
        ]

    if name == "rich":
        analyses.remove("dylin.analyses.GradientAnalysis.GradientAnalysis")
        analyses.remove("dylin.analyses.TensorflowNonFinitesAnalysis.TensorflowNonFinitesAnalysis")
    if name == "openleadr_python":
        with open(str(Path(name)/"test"/"test_reports.py")) as f:
            content = f.read()
        content = content.replace("assert(", "assert (")
        with open(str(Path(name)/"test"/"test_reports.py"), "w") as f:
            f.write(content)
    start = time.time()
    instrument_dir(name, analyses, use_external_dir=False)
    inst_time_2 = time.time() - start
    print("Instrumented repo")
    with open("/Work/reports/timing.txt", "w") as f:
        f.write(f"{name} {inst_time_2} ")
